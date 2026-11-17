"""Root API Router for version 1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import (
    aadhaar,
    agents,
    audit,
    auth,
    cases,
    delegation,
    evidence,
    health,
    monitoring,
    ocr,
    organizations,
    pancard,
    policy,
    privacy,
    receipts,
    review,
    risk,
    validation,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(monitoring.router)
api_router.include_router(aadhaar.router)
api_router.include_router(pancard.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(organizations.claims_router)
api_router.include_router(agents.router)
api_router.include_router(delegation.router)
api_router.include_router(cases.router)
api_router.include_router(evidence.router)
api_router.include_router(ocr.router)
api_router.include_router(validation.router)
api_router.include_router(policy.router)
api_router.include_router(review.router)
api_router.include_router(receipts.router)
api_router.include_router(audit.router)
api_router.include_router(risk.router)
api_router.include_router(privacy.router)
