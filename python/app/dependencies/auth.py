from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from app.db.models.user import User
from app.db.user_dao import get_user_by_id
from app.utils.auth import verify_access_token
from app.utils.status_code import StatusCode

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> User:
    """
    认证依赖，从JWT token中获取当前用户
    
    Args:
        token: JWT token（从Authorization header自动提取）
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """
    可选的认证依赖，如果token不存在或无效，返回None（用于支持匿名用户）
    
    Args:
        token: JWT token（从Authorization header自动提取）
        
    Returns:
        Optional[User]: 当前用户对象，如果未认证则返回None
    """
    if not token:
        return None
    
    user_id = verify_access_token(token)
    if user_id is None:
        return None
    
    return get_user_by_id(user_id)

