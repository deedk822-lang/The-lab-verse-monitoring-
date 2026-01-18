import hashlib
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import redis
from ..models.user import User
from ..core.config import settings

# Initialize Redis for rate limiting
redis_client = redis.from_url(settings.REDIS_URL)

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and extract payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current user from JWT token with rate limiting.
    """
    # Rate limiting
    # Derive client_ip from request.client.host
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Use a non-reversible fingerprint of the token
    token_fingerprint = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    key = f"rate_limit:{client_ip}:{token_fingerprint}"

    # Increment counter and check rate limit
    try:
        current_requests = redis_client.incr(key)
        if current_requests == 1:
            redis_client.expire(key, 60)  # Reset after 1 minute

        if current_requests > settings.REQUESTS_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
    except redis.RedisError:
        # Failing closed is safer. If Redis is down, we can't enforce rate limits.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is temporarily unavailable."
        )

    # Verify token
    payload = verify_token(credentials.credentials)

    # Extract user info from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract tenant and permissions
    tenant_id = payload.get("tenant_id", "default_tenant")

    # Return user with explicit permissions based on claims
    return User(
        id=user_id,
        email=payload.get("email", "unknown@example.com"),
        tenant_id=tenant_id,
        has_glm_access=payload.get("has_glm_access", False),
        has_autoglm_access=payload.get("has_autoglm_access", False),
        has_billing_access=payload.get("has_billing_access", False)
    )
