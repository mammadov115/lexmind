import bcrypt
from slugify import slugify


def hash_password(password: str) -> str:
    """Generate a bcrypt hash of the plain password."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed value."""
    pw_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except ValueError:
        return False


def slugify_name(name: str) -> str:
    """Convert a name into a URL-friendly, lowercased slug."""
    return slugify(name)
