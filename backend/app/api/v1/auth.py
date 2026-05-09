from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserRegisterResponse,
    LoginResponse,
    ApiResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


@router.post("/register", response_model=ApiResponse)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        nickname=request.nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        code=0,
        data={
            "user_id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
        },
        message="ok",
    )


@router.post("/login", response_model=ApiResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return ApiResponse(
        code=0,
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,
        },
        message="ok",
    )


@router.get("/me", response_model=ApiResponse)
async def get_me(
    user: User = Depends(get_current_user_required),
) -> ApiResponse:
    return ApiResponse(
        code=0,
        data={
            "user_id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
        },
        message="ok",
    )