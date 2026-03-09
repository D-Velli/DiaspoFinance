from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import JWTError

from app.core.security import _jwks_cache, verify_clerk_jwt

MOCK_JWKS_URL = "https://test.clerk.accounts.dev/.well-known/jwks.json"


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Reset JWKS cache between tests."""
    _jwks_cache["keys"] = []
    _jwks_cache["fetched_at"] = None
    yield
    _jwks_cache["keys"] = []
    _jwks_cache["fetched_at"] = None


def _mock_httpx_client(mock_keys):
    """Create a properly mocked httpx AsyncClient."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"keys": mock_keys}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    return mock_client


@pytest.mark.asyncio
async def test_verify_jwt_no_matching_kid_raises():
    """Test that a JWT with unknown kid raises JWTError after JWKS refresh."""
    mock_keys = [{"kid": "key-1", "kty": "RSA", "n": "abc", "e": "AQAB"}]
    mock_client = _mock_httpx_client(mock_keys)

    with (
        patch("app.core.security.httpx.AsyncClient") as mock_cls,
        patch("app.core.security.jwt.get_unverified_header", return_value={"kid": "unknown-kid"}),
    ):
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(JWTError, match="No matching key found"):
            await verify_clerk_jwt("fake.jwt.token", MOCK_JWKS_URL)


@pytest.mark.asyncio
async def test_verify_jwt_fetches_jwks():
    """Test that JWKS are fetched when cache is empty."""
    mock_keys = [{"kid": "key-1", "kty": "RSA", "n": "abc", "e": "AQAB"}]
    mock_client = _mock_httpx_client(mock_keys)

    with (
        patch("app.core.security.httpx.AsyncClient") as mock_cls,
        patch("app.core.security.jwt.get_unverified_header", return_value={"kid": "key-1"}),
        patch("app.core.security.jwk.construct"),
        patch("app.core.security.jwt.decode", return_value={"sub": "user_123"}),
    ):
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        claims = await verify_clerk_jwt("fake.jwt.token", MOCK_JWKS_URL)

        assert claims["sub"] == "user_123"
        mock_client.get.assert_called_once_with(MOCK_JWKS_URL)
