"""Dependencies for admin control plane endpoints."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User


async def require_admin_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency that enforces admin/editor authentication on admin endpoints.

    If settings.require_admin_auth is False, returns a mock admin user.
    Otherwise:
    - Missing or malformed header -> 401 Unauthorized
    - Invalid or expired token -> 401 Unauthorized
    - Inactive user -> 403 Forbidden
    - Insufficient role (not admin, editor, or website_editor and not superuser) -> 403 Forbidden
    """
    if not getattr(settings, "require_admin_auth", True):
        return User(
            id="admin-dev",
            email="admin@tswebui.local",
            role="admin",
            is_active=True,
            is_superuser=True,
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for admin access",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    allowed_roles = {"admin", "editor", "website_editor"}
    if not user.is_superuser and user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: role '{user.role}' not authorized for admin operations",
        )

    return user
