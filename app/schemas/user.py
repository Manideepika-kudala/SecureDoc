from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


COMMON_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "123456789",
    "qwerty123",
    "admin123",
    "welcome123",
    "iloveyou"
}


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["owner", "viewer"] = "owner"

    @field_validator("password")
    @classmethod
    def reject_common_passwords(cls, value):
        if value.lower() in COMMON_PASSWORDS:
            raise ValueError("This password is too common. Choose a stronger password.")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    is_active: bool
    role: str
