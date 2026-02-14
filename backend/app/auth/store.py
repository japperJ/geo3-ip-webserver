from dataclasses import dataclass


@dataclass
class StoredUser:
    email: str
    password_hash: str
    role: str


_USERS: dict[str, StoredUser] = {}


def clear_users() -> None:
    _USERS.clear()


def add_user(email: str, password_hash: str, role: str = "user") -> StoredUser:
    user = StoredUser(email=email, password_hash=password_hash, role=role)
    _USERS[email] = user
    return user


def get_user(email: str) -> StoredUser | None:
    return _USERS.get(email)
