from fastapi import Depends, HTTPException, status

from app.auth.deps import get_current_user
from app.auth.permissions import require_role


def require_admin(user=Depends(get_current_user)):
    checker = require_role("owner", "admin")
    if not checker(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user
