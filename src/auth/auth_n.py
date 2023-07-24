from typing import Optional


def authenticate_user(token: Optional[str] = None) -> str:
    # FIXME: Implement real auth, this is just for demo purposes
    if token is None:
        return None
    elif token == "mock-admin-token":
        return "admin"
    elif token == "mock-user-1":
        return "user-1"
    else:
        return "user-2"
