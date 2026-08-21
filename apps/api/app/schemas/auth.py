from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    is_active: bool

class TenantResponse(BaseModel):
    id: str
    name: str
