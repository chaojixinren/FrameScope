import time
import logging
from sqlalchemy.exc import OperationalError
from app.db.models.models import Model
from app.db.models.providers import Provider
from app.db.models.video_tasks import VideoTask
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.engine import get_engine, Base

logger = logging.getLogger(__name__)

def init_db():
    """初始化数据库，带重试机制处理数据库锁定问题"""
    engine = get_engine()
    max_retries = 5
    retry_delay = 1.0  # 1秒
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("数据库初始化成功")
            return
        except OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                logger.warning(f"数据库被锁定，等待 {wait_time:.1f} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"数据库初始化失败: {e}")
                raise
        except Exception as e:
            logger.error(f"数据库初始化时发生未知错误: {e}")
            raise