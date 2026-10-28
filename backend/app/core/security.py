import uuid
from typing import Dict, Any, Optional
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    DecodeError,
    PyJWTError,
)
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging import logger

security_scheme = HTTPBearer(auto_error=False)


class SupabaseAuthVerifier:
    def __init__(self):
        self._jwks_client: Optional[jwt.PyJWKClient] = None

    def _get_jwks_client(self) -> Optional[jwt.PyJWKClient]:
        if not self._jwks_client:
            jwks_url = settings.SUPABASE_JWKS_URL
            if not jwks_url and settings.SUPABASE_URL:
                clean_url = settings.SUPABASE_URL.rstrip("/")
                jwks_url = f"{clean_url}/auth/v1/.well-known/jwks.json"

            if jwks_url:
                try:
                    self._jwks_client = jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
                except Exception as e:
                    logger.warning(f"Could not initialize JWKS client for {jwks_url}: {e}")
        return self._jwks_client

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Validates Supabase JWT signature, expiration, issuer, and audience.
        Returns the decoded payload.
        Raises HTTPException(401) on any failure.
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Unverified header inspection to check algorithm and key ID
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        validation_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": bool(settings.SUPABASE_AUDIENCE),
            "require": ["exp", "sub"],
        }

        # Verification using symmetric secret (HS256) or JWKS (RS256/ES256)
        signing_key = None
        key_or_secret = None

        if alg.startswith("RS") or alg.startswith("ES"):
            jwks_client = self._get_jwks_client()
            if jwks_client:
                try:
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    key_or_secret = signing_key.key
                except Exception as e:
                    logger.warning(f"Failed to fetch public key from JWKS: {e}")

        # Fallback to SUPABASE_JWT_SECRET
        if not key_or_secret:
            if settings.SUPABASE_JWT_SECRET:
                key_or_secret = settings.SUPABASE_JWT_SECRET
            else:
                # If neither secret nor JWKS is available, cannot verify token
                logger.error("No Supabase verification secret or JWKS configured")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication server configuration error",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        try:
            payload = jwt.decode(
                token,
                key_or_secret,
                algorithms=[alg, "HS256", "RS256", "ES256"],
                audience=settings.SUPABASE_AUDIENCE if settings.SUPABASE_AUDIENCE else None,
                issuer=settings.supabase_issuer if settings.supabase_issuer else None,
                options=validation_options,
            )
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token audience is invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token issuer is invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (InvalidSignatureError, DecodeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract and validate subject as valid UUID
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            uuid.UUID(str(sub))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Subject identifier is not a valid UUID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload


auth_verifier = SupabaseAuthVerifier()


async def get_current_user_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """Dependency that extracts and validates the Bearer JWT token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_verifier.verify_token(credentials.credentials)


async def get_current_user_id(
    payload: Dict[str, Any] = Depends(get_current_user_token_payload),
) -> uuid.UUID:
    """Dependency returning the verified user UUID from the token."""
    return uuid.UUID(str(payload["sub"]))
