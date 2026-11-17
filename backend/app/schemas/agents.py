"""Schemas for AI-Agent Identity Registry and Versioned Manifests."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


VALID_AGENT_CAPABILITIES = {
    "read:evidence",
    "write:evidence",
    "extract:ocr",
    "validate:rules",
    "evaluate:policy",
    "review:assist",
    "audit:read",
    "claim:submit",
    "task:execute",
}

VALID_KEY_ALGORITHMS = {"ED25519", "RSA-2048", "RSA-4096", "ECDSA-P256"}


class AgentManifestPayload(BaseModel):
    """Payload representing an agent manifest specification."""
    capabilities: List[str] = Field(..., description="Granted technical capabilities for this agent")
    model_provider: str = Field(..., description="Provider name, e.g. google, openai, anthropic, self-hosted")
    model_id: str = Field(..., description="Model identifier, e.g. gemini-1.5-pro, claude-3-5-sonnet")
    runtime_environment: Optional[str] = Field("CONTAINER", description="Runtime context: CONTAINER, SERVERLESS, LOCAL")
    system_prompt_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of system prompt instructions")
    code_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of agent source/binary package")
    change_summary: Optional[str] = Field(None, description="Description of changes in this version")

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, caps: List[str]) -> List[str]:
        if not caps:
            raise ValueError("Agent must declare at least one capability")
        for cap in caps:
            if cap not in VALID_AGENT_CAPABILITIES and not cap.startswith("custom:"):
                raise ValueError(f"Unsupported capability '{cap}'. Allowed: {sorted(VALID_AGENT_CAPABILITIES)} or 'custom:*'")
        return caps


class AgentManifestResponse(BaseModel):
    """Response model for a versioned agent manifest."""
    manifest_version: int
    capabilities: List[str]
    model_provider: str
    model_id: str
    runtime_environment: str = "CONTAINER"
    system_prompt_hash: Optional[str] = None
    code_hash: Optional[str] = None
    published_by: str
    change_summary: Optional[str] = None
    created_at: datetime


class AgentCreateRequest(BaseModel):
    """Request payload to register a new AI Agent identity."""
    name: str = Field(..., min_length=2, max_length=100, description="Display name for the AI agent")
    agent_slug: str = Field(..., min_length=2, max_length=60, description="Unique URI/identifier slug for the agent")
    description: Optional[str] = Field(None, max_length=500)
    organization_id: Optional[str] = Field(None, description="Optional organization to which this agent is assigned")
    manifest: AgentManifestPayload
    public_key_pem: Optional[str] = Field(None, description="Cryptographic public key in PEM format")
    public_key: Optional[str] = Field(None, description="Convenience alias for public_key_pem")
    operator_id: Optional[str] = Field(None, description="Optional operator user ID")
    key_algorithm: Optional[str] = Field("ED25519", description="Cryptographic algorithm: ED25519, RSA-2048, RSA-4096, ECDSA-P256")
    validity_days: Optional[int] = Field(365, ge=1, le=1095, description="Initial validity period in days")

    @field_validator("key_algorithm")
    @classmethod
    def validate_algorithm(cls, alg: Optional[str]) -> Optional[str]:
        if alg and alg not in VALID_KEY_ALGORITHMS:
            raise ValueError(f"Invalid key algorithm '{alg}'. Supported: {sorted(VALID_KEY_ALGORITHMS)}")
        return alg


class AgentManifestUpdateRequest(BaseModel):
    """Request payload to publish a new manifest version for an active agent."""
    capabilities: List[str]
    model_provider: str
    model_id: str
    runtime_environment: Optional[str] = "CONTAINER"
    system_prompt_hash: Optional[str] = None
    code_hash: Optional[str] = None
    change_summary: str = Field(..., min_length=5, description="Audit reason / summary of manifest modifications")

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, caps: List[str]) -> List[str]:
        if not caps:
            raise ValueError("Agent must declare at least one capability")
        for cap in caps:
            if cap not in VALID_AGENT_CAPABILITIES and not cap.startswith("custom:"):
                raise ValueError(f"Unsupported capability '{cap}'. Allowed: {sorted(VALID_AGENT_CAPABILITIES)} or 'custom:*'")
        return caps


class AgentRotateKeyRequest(BaseModel):
    """Request payload to rotate an agent's cryptographic key."""
    public_key_pem: str = Field(..., min_length=20, description="New public key in PEM format")
    key_algorithm: Optional[str] = Field("ED25519", description="Cryptographic algorithm")

    @field_validator("key_algorithm")
    @classmethod
    def validate_algorithm(cls, alg: Optional[str]) -> Optional[str]:
        if alg and alg not in VALID_KEY_ALGORITHMS:
            raise ValueError(f"Invalid key algorithm '{alg}'. Supported: {sorted(VALID_KEY_ALGORITHMS)}")
        return alg


class AgentRevokeRequest(BaseModel):
    """Payload to revoke an AI agent identity immediately."""
    reason: str = Field(..., min_length=5, max_length=500, description="Formal revocation reason for audit trail")


class AgentResponse(BaseModel):
    """Complete response model for an AI Agent identity."""
    id: str
    agent_slug: str
    name: str
    description: Optional[str] = None
    owner_id: str
    organization_id: Optional[str] = None
    status: str = Field(..., description="ACTIVE, SUSPENDED, REVOKED, EXPIRED")
    current_manifest_version: int
    current_manifest: AgentManifestResponse
    public_key_fingerprint: Optional[str] = None
    key_algorithm: Optional[str] = None
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool


class AgentListResponse(BaseModel):
    """List response for AI Agent identities."""
    agents: List[AgentResponse]
    total: int
