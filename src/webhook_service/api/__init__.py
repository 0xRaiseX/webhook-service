from fastapi import APIRouter
from . import endpoints, subscriptions, events, deliveries

router = APIRouter()
router.include_router(endpoints.router, prefix="/endpoints", tags=["endpoints"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(deliveries.router, prefix="/deliveries", tags=["deliveries"])

