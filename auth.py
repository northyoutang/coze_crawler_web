"""
认证模块
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import hashlib

from database import get_db

# 固定账号密码
FIXED_USERNAME = "northyoutang"
FIXED_PASSWORD = "northyoutang@gmail"

# 存储有效的session tokens
valid_sessions = set()


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(username: str, password: str) -> bool:
    """验证用户名密码"""
    return username == FIXED_USERNAME and password == FIXED_PASSWORD


def create_session() -> str:
    """创建session token"""
    token = secrets.token_hex(32)
    valid_sessions.add(token)
    return token


def destroy_session(token: str):
    """销毁session"""
    if token in valid_sessions:
        valid_sessions.remove(token)


def is_session_valid(token: Optional[str]) -> bool:
    """检查session是否有效"""
    return token is not None and token in valid_sessions


async def get_session_from_request(request: Request) -> Optional[str]:
    """从请求中获取session token"""
    # 首先尝试从cookie获取
    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token
    
    # 尝试从Authorization header获取
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    
    return None


async def require_auth(request: Request):
    """认证依赖项"""
    session_token = await get_session_from_request(request)
    if not session_token or not is_session_valid(session_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
