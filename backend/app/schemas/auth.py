from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", v):
            raise ValueError("Password must contain at least one lowercase letter, one uppercase letter, and one digit")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    user_id: str
    email: str
    nickname: str | None = None

    class Config:
        from_attributes = True


class UserRegisterResponse(BaseModel):
    user_id: str
    email: str
    nickname: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class ApiResponse(BaseModel):
    code: int = 0
    data: dict | list | None = None
    message: str = "ok"