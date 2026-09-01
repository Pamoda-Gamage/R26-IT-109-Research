from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # hardcoded for demo


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str


class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str | None = None


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest):
    if payload.username != ADMIN_USERNAME or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    return {"access_token": "admin-token-demo", "token_type": "bearer", "role": "admin"}


@router.post("/user/register", response_model=UserLoginResponse)
async def user_register(payload: UserRegisterRequest):
    import uuid

    user_id = str(uuid.uuid4())
    return {
        "access_token": f"user-token-{user_id}",
        "token_type": "bearer",
        "role": "user",
        "user_id": user_id,
    }


@router.post("/user/login", response_model=UserLoginResponse)
async def user_login(payload: UserLoginRequest):
    import uuid

    user_id = str(uuid.uuid4())
    return {
        "access_token": f"user-token-{user_id}",
        "token_type": "bearer",
        "role": "user",
        "user_id": user_id,
    }
