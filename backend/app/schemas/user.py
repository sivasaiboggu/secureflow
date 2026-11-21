from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[str] = "user"

class UserCreate(UserBase):
    # Twelve characters is the project's own bar: the seed script already
    # refuses admin passwords shorter than 12, while this endpoint used
    # to accept a one-character password. The 128 cap keeps the password
    # hash itself bounded. A blank or whitespace-only organization name
    # is rejected the same way, before any row is written.
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=1, max_length=100)

    @field_validator("organization_name", mode="before")
    @classmethod
    def _strip_organization_name(cls, value):
        return value.strip() if isinstance(value, str) else value

class UserResponse(UserBase):
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RefreshRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    user: UserResponse

class UserLogin(BaseModel):
    email: EmailStr
    password: str
