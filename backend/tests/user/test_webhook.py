import json
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_500(client):
    """Test that invalid SVIX signature is rejected."""
    with patch("app.user.webhook.settings") as mock_settings:
        mock_settings.CLERK_WEBHOOK_SECRET = "whsec_test123456789012345678901234"

        response = await client.post(
            "/api/v1/webhooks/clerk",
            content=json.dumps({"type": "user.created", "data": {}}),
            headers={
                "Content-Type": "application/json",
                "svix-id": "msg_fake",
                "svix-timestamp": "1234567890",
                "svix-signature": "v1,invalid_signature",
            },
        )

        assert response.status_code == 500


@pytest.mark.asyncio
async def test_webhook_missing_headers_returns_500(client):
    """Test that missing SVIX headers results in error."""
    with patch("app.user.webhook.settings") as mock_settings:
        mock_settings.CLERK_WEBHOOK_SECRET = "whsec_test123456789012345678901234"

        response = await client.post(
            "/api/v1/webhooks/clerk",
            content=json.dumps({"type": "user.created", "data": {}}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 500
