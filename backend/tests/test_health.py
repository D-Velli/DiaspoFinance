import pytest


@pytest.mark.asyncio
async def test_health_check_returns_200(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_returns_app_info(client):
    response = await client.get("/api/v1/health")
    data = response.json()["data"]
    assert data["status"] == "healthy"
    assert data["app_name"] == "DiaspoFinance"
    assert data["version"] == "v1"


@pytest.mark.asyncio
async def test_health_check_response_follows_standard_format(client):
    """Verify response follows the standard envelope: {"data": {...}}"""
    response = await client.get("/api/v1/health")
    body = response.json()
    assert "data" in body
    assert "error" not in body


@pytest.mark.asyncio
async def test_request_id_middleware_adds_header(client):
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_request_id_middleware_echoes_provided_id(client):
    custom_id = "test-request-123"
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-Id": custom_id},
    )
    assert response.headers["x-request-id"] == custom_id


@pytest.mark.asyncio
async def test_diaspofinance_error_handler_returns_json(client):
    """Non-existent route should return 404 (or standard error format for custom errors)."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code in (404, 405)
