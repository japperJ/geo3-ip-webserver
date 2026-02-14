from app.auth.store import StoredUser


def require_role(*allowed_roles: str):
    def checker(user: StoredUser) -> bool:
        return user.role in allowed_roles

    return checker
