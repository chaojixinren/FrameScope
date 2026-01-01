import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv
from app.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def get_password_hash(password: str) -> str:
    """
    生成密码哈希（直接使用 bcrypt，避免 passlib 兼容性问题）
    
    Args:
        password: 明文密码
        
    Returns:
        str: bcrypt哈希后的密码（字符串格式）
        
    Note:
        bcrypt 限制密码最大长度为 72 字节，如果超过会自动截断
    """
    try:
        # 确保密码是字符串类型
        if not isinstance(password, str):
            password = str(password)
        
        # 转换为字节（bcrypt 需要字节输入）
        password_bytes = password.encode('utf-8')
        password_length = len(password_bytes)
        logger.debug(f"密码加密: 字符长度={len(password)}, 字节长度={password_length}")
        
        # bcrypt 限制：密码不能超过 72 字节
        if password_length > 72:
            logger.warning(f"密码超过 72 字节限制 ({password_length} 字节)，将截断到 72 字节")
            password_bytes = password_bytes[:72]
        
        # 生成 salt 并哈希密码
        # bcrypt.gensalt() 默认 rounds=12，这是安全的默认值
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        
        # 转换为字符串返回
        hashed = hashed_bytes.decode('utf-8')
        logger.debug("密码加密成功")
        return hashed
    except Exception as e:
        logger.error(f"密码加密失败: {e}, 密码类型: {type(password)}, 密码长度: {len(str(password)) if password else 0}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码（直接使用 bcrypt，避免 passlib 兼容性问题）
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码（字符串格式）
        
    Returns:
        bool: 密码是否正确
    """
    try:
        # 转换为字节
        plain_password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        
        # 验证密码
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False


def create_access_token(user_id: int) -> str:
    """
    创建JWT访问令牌
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: JWT token
    """
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[int]:
    """
    验证JWT token并返回用户ID
    
    Args:
        token: JWT token
        
    Returns:
        Optional[int]: 用户ID，如果token无效则返回None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None


def get_token_from_header(authorization: str) -> Optional[str]:
    """
    从Authorization header中提取token
    
    Args:
        authorization: Authorization header值，格式：Bearer <token>
        
    Returns:
        Optional[str]: token字符串，如果格式错误则返回None
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]

