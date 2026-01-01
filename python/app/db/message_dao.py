from typing import List, Optional
from app.db.models.message import Message
from app.db.engine import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_message(user_id: int, conversation_id: int, role: str, content: str) -> Message:
    """
    创建消息
    
    Args:
        user_id: 用户ID
        conversation_id: 对话ID
        role: 角色（"user" 或 "assistant"）
        content: 消息内容
        
    Returns:
        Message: 创建的消息对象
    """
    db = next(get_db())
    try:
        message = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        logger.info(f"消息创建成功: conversation_id={conversation_id}, role={role}, message_id={message.id}")
        return message
    except Exception as e:
        db.rollback()
        logger.error(f"创建消息失败: {e}")
        raise
    finally:
        db.close()


def get_messages_by_conversation_id(conversation_id: int, limit: int = 50) -> List[Message]:
    """
    获取对话的消息列表（按时间正序，默认最近50条）
    
    Args:
        conversation_id: 对话ID
        limit: 返回数量限制（默认50条，避免token超限）
        
    Returns:
        List[Message]: 消息列表（按created_at升序）
    """
    db = next(get_db())
    try:
        # 先获取总数
        total = db.query(Message).filter_by(conversation_id=conversation_id).count()
        
        # 如果消息数量超过limit，只返回最近limit条
        if total > limit:
            offset = total - limit
            return db.query(Message).filter_by(conversation_id=conversation_id).order_by(
                Message.created_at.asc()
            ).offset(offset).limit(limit).all()
        else:
            return db.query(Message).filter_by(conversation_id=conversation_id).order_by(
                Message.created_at.asc()
            ).all()
    finally:
        db.close()


def get_message_count_by_conversation_id(conversation_id: int) -> int:
    """
    获取对话的消息数量
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        int: 消息数量
    """
    db = next(get_db())
    try:
        return db.query(Message).filter_by(conversation_id=conversation_id).count()
    finally:
        db.close()


def delete_messages_by_conversation_id(conversation_id: int) -> bool:
    """
    删除对话的所有消息（由Conversation级联处理，但保留此函数作为备用）
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        bool: 是否删除成功
    """
    db = next(get_db())
    try:
        db.query(Message).filter_by(conversation_id=conversation_id).delete()
        db.commit()
        logger.info(f"对话消息删除成功: conversation_id={conversation_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"删除对话消息失败: {e}")
        return False
    finally:
        db.close()

