from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    badge_number: str | None = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
