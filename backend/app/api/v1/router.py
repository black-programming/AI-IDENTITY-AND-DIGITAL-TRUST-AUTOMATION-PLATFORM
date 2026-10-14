"""Root API Router for version 1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import cases, health, policy, receipts, review

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(cases.router)
api_router.include_router(policy.router)
api_router.include_router(review.router)
api_router.include_router(receipts.router)
