from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.utils.response import ResponseWrapper as R
from app.utils.status_code import StatusCode
from app.db.user_dao import (
    create_user,
    get_user_by_username,
    get_user_by_phone,
    verify_user_password,
    update_user_online_status
)
from app.utils.auth import create_access_token
from app.dependencies.auth import get_current_user
from app.db.models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    phone_number: Optional[str] = None
    avatar: Optional[str] = None


class LoginRequest(BaseModel):
    username: Optional[str] = None
    phone_number: Optional[str] = None
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "user123",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


@router.post("/register")
def register(request: RegisterRequest):
    """
    用户注册
    
    Args:
        request: 注册请求（username, password, phone_number可选, avatar可选）
        
    Returns:
        成功响应，包含用户信息
    """
    try:
        # 验证输入
        if not request.username or not request.password:
            return R.error(msg="用户名和密码不能为空", code=StatusCode.PARAM_ERROR)
        
        if len(request.password) < 6:
            return R.error(msg="密码长度至少6位", code=StatusCode.PARAM_ERROR)
        
        # 创建用户
        user = create_user(
            username=request.username,
            password=request.password,
            phone_number=request.phone_number,
            avatar=request.avatar
        )
        
        # 生成token
        access_token = create_access_token(user.id)
        
        return R.success(data={
            "user_id": user.id,
            "username": user.username,
            "phone_number": user.phone_number,
            "avatar": user.avatar,
            "access_token": access_token,
            "token_type": "bearer"
        }, msg="注册成功")
        
    except ValueError as e:
        return R.error(msg=str(e), code=StatusCode.PARAM_ERROR)
    except Exception as e:
        return R.error(msg=f"注册失败: {str(e)}", code=StatusCode.AUTH_ERROR)


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录（使用OAuth2标准格式：username字段可以是用户名或手机号）
    
    Args:
        form_data: OAuth2PasswordRequestForm（username字段可以是用户名或手机号，password是密码）
        
    Returns:
        成功响应，包含JWT token和用户信息
    """
    try:
        username_or_phone = form_data.username
        password = form_data.password
        
        if not username_or_phone or not password:
            return R.error(msg="用户名/手机号和密码不能为空", code=StatusCode.PARAM_ERROR)
        
        # 尝试通过用户名查找
        user = get_user_by_username(username_or_phone)
        
        # 如果用户名找不到，尝试通过手机号查找
        if not user:
            user = get_user_by_phone(username_or_phone)
        
        if not user:
            return R.error(msg="用户名或密码错误", code=StatusCode.AUTH_ERROR)
        
        # 验证密码
        if not verify_user_password(user, password):
            return R.error(msg="用户名或密码错误", code=StatusCode.AUTH_ERROR)
        
        # 更新在线状态
        update_user_online_status(user.id, 1)
        
        # 生成token
        access_token = create_access_token(user.id)
        
        return R.success(data={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }, msg="登录成功")
        
    except Exception as e:
        return R.error(msg=f"登录失败: {str(e)}", code=StatusCode.AUTH_ERROR)


@router.post("/login_json")
def login_json(request: LoginRequest):
    """
    用户登录（JSON格式，支持用户名或手机号）
    
    Args:
        request: 登录请求（username或phone_number二选一，password必填）
        
    Returns:
        成功响应，包含JWT token和用户信息
    """
    try:
        if not request.password:
            return R.error(msg="密码不能为空", code=StatusCode.PARAM_ERROR)
        
        if not request.username and not request.phone_number:
            return R.error(msg="用户名或手机号至少提供一个", code=StatusCode.PARAM_ERROR)
        
        # 尝试通过用户名查找
        user = None
        if request.username:
            user = get_user_by_username(request.username)
        
        # 如果用户名找不到，尝试通过手机号查找
        if not user and request.phone_number:
            user = get_user_by_phone(request.phone_number)
        
        if not user:
            return R.error(msg="用户名或密码错误", code=StatusCode.AUTH_ERROR)
        
        # 验证密码
        if not verify_user_password(user, request.password):
            return R.error(msg="用户名或密码错误", code=StatusCode.AUTH_ERROR)
        
        # 更新在线状态
        update_user_online_status(user.id, 1)
        
        # 生成token
        access_token = create_access_token(user.id)
        
        return R.success(data={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }, msg="登录成功")
        
    except Exception as e:
        return R.error(msg=f"登录失败: {str(e)}", code=StatusCode.AUTH_ERROR)


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    Args:
        current_user: 当前用户（通过认证依赖注入）
        
    Returns:
        成功响应，包含用户信息
    """
    return R.success(data={
        "id": current_user.id,
        "username": current_user.username,
        "phone_number": current_user.phone_number,
        "avatar": current_user.avatar,
        "is_online": current_user.is_online,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }, msg="获取用户信息成功")

