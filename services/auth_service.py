
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.logger import logger
from app.models.customer import Customer



password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return a secure hash of a customer's password."""

    if not password or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    if len(password) > 1024:
        raise ValueError("Password is too long.")

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its stored hash."""

    if not password or not password_hash:
        return False

    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        logger.warning("Password hash verification failed.")
        return False


def _validate_jwt_settings() -> None:
    """Fail closed if secure token settings are missing."""

    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be configured with a strong secret."
        )

    if settings.JWT_ALGORITHM != "HS256":
        raise RuntimeError("Unsupported JWT signing algorithm.")

    if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError("Token expiry must be positive.")


def register_customer(
    db: Session,
    email: str,
    password: str,
) -> Customer:
    """Create a customer account."""

    normalized_email = email.strip().lower()

    if not normalized_email or "@" not in normalized_email:
        raise ValueError("A valid email address is required.")

    password_hash = hash_password(password)

    customer = Customer(
        email=normalized_email,
        password_hash=password_hash,
        is_active=True,
    )

    try:
        db.add(customer)
        db.commit()
        db.refresh(customer)

        logger.info("Customer registered: customer_id=%s", customer.id)
        return customer

    except IntegrityError:
        db.rollback()
        logger.info("Registration rejected because the email already exists.")
        raise ValueError("An account with this email already exists.") from None

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during customer registration.")
        raise


def authenticate_customer(
    db: Session,
    email: str,
    password: str,
) -> Customer | None:
    """Return an active customer if the credentials are valid."""

    normalized_email = email.strip().lower()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.email == normalized_email)
            .first()
        )

        if (
            customer is None
            or not customer.is_active
            or not verify_password(password, customer.password_hash)
        ):
            logger.info("Customer login rejected.")
            return None

        logger.info("Customer login successful: customer_id=%s", customer.id)
        return customer

    except SQLAlchemyError:
        logger.exception("Database error during customer authentication.")
        raise


def create_access_token(customer_id: int) -> str:
    """Create a signed JWT access token for an authenticated customer."""

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    _validate_jwt_settings()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(customer_id),
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    logger.info("Access token created for customer_id=%s", customer_id)
    return token


def decode_access_token(token: str) -> int:
    """Validate a JWT and return its customer ID."""

    _validate_jwt_settings()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdigit():
            raise ValueError("Invalid token subject.")

        customer_id = int(subject)
        if customer_id <= 0:
            raise ValueError("Invalid token subject.")

        return customer_id

    except jwt.InvalidTokenError:
        logger.info("Rejected invalid or expired access token.")
        raise ValueError("Invalid or expired access token.") from None
