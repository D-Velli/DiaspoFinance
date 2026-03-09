import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.exceptions import DiaspoFinanceError
from app.user import service as user_service

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Clerk webhooks with SVIX signature verification."""
    body = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }

    wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
    try:
        event = wh.verify(body, headers)
    except WebhookVerificationError:
        logger.error("webhook.clerk.invalid_signature")
        raise DiaspoFinanceError(
            message="Invalid webhook signature",
            code="WEBHOOK_INVALID",
            status_code=400,
        )

    event_type = event.get("type")
    data = event.get("data", {})

    if event_type == "user.created":
        email_addresses = data.get("email_addresses", [])
        phone_numbers = data.get("phone_numbers", [])
        await user_service.create_or_sync_user(
            db,
            clerk_id=data["id"],
            email=email_addresses[0]["email_address"] if email_addresses else "",
            display_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            phone=phone_numbers[0]["phone_number"] if phone_numbers else None,
        )
        logger.info("webhook.clerk.user_created", clerk_id=data["id"])

    elif event_type == "user.updated":
        email_addresses = data.get("email_addresses", [])
        phone_numbers = data.get("phone_numbers", [])
        await user_service.update_user(
            db,
            clerk_id=data["id"],
            email=email_addresses[0]["email_address"] if email_addresses else None,
            display_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            phone=phone_numbers[0]["phone_number"] if phone_numbers else None,
        )
        logger.info("webhook.clerk.user_updated", clerk_id=data["id"])

    return {"data": {"status": "ok"}}
