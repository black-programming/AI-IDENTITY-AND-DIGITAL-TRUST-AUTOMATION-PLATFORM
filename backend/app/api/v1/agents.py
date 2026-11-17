"""API Endpoints for AI-Agent Identity Registry and Versioned Manifests."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.agents import (
    AgentCreateRequest,
    AgentManifestResponse,
    AgentManifestUpdateRequest,
    AgentResponse,
    AgentRevokeRequest,
    AgentRotateKeyRequest,
)
from app.services.agent_registry_service import AgentRegistryService

router = APIRouter(prefix="/agents", tags=["AI-Agent Registry"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Register a new AI-Agent identity with version 1 manifest and optional key fingerprint."""
    return AgentRegistryService.register_agent(request, current_user)


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: ACTIVE, SUSPENDED, REVOKED, EXPIRED"),
    organization_id: Optional[str] = Query(None, alias="org_id", description="Filter by organization ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[AgentResponse]:
    """List AI-Agents accessible to the caller."""
    return AgentRegistryService.list_agents(current_user, status_filter, organization_id)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Inspect AI-Agent details, current manifest, and active lifecycle state."""
    return AgentRegistryService.get_agent(agent_id, current_user)


@router.get("/{agent_id}/manifests", response_model=List[AgentManifestResponse])
async def list_agent_manifests(
    agent_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[AgentManifestResponse]:
    """Retrieve complete version history of manifests for an agent."""
    return AgentRegistryService.list_manifests(agent_id, current_user)


@router.put("/{agent_id}/manifest", response_model=AgentResponse)
async def update_agent_manifest(
    agent_id: str,
    request: AgentManifestUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Publish a new versioned manifest (v+1) for an active agent."""
    return AgentRegistryService.update_manifest(agent_id, request, current_user)


@router.post("/{agent_id}/rotate-key", response_model=AgentResponse)
async def rotate_agent_key(
    agent_id: str,
    request: AgentRotateKeyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Rotate the cryptographic public key and fingerprint for an active agent."""
    return AgentRegistryService.rotate_key(agent_id, request, current_user)


@router.post("/{agent_id}/revoke", response_model=AgentResponse)
async def revoke_agent(
    agent_id: str,
    request: AgentRevokeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Permanently revoke an AI-Agent identity."""
    return AgentRegistryService.revoke_agent(agent_id, request.reason, current_user)


@router.post("/{agent_id}/suspend", response_model=AgentResponse)
async def suspend_agent(
    agent_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Temporarily suspend an active AI-Agent identity."""
    return AgentRegistryService.suspend_agent(agent_id, current_user)


@router.post("/{agent_id}/activate", response_model=AgentResponse)
async def activate_agent(
    agent_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentResponse:
    """Re-activate a suspended AI-Agent identity (revoked agents cannot be reactivated)."""
    return AgentRegistryService.activate_agent(agent_id, current_user)
