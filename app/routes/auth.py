
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.logger import logger

from ..services.auth_service import (
    authenticate_customer,
    create_access_token,
    register_customer,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=1024)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: int


@router.post("/register", response_model=AuthResponse,
             status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    try:
        customer = register_customer(
            db=db,
            email=request.email,
            password=request.password,
        )
        token = create_access_token(customer.id)

        logger.info("Registration endpoint completed: customer_id=%s",
                    customer.id)

        return AuthResponse(
            access_token=token,
            customer_id=customer.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    except SQLAlchemyError:
        logger.exception("Database error in registration endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register account.",
        ) from None


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    try:
        customer = authenticate_customer(
            db=db,
            email=request.email,
            password=request.password,
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(customer.id)

        logger.info("Login endpoint completed: customer_id=%s",
                    customer.id)

        return AuthResponse(
            access_token=token,
            customer_id=customer.id,
        )

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception("Database error in login endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to log in.",
        ) from None
