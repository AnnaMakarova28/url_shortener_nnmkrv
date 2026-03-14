from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
