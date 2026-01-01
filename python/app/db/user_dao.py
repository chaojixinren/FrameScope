from typing import Optional
from app.db.models.user import User
from app.db.engine import get_db
from app.utils.logger import get_logger
from app.utils.auth import get_password_hash, verify_password

logger = get_logger(__name__)


def create_user(username: str, password: str, phone_number: Optional[str] = None, avatar: Optional[str] = None) -> User:
    """
    创建新用户
    
    Args:
        username: 用户名
        password: 明文密码（会自动加密）
        phone_number: 手机号（可选）
        avatar: 头像URL（可选）
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        Exception: 如果用户名或手机号已存在
    """
    db = next(get_db())
    try:
        # 检查用户名是否已存在
        if db.query(User).filter_by(username=username).first():
            raise ValueError(f"用户名 {username} 已存在")
        
        # 检查手机号是否已存在（如果提供了手机号）
        if phone_number and db.query(User).filter_by(phone_number=phone_number).first():
            raise ValueError(f"手机号 {phone_number} 已存在")
        
        # 加密密码
        hashed_password = get_password_hash(password)
        
        # 创建用户
        user = User(
            username=username,
            password=hashed_password,
            phone_number=phone_number,
            avatar=avatar,
            is_online=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"用户创建成功: username={username}, id={user.id}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"创建用户失败: {e}")
        raise
    finally:
        db.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """
    根据ID获取用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        Optional[User]: 用户对象，如果不存在则返回None
    """
    db = next(get_db())
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()


def get_user_by_username(username: str) -> Optional[User]:
    """
    根据用户名获取用户
    
    Args:
        username: 用户名
        
    Returns:
        Optional[User]: 用户对象，如果不存在则返回None
    """
    db = next(get_db())
    try:
        return db.query(User).filter_by(username=username).first()
    finally:
        db.close()


def get_user_by_phone(phone_number: str) -> Optional[User]:
    """
    根据手机号获取用户
    
    Args:
        phone_number: 手机号
        
    Returns:
        Optional[User]: 用户对象，如果不存在则返回None
    """
    db = next(get_db())
    try:
        return db.query(User).filter_by(phone_number=phone_number).first()
    finally:
        db.close()


def update_user_online_status(user_id: int, is_online: int) -> bool:
    """
    更新用户在线状态
    
    Args:
        user_id: 用户ID
        is_online: 在线状态（0=离线, 1=在线）
        
    Returns:
        bool: 是否更新成功
    """
    db = next(get_db())
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"用户不存在: user_id={user_id}")
            return False
        
        user.is_online = is_online
        db.commit()
        logger.info(f"用户在线状态更新: user_id={user_id}, is_online={is_online}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户在线状态失败: {e}")
        return False
    finally:
        db.close()


def verify_user_password(user: User, password: str) -> bool:
    """
    验证用户密码
    
    Args:
        user: 用户对象
        password: 明文密码
        
    Returns:
        bool: 密码是否正确
    """
    return verify_password(password, user.password)

