from datetime import UTC, datetime, timedelta

import httpx
import structlog
from jose import JWTError, jwk, jwt

logger = structlog.get_logger()

_jwks_cache: dict = {"keys": [], "fetched_at": None}
JWKS_CACHE_TTL = timedelta(minutes=60)


async def _fetch_jwks(jwks_url: str) -> list:
    """Fetch and cache JWKS from Clerk."""
    now = datetime.now(UTC)
    if _jwks_cache["keys"] and _jwks_cache["fetched_at"]:
        if now - _jwks_cache["fetched_at"] < JWKS_CACHE_TTL:
            return _jwks_cache["keys"]

    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        keys = response.json()["keys"]

    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    logger.info("jwks.refreshed", key_count=len(keys))
    return keys


async def verify_clerk_jwt(token: str, jwks_url: str) -> dict:
    """Verify a Clerk JWT and return claims."""
    keys = await _fetch_jwks(jwks_url)

    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # Find matching key
    matching_key = None
    for key in keys:
        if key["kid"] == kid:
            matching_key = key
            break

    if not matching_key:
        # Refresh JWKS in case of key rotation
        _jwks_cache["fetched_at"] = None
        keys = await _fetch_jwks(jwks_url)
        for key in keys:
            if key["kid"] == kid:
                matching_key = key
                break

    if not matching_key:
        raise JWTError(f"No matching key found for kid: {kid}")

    public_key = jwk.construct(matching_key)
    claims = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )

    return claims
