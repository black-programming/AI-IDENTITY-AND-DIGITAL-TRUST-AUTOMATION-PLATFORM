"""AI-Agent Identity Registry Service.

Manages AI agent registration, versioned manifests, cryptographic public key fingerprints,
status lifecycles (ACTIVE, SUSPENDED, REVOKED, EXPIRED), and tamper-evident audit logging.
"""

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.errors import ConflictException, NotFoundException, PermissionDeniedException, ValidationException
from app.core.security import (
    AuthenticatedUser,
    ROLE_AUDITOR,
    ROLE_ORG_ADMIN,
    ROLE_ORG_MEMBER,
    ROLE_SYS_ADMIN,
    ROLE_VERIFIER,
)
from app.schemas.agents import (
    AgentCreateRequest,
    AgentListResponse,
    AgentManifestPayload,
    AgentManifestResponse,
    AgentManifestUpdateRequest,
    AgentResponse,
    AgentRevokeRequest,
    AgentRotateKeyRequest,
)
from app.services.audit_service import AuditService
from app.services.organization_service import _MOCK_MEMBERSHIPS_DB


def compute_key_fingerprint(pem_str: str) -> str:
    """Compute canonical SHA-256 fingerprint for a public key PEM string."""
    clean_bytes = pem_str.strip().encode("utf-8")
    digest = hashlib.sha256(clean_bytes).hexdigest().upper()
    return f"SHA256:{digest}"


# In-Memory Database for Agents
_MOCK_AGENTS_DB: Dict[str, Dict[str, Any]] = {
    "agent-ocr-extractor-01": {
        "id": "agent-ocr-extractor-01",
        "agent_slug": "ocr-vision-pipeline-v1",
        "name": "OCR Vision Extraction Agent",
        "description": "Autonomous vision pipeline for extracting and parsing synthetic identity documents",
        "owner_id": "user-org-admin-1",
        "organization_id": "org-acme-111",
        "status": "ACTIVE",
        "current_manifest_version": 1,
        "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAGb9f4n5e8z1k0v2m4q6w8e0r2t4y6u8i0o2p4a6s8d0=\n-----END PUBLIC KEY-----",
        "public_key_fingerprint": "SHA256:4C8F5B2E1D9A7C3B0E8F6A4C2E0B8D6F4A2C0E8B6D4F2A0C8E6B4D2F0A8C6E4B",
        "key_algorithm": "ED25519",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=365),
        "revoked_at": None,
        "revoked_by": None,
        "revocation_reason": None,
        "created_at": datetime.now(timezone.utc) - timedelta(days=10),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=10),
    },
    "agent-policy-evaluator-02": {
        "id": "agent-policy-evaluator-02",
        "agent_slug": "trust-policy-evaluator-v1",
        "name": "Deterministic Trust Policy Evaluator",
        "description": "Rule-based engine evaluation agent for KYC trust tier determinations",
        "owner_id": "a0000000-0000-0000-0000-000000000001",
        "organization_id": None,
        "status": "ACTIVE",
        "current_manifest_version": 1,
        "public_key_pem": None,
        "public_key_fingerprint": None,
        "key_algorithm": "ED25519",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=180),
        "revoked_at": None,
        "revoked_by": None,
        "revocation_reason": None,
        "created_at": datetime.now(timezone.utc) - timedelta(days=5),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=5),
    },
}

# In-Memory Database for Versioned Manifests
_MOCK_MANIFESTS_DB: Dict[str, List[Dict[str, Any]]] = {
    "agent-ocr-extractor-01": [
        {
            "manifest_version": 1,
            "capabilities": ["extract:ocr", "read:evidence"],
            "model_provider": "google",
            "model_id": "gemini-1.5-pro",
            "runtime_environment": "CONTAINER",
            "system_prompt_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "code_hash": "sha256:ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "published_by": "user-org-admin-1",
            "change_summary": "Initial baseline manifest for OCR vision extraction agent",
            "created_at": datetime.now(timezone.utc) - timedelta(days=10),
        }
    ],
    "agent-policy-evaluator-02": [
        {
            "manifest_version": 1,
            "capabilities": ["evaluate:policy", "audit:read"],
            "model_provider": "self-hosted",
            "model_id": "rule-policy-engine-v1",
            "runtime_environment": "SERVERLESS",
            "system_prompt_hash": None,
            "code_hash": "sha256:3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
            "published_by": "a0000000-0000-0000-0000-000000000001",
            "change_summary": "Initial baseline deterministic policy evaluation manifest",
            "created_at": datetime.now(timezone.utc) - timedelta(days=5),
        }
    ],
}


class AgentRegistryService:
    """Core domain logic for AI-Agent Identity Registry."""

    @classmethod
    def _user_can_access_agent(cls, user: AuthenticatedUser, agent: Dict[str, Any]) -> bool:
        """Enforce visibility: Owner, Org Member, or Platform Inspector (Verifier, Auditor, Sys Admin)."""
        if user.role in (ROLE_SYS_ADMIN, ROLE_AUDITOR, ROLE_VERIFIER):
            return True
        if agent["owner_id"] == user.user_id:
            return True
        org_id = agent.get("organization_id")
        if org_id:
            if user.has_org_access(org_id):
                return True
            org_members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
            if any(m["user_id"] == user.user_id for m in org_members):
                return True
        return False

    @classmethod
    def _user_can_manage_agent(cls, user: AuthenticatedUser, agent: Dict[str, Any]) -> bool:
        """Enforce management authority: strictly Agent Owner or Platform System Admin."""
        if user.role == ROLE_SYS_ADMIN:
            return True
        return agent["owner_id"] == user.user_id

    @classmethod
    def _build_response(cls, agent: Dict[str, Any]) -> AgentResponse:
        """Construct full AgentResponse including current manifest and active dynamic status."""
        now = datetime.now(timezone.utc)
        status = agent["status"]

        # Dynamic check for expiry if currently ACTIVE
        if status == "ACTIVE" and agent["expires_at"] < now:
            status = "EXPIRED"

        manifests = _MOCK_MANIFESTS_DB.get(agent["id"], [])
        current_version = agent["current_manifest_version"]
        current_manifest_dict = next((m for m in manifests if m["manifest_version"] == current_version), None)
        if not current_manifest_dict:
            # Fallback to last manifest if available
            current_manifest_dict = manifests[-1] if manifests else {
                "manifest_version": 1,
                "capabilities": ["task:execute"],
                "model_provider": "unknown",
                "model_id": "unknown",
                "runtime_environment": "CONTAINER",
                "published_by": agent["owner_id"],
                "created_at": agent["created_at"],
            }

        manifest_resp = AgentManifestResponse(**current_manifest_dict)

        return AgentResponse(
            id=agent["id"],
            agent_slug=agent["agent_slug"],
            name=agent["name"],
            description=agent.get("description"),
            owner_id=agent["owner_id"],
            organization_id=agent.get("organization_id"),
            status=status,
            current_manifest_version=current_version,
            current_manifest=manifest_resp,
            public_key_fingerprint=agent.get("public_key_fingerprint"),
            key_algorithm=agent.get("key_algorithm"),
            expires_at=agent["expires_at"],
            revoked_at=agent.get("revoked_at"),
            revoked_by=agent.get("revoked_by"),
            revocation_reason=agent.get("revocation_reason"),
            created_at=agent["created_at"],
            updated_at=agent["updated_at"],
            is_active=(status == "ACTIVE"),
        )

    @classmethod
    def register_agent(cls, request: AgentCreateRequest, caller: AuthenticatedUser) -> AgentResponse:
        """Register a new AI Agent identity with initial manifest and cryptographic fingerprint."""
        # 1. Slug uniqueness
        for existing in _MOCK_AGENTS_DB.values():
            if existing["agent_slug"].lower() == request.agent_slug.lower():
                raise ConflictException(f"Agent with slug '{request.agent_slug}' already exists")

        # 2. Org boundary check if organization_id specified
        if request.organization_id:
            org_id = request.organization_id
            has_org = caller.has_org_access(org_id)
            if not has_org:
                org_members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
                if not any(m["user_id"] == caller.user_id for m in org_members):
                    raise PermissionDeniedException(f"Access to organization '{org_id}' denied")

        # 3. Cryptographic Key Fingerprint
        key_fingerprint = None
        if request.public_key_pem:
            key_fingerprint = compute_key_fingerprint(request.public_key_pem)

        now = datetime.now(timezone.utc)
        agent_id = f"agent-{uuid.uuid4()}"
        expires_at = now + timedelta(days=request.validity_days or 365)

        # 4. Manifest v1
        initial_manifest = {
            "manifest_version": 1,
            "capabilities": request.manifest.capabilities,
            "model_provider": request.manifest.model_provider,
            "model_id": request.manifest.model_id,
            "runtime_environment": request.manifest.runtime_environment or "CONTAINER",
            "system_prompt_hash": request.manifest.system_prompt_hash,
            "code_hash": request.manifest.code_hash,
            "published_by": caller.user_id,
            "change_summary": request.manifest.change_summary or "Initial agent registration",
            "created_at": now,
        }

        # 5. Agent Record
        agent_dict = {
            "id": agent_id,
            "agent_slug": request.agent_slug,
            "name": request.name,
            "description": request.description,
            "owner_id": caller.user_id,
            "organization_id": request.organization_id,
            "status": "ACTIVE",
            "current_manifest_version": 1,
            "public_key_pem": request.public_key_pem,
            "public_key_fingerprint": key_fingerprint,
            "key_algorithm": request.key_algorithm or "ED25519",
            "expires_at": expires_at,
            "revoked_at": None,
            "revoked_by": None,
            "revocation_reason": None,
            "created_at": now,
            "updated_at": now,
        }

        _MOCK_AGENTS_DB[agent_id] = agent_dict
        _MOCK_MANIFESTS_DB[agent_id] = [initial_manifest]

        # 6. Audit Trail Logging
        AuditService.record_event(
            action_type="AGENT_REGISTERED",
            target_resource=f"agent/{agent_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={
                "agent_id": agent_id,
                "agent_slug": request.agent_slug,
                "name": request.name,
                "capabilities": request.manifest.capabilities,
                "public_key_fingerprint": key_fingerprint,
                "expires_at": expires_at.isoformat(),
            },
        )

        return cls._build_response(agent_dict)

    @classmethod
    def get_agent(cls, agent_id: str, caller: AuthenticatedUser) -> AgentResponse:
        """Inspect agent profile, manifest, and lifecycle state."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_access_agent(caller, agent):
            raise PermissionDeniedException(f"Access to agent '{agent_id}' denied")

        return cls._build_response(agent)

    @classmethod
    def list_agents(
        cls,
        caller: AuthenticatedUser,
        status_filter: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> List[AgentResponse]:
        """List agents visible to caller, filtered optionally by status or organization."""
        results: List[AgentResponse] = []
        for agent in _MOCK_AGENTS_DB.values():
            if not cls._user_can_access_agent(caller, agent):
                continue
            if org_id and agent.get("organization_id") != org_id:
                continue
            resp = cls._build_response(agent)
            if status_filter and resp.status.upper() != status_filter.upper():
                continue
            results.append(resp)
        return sorted(results, key=lambda a: a.name)

    @classmethod
    def update_manifest(
        cls,
        agent_id: str,
        request: AgentManifestUpdateRequest,
        caller: AuthenticatedUser,
    ) -> AgentResponse:
        """Publish a new versioned manifest for an active agent."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_manage_agent(caller, agent):
            raise PermissionDeniedException("Only the agent owner or system administrator can update its manifest")

        if agent["status"] == "REVOKED":
            raise ValidationException("Cannot update manifest: agent has been revoked")
        if agent["status"] == "EXPIRED":
            raise ValidationException("Cannot update manifest: agent identity has expired")

        new_version = agent["current_manifest_version"] + 1
        now = datetime.now(timezone.utc)

        new_manifest = {
            "manifest_version": new_version,
            "capabilities": request.capabilities,
            "model_provider": request.model_provider,
            "model_id": request.model_id,
            "runtime_environment": request.runtime_environment or "CONTAINER",
            "system_prompt_hash": request.system_prompt_hash,
            "code_hash": request.code_hash,
            "published_by": caller.user_id,
            "change_summary": request.change_summary,
            "created_at": now,
        }

        _MOCK_MANIFESTS_DB.setdefault(agent_id, []).append(new_manifest)
        agent["current_manifest_version"] = new_version
        agent["updated_at"] = now

        AuditService.record_event(
            action_type="AGENT_MANIFEST_UPDATED",
            target_resource=f"agent/{agent_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={
                "agent_id": agent_id,
                "manifest_version": new_version,
                "capabilities": request.capabilities,
                "change_summary": request.change_summary,
            },
        )

        return cls._build_response(agent)

    @classmethod
    def rotate_key(
        cls,
        agent_id: str,
        request: AgentRotateKeyRequest,
        caller: AuthenticatedUser,
    ) -> AgentResponse:
        """Rotate the cryptographic public key and fingerprint for an active agent."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_manage_agent(caller, agent):
            raise PermissionDeniedException("Only the agent owner or system administrator can rotate credentials")

        if agent["status"] == "REVOKED":
            raise ValidationException("Cannot rotate key: agent has been revoked")

        new_fingerprint = compute_key_fingerprint(request.public_key_pem)
        now = datetime.now(timezone.utc)

        agent["public_key_pem"] = request.public_key_pem
        agent["public_key_fingerprint"] = new_fingerprint
        agent["key_algorithm"] = request.key_algorithm or agent.get("key_algorithm", "ED25519")
        agent["updated_at"] = now

        AuditService.record_event(
            action_type="AGENT_KEY_ROTATED",
            target_resource=f"agent/{agent_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={
                "agent_id": agent_id,
                "new_fingerprint": new_fingerprint,
                "key_algorithm": agent["key_algorithm"],
            },
        )

        return cls._build_response(agent)

    @classmethod
    def revoke_agent(
        cls,
        agent_id: str,
        reason: str,
        caller: AuthenticatedUser,
    ) -> AgentResponse:
        """Permanently revoke an agent identity."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_manage_agent(caller, agent):
            raise PermissionDeniedException("Only the agent owner or system administrator can revoke this agent")

        if agent["status"] == "REVOKED":
            raise ConflictException(f"Agent '{agent_id}' is already revoked")

        now = datetime.now(timezone.utc)
        agent["status"] = "REVOKED"
        agent["revoked_at"] = now
        agent["revoked_by"] = caller.user_id
        agent["revocation_reason"] = reason
        agent["updated_at"] = now

        AuditService.record_event(
            action_type="AGENT_REVOKED",
            target_resource=f"agent/{agent_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={
                "agent_id": agent_id,
                "revoked_by": caller.user_id,
                "reason": reason,
            },
        )

        return cls._build_response(agent)

    @classmethod
    def suspend_agent(cls, agent_id: str, caller: AuthenticatedUser) -> AgentResponse:
        """Temporarily suspend an active agent identity."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_manage_agent(caller, agent):
            raise PermissionDeniedException("Only the agent owner or system administrator can suspend this agent")

        if agent["status"] == "REVOKED":
            raise ValidationException("Cannot suspend a revoked agent")

        now = datetime.now(timezone.utc)
        agent["status"] = "SUSPENDED"
        agent["updated_at"] = now

        AuditService.record_event(
            action_type="AGENT_SUSPENDED",
            target_resource=f"agent/{agent_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={"agent_id": agent_id},
        )

        return cls._build_response(agent)

    @classmethod
    def activate_agent(cls, agent_id: str, caller: AuthenticatedUser) -> AgentResponse:
        """Re-activate a suspended agent identity (revoked agents cannot be re-activated)."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_manage_agent(caller, agent):
            raise PermissionDeniedException("Only the agent owner or system administrator can activate this agent")

        if agent["status"] == "REVOKED":
            raise ValidationException("Cannot activate a revoked agent. Revocation is permanent.")

        now = datetime.now(timezone.utc)
        agent["status"] = "ACTIVE"
        agent["updated_at"] = now

        AuditService.record_event(
            action_type="AGENT_ACTIVATED",
            target_resource=f"agent/{agent_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={"agent_id": agent_id},
        )

        return cls._build_response(agent)

    @classmethod
    def list_manifests(cls, agent_id: str, caller: AuthenticatedUser) -> List[AgentManifestResponse]:
        """List versioned manifests history for an agent."""
        agent = _MOCK_AGENTS_DB.get(agent_id)
        if not agent:
            raise NotFoundException(f"Agent '{agent_id}' not found")

        if not cls._user_can_access_agent(caller, agent):
            raise PermissionDeniedException(f"Access to agent '{agent_id}' denied")

        manifests = _MOCK_MANIFESTS_DB.get(agent_id, [])
        return [AgentManifestResponse(**m) for m in sorted(manifests, key=lambda m: m["manifest_version"])]
