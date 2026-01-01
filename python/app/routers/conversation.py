from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.utils.response import ResponseWrapper as R
from app.utils.status_code import StatusCode
from app.db.conversation_dao import (
    create_conversation,
    get_conversations_by_user_id,
    get_conversation_by_id,
    update_conversation_title,
    delete_conversation,
    get_conversation_count_by_user_id
)
from app.db.message_dao import get_messages_by_conversation_id, get_message_count_by_conversation_id
from app.dependencies.auth import get_current_user
from app.db.models.user import User
from app.db.models.conversation import Conversation

router = APIRouter()


class CreateConversationRequest(BaseModel):
    title: Optional[str] = ""


class UpdateConversationTitleRequest(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: str
    updated_at: str
    message_count: Optional[int] = None


@router.get("/conversations")
def get_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的对话列表
    
    Args:
        limit: 返回数量限制（默认50）
        offset: 偏移量（默认0）
        current_user: 当前用户（通过认证依赖注入）
        
    Returns:
        成功响应，包含对话列表
    """
    try:
        conversations = get_conversations_by_user_id(current_user.id, limit=limit, offset=offset)
        total = get_conversation_count_by_user_id(current_user.id)
        
        conversation_list = []
        for conv in conversations:
            # 计算每个对话的消息数量
            message_count = get_message_count_by_conversation_id(conv.id)
            conversation_list.append({
                "id": conv.id,
                "user_id": conv.user_id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                "message_count": message_count
            })
        
        return R.success(data={
            "conversations": conversation_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }, msg="获取对话列表成功")
        
    except Exception as e:
        return R.error(msg=f"获取对话列表失败: {str(e)}", code=StatusCode.FAIL)


@router.post("/conversations")
def create_conversation_endpoint(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建新对话
    
    Args:
        request: 创建对话请求（title可选）
        current_user: 当前用户（通过认证依赖注入）
        
    Returns:
        成功响应，包含对话信息
    """
    try:
        conversation = create_conversation(
            user_id=current_user.id,
            title=request.title or ""
        )
        
        return R.success(data={
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
        }, msg="创建对话成功")
        
    except Exception as e:
        return R.error(msg=f"创建对话失败: {str(e)}", code=StatusCode.FAIL)


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取对话详情和消息列表
    
    Args:
        conversation_id: 对话ID
        current_user: 当前用户（通过认证依赖注入）
        
    Returns:
        成功响应，包含对话信息和消息列表
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        
        if not conversation:
            return R.error(msg="对话不存在", code=StatusCode.CONVERSATION_NOT_FOUND)
        
        # 验证所有权
        if conversation.user_id != current_user.id:
            return R.error(msg="无权访问该对话", code=StatusCode.CONVERSATION_ACCESS_DENIED)
        
        # 获取消息列表
        messages = get_messages_by_conversation_id(conversation_id)
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })
        
        return R.success(data={
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "messages": message_list
        }, msg="获取对话详情成功")
        
    except Exception as e:
        return R.error(msg=f"获取对话详情失败: {str(e)}", code=StatusCode.FAIL)


@router.put("/conversations/{conversation_id}/title")
def update_conversation_title_endpoint(
    conversation_id: int,
    request: UpdateConversationTitleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    更新对话标题
    
    Args:
        conversation_id: 对话ID
        request: 更新标题请求
        current_user: 当前用户（通过认证依赖注入）
        
    Returns:
        成功响应
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        
        if not conversation:
            return R.error(msg="对话不存在", code=StatusCode.CONVERSATION_NOT_FOUND)
        
        # 验证所有权
        if conversation.user_id != current_user.id:
            return R.error(msg="无权访问该对话", code=StatusCode.CONVERSATION_ACCESS_DENIED)
        
        success = update_conversation_title(conversation_id, request.title)
        
        if not success:
            return R.error(msg="更新对话标题失败", code=StatusCode.FAIL)
        
        return R.success(data=None, msg="更新对话标题成功")
        
    except Exception as e:
        return R.error(msg=f"更新对话标题失败: {str(e)}", code=StatusCode.FAIL)


@router.delete("/conversations/{conversation_id}")
def delete_conversation_endpoint(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    删除对话（级联删除所有消息）
    
    Args:
        conversation_id: 对话ID
        current_user: 当前用户（通过认证依赖注入）
        
    Returns:
        成功响应
    """
    try:
        conversation = get_conversation_by_id(conversation_id)
        
        if not conversation:
            return R.error(msg="对话不存在", code=StatusCode.CONVERSATION_NOT_FOUND)
        
        # 验证所有权
        if conversation.user_id != current_user.id:
            return R.error(msg="无权访问该对话", code=StatusCode.CONVERSATION_ACCESS_DENIED)
        
        success = delete_conversation(conversation_id)
        
        if not success:
            return R.error(msg="删除对话失败", code=StatusCode.FAIL)
        
        return R.success(data=None, msg="删除对话成功")
        
    except Exception as e:
        return R.error(msg=f"删除对话失败: {str(e)}", code=StatusCode.FAIL)

