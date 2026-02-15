from dataclasses import dataclass
from uuid import UUID


@dataclass
class StoredUser:
    email: str
    password_hash: str
    role: str
    id: UUID | None = None


_USERS: dict[str, StoredUser] = {}


def clear_users() -> None:
    _USERS.clear()


def add_user(email: str, password_hash: str, role: str = "user", user_id: UUID | None = None) -> StoredUser:
    user = StoredUser(email=email, password_hash=password_hash, role=role, id=user_id)
    _USERS[email] = user
    return user


def get_user(email: str) -> StoredUser | None:
    return _USERS.get(email)
