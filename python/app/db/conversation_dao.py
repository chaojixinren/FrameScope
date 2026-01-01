from typing import List, Optional
from sqlalchemy import exists
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.engine import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_conversation(user_id: int, title: str = "") -> Conversation:
    """
    创建新对话
    
    Args:
        user_id: 用户ID
        title: 对话标题（默认为空字符串，后续可自动生成）
        
    Returns:
        Conversation: 创建的对话对象
    """
    db = next(get_db())
    try:
        conversation = Conversation(
            user_id=user_id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        logger.info(f"对话创建成功: user_id={user_id}, conversation_id={conversation.id}")
        return conversation
    except Exception as e:
        db.rollback()
        logger.error(f"创建对话失败: {e}")
        raise
    finally:
        db.close()


def get_conversations_by_user_id(user_id: int, limit: int = 50, offset: int = 0) -> List[Conversation]:
    """
    获取用户的对话列表（按更新时间倒序）
    只返回有assistant消息的对话（即已完成的对话）
    
    Args:
        user_id: 用户ID
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        List[Conversation]: 对话列表（只包含有assistant消息的对话）
    """
    db = next(get_db())
    try:
        # 只返回有assistant消息的对话（即已完成的对话）
        # 使用EXISTS子查询检查是否存在assistant消息
        return db.query(Conversation).filter_by(user_id=user_id).filter(
            exists().where(
                (Message.conversation_id == Conversation.id) & 
                (Message.role == "assistant")
            )
        ).order_by(
            Conversation.updated_at.desc()
        ).offset(offset).limit(limit).all()
    finally:
        db.close()


def get_conversation_by_id(conversation_id: int) -> Optional[Conversation]:
    """
    根据ID获取对话
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        Optional[Conversation]: 对话对象，如果不存在则返回None
    """
    db = next(get_db())
    try:
        return db.query(Conversation).filter_by(id=conversation_id).first()
    finally:
        db.close()


def update_conversation_title(conversation_id: int, title: str) -> bool:
    """
    更新对话标题
    
    Args:
        conversation_id: 对话ID
        title: 新标题
        
    Returns:
        bool: 是否更新成功
    """
    db = next(get_db())
    try:
        conversation = db.query(Conversation).filter_by(id=conversation_id).first()
        if not conversation:
            logger.warning(f"对话不存在: conversation_id={conversation_id}")
            return False
        
        conversation.title = title
        db.commit()
        logger.info(f"对话标题更新成功: conversation_id={conversation_id}, title={title}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"更新对话标题失败: {e}")
        return False
    finally:
        db.close()


def delete_conversation(conversation_id: int) -> bool:
    """
    删除对话（级联删除所有消息）
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        bool: 是否删除成功
    """
    db = next(get_db())
    try:
        conversation = db.query(Conversation).filter_by(id=conversation_id).first()
        if not conversation:
            logger.warning(f"对话不存在: conversation_id={conversation_id}")
            return False
        
        db.delete(conversation)
        db.commit()
        logger.info(f"对话删除成功: conversation_id={conversation_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"删除对话失败: {e}")
        return False
    finally:
        db.close()


def get_conversation_count_by_user_id(user_id: int) -> int:
    """
    获取用户的对话数量（只统计有assistant消息的对话）
    
    Args:
        user_id: 用户ID
        
    Returns:
        int: 对话数量（只统计已完成的对话）
    """
    db = next(get_db())
    try:
        # 只统计有assistant消息的对话
        # 使用EXISTS子查询检查是否存在assistant消息
        return db.query(Conversation).filter_by(user_id=user_id).filter(
            exists().where(
                (Message.conversation_id == Conversation.id) & 
                (Message.role == "assistant")
            )
        ).count()
    finally:
        db.close()

