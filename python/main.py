import os
import sys
import uuid
import re
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers
from app.exceptions.exception_handlers import register_exception_handlers
# from app.db.model_dao import init_model_table
# from app.db.provider_dao import init_provider_table
from app.utils.logger import get_logger
from app import create_app
from app.transcriber.transcriber_provider import get_transcriber
from ffmpeg_helper import ensure_ffmpeg_or_raise

# 添加 agent 目录到路径，以便导入 agent 模块
agent_path = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_path))

from agent.graphs.agent_graph import build_multi_video_graph, build_example_video_graph
from agent.graphs.state import AIState
from app.db.conversation_dao import create_conversation, get_conversation_by_id, update_conversation_title
from app.db.message_dao import create_message, get_messages_by_conversation_id
from app.utils.conversation_helper import generate_conversation_title
from app.dependencies.auth import get_current_user
from app.db.models.user import User
from fastapi import Depends
from app.utils.response import ResponseWrapper as R

# 为了向后兼容，保留 MultiVideoState 作为 AIState 的别名
MultiVideoState = AIState

logger = get_logger(__name__)
load_dotenv()

# 读取 .env 中的路径
static_path = os.getenv('STATIC', '/static')
out_dir = os.getenv('OUT_DIR', './static/screenshots')

# 自动创建本地目录（static 和 static/screenshots）
static_dir = "static"
uploads_dir = "uploads"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    get_transcriber(transcriber_type=os.getenv("TRANSCRIBER_TYPE", "groq"))
    seed_default_providers()
    yield

app = create_app(lifespan=lifespan)

# CORS 配置：允许的源列表
# 支持从环境变量读取，如果没有则使用默认值
cors_origins_env = os.getenv("CORS_ORIGINS")
if cors_origins_env:
    # 从环境变量读取，支持逗号分隔的多个源
    origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # 默认允许的源（包含常见开发端口）
    origins = [
        "http://localhost",
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:3000",  # React 默认端口
        "http://localhost:8080",  # Vue CLI 默认端口
        "http://127.0.0.1",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://tauri.localhost",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.mount(static_path, StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# ==================== AI 服务路由（从 agent/server.py 合并） ====================

class MultiVideoRequest(BaseModel):
    """多视频搜索和总结请求模型"""
    question: str = Field(..., min_length=1, max_length=5000, description="用户问题（例如：某品牌的相机怎么样）")
    session_id: Optional[str] = Field(None, max_length=255, description="会话ID")
    conversation_id: Optional[int] = Field(None, description="对话ID（可选，如果提供则加载历史消息）")
    model_name: Optional[str] = Field(None, description="GPT 模型名称（可选，不提供则使用默认）")
    provider_id: Optional[str] = Field(None, description="提供商 ID（可选，不提供则使用默认）")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("问题不能为空")
        if len(set(v)) < 3 and len(v) > 100:
            raise ValueError("问题内容无效")
        return v.strip()
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("会话ID格式无效")
        return v


class MultiVideoResponse(BaseModel):
    """多视频搜索和总结响应模型"""
    success: bool
    answer: str
    metadata: Optional[Dict[str, Any]] = None  # 包含视频数量、处理时间等信息


class ExampleVideoRequest(BaseModel):
    """示例视频处理请求模型"""
    question: str = Field(..., min_length=1, max_length=5000, description="用户问题（例如：这些视频的内容是什么）")
    video_ids: List[str] = Field(..., min_items=1, description="视频ID列表（例如：['BV1Dk4y1X71E', 'BV1JD4y1z7vc']）")
    session_id: Optional[str] = Field(None, max_length=255, description="会话ID")
    conversation_id: Optional[int] = Field(None, description="对话ID（可选，如果提供则加载历史消息）")
    model_name: Optional[str] = Field(None, description="GPT 模型名称（可选，不提供则使用默认）")
    provider_id: Optional[str] = Field(None, description="提供商 ID（可选，不提供则使用默认）")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("问题不能为空")
        return v.strip()
    
    @field_validator('video_ids')
    @classmethod
    def validate_video_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("视频ID列表不能为空")
        # 验证视频ID格式（B站BV号）
        for video_id in v:
            if not re.match(r'^BV[0-9A-Za-z]+$', video_id):
                raise ValueError(f"无效的视频ID格式: {video_id}，应为BV号（如BV1Dk4y1X71E）")
        return v


async def run_multi_video_query(
    question: str,
    user_id: int,
    session_id: str = None,
    conversation_id: Optional[int] = None,
    model_name: str = None,
    provider_id: str = None,
) -> MultiVideoState:
    """
    运行多视频搜索和总结查询
    
    Args:
        question: 用户问题
        user_id: 用户ID
        session_id: 会话ID（可选）
        conversation_id: 对话ID（可选，如果提供则加载历史消息）
        model_name: 模型名称（可选）
        provider_id: 提供商ID（可选）
        
    Returns:
        MultiVideoState: 包含答案、笔记结果等信息的最终状态
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # 处理对话历史
    history = []
    current_conversation_id = conversation_id
    previous_summary = None  # 用于存储之前的视频总结
    
    if conversation_id:
        # 加载历史消息
        messages = get_messages_by_conversation_id(conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        logger.info(f"加载对话历史: conversation_id={conversation_id}, 消息数={len(history)}")
        
        # 从历史消息中提取第一次的总结（通常是第一条 assistant 消息，包含完整的视频总结）
        # 查找第一条 assistant 消息，如果它看起来像视频总结（包含关键帧、视频链接等），就作为 previous_summary
        for msg in messages:
            if msg.role == "assistant":
                content = msg.content
                # 判断是否是视频总结：包含关键帧图片链接或视频链接
                if "![关键帧" in content or "查看原片" in content or "bilibili.com/video" in content:
                    previous_summary = content
                    logger.info(f"从历史消息中提取到之前的视频总结（长度: {len(content)} 字符）")
                    break
    else:
        # 创建新对话（标题暂为空，后续自动生成）
        conversation = create_conversation(user_id=user_id, title="")
        current_conversation_id = conversation.id
        logger.info(f"创建新对话: conversation_id={current_conversation_id}")
    
    # Build graph
    graph = build_multi_video_graph()
    
    # Initialize state
    initial_state: MultiVideoState = {
        "question": question,
        "user_id": user_id,
        "session_id": session_id,
        "history": history,
        "timestamp": None,
        "video_urls": [],
        "search_query": None,
        "note_results": [],
        "model_name": model_name,
        "provider_id": provider_id,
        "note_generation_status": None,
        "summary_result": previous_summary,  # 如果是后续提问，这里会包含之前的总结
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    # Run graph (异步)
    logger.info(f"Starting Multi-Video Graph - User ID: {user_id}, Conversation ID: {current_conversation_id}, Question: {question}")
    
    result = await graph.ainvoke(initial_state)
    
    # 保存消息到数据库
    answer = result.get("answer", "")
    if current_conversation_id and answer:
        try:
            # 保存用户消息
            create_message(
                user_id=user_id,
                conversation_id=current_conversation_id,
                role="user",
                content=question
            )
            # 保存助手回复
            create_message(
                user_id=user_id,
                conversation_id=current_conversation_id,
                role="assistant",
                content=answer
            )
            logger.info(f"消息已保存到对话: conversation_id={current_conversation_id}")
            
            # 如果对话标题为空，自动生成标题
            conversation = get_conversation_by_id(current_conversation_id)
            if conversation and not conversation.title:
                try:
                    title = await generate_conversation_title(
                        question=question,
                        answer=answer,
                        model_name=model_name,
                        provider_id=provider_id
                    )
                    update_conversation_title(current_conversation_id, title)
                    logger.info(f"对话标题已生成: {title}")
                except Exception as e:
                    logger.error(f"生成对话标题失败: {e}")
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            traceback.print_exc()
    
    return result


@app.post("/api/multi_video")
async def multi_video_endpoint(
    request: MultiVideoRequest,
    current_user: User = Depends(get_current_user)
):
    """
    处理多视频搜索和总结请求的核心接口（需要认证）
    
    流程：
    1. Agent1 搜索相关视频
    2. 并发生成每个视频的笔记
    3. Agent2 对多个笔记进行多角度总结
    
    Args:
        request: 包含 question 等的请求
        current_user: 当前认证用户（通过JWT token自动获取）
        
    Returns:
        MultiVideoResponse: 包含答案和元数据的响应
    """
    try:
        # 从认证用户获取 user_id（更安全，防止伪造）
        user_id = current_user.id
        
        # 调用多视频工作流
        result = await run_multi_video_query(
            question=request.question,
            user_id=user_id,
            session_id=request.session_id or f"session_{user_id}",
            conversation_id=request.conversation_id,
            model_name=request.model_name,
            provider_id=request.provider_id,
        )
        
        # 提取响应数据
        answer = result.get("answer", "")
        metadata = result.get("metadata")
        
        # 确保answer不为空
        if not answer:
            answer = "抱歉，暂时无法生成总结内容。"
        
        # 返回标准化的响应（使用ResponseWrapper以匹配前端期望的格式）
        return R.success(data=MultiVideoResponse(
            success=True,
            answer=answer,
            metadata=metadata
        ))
        
    except ValueError as e:
        return R.error(code=400, msg=f"输入验证失败: {str(e)}")
    except Exception as e:
        error_detail = str(e)
        logger.error(f"Error in multi_video_endpoint: {error_detail}")
        traceback.print_exc()
        return R.error(code=500, msg=f"处理失败: {error_detail}")


async def run_example_video_query(
    question: str,
    video_ids: List[str],
    user_id: int,
    session_id: str = None,
    conversation_id: Optional[int] = None,
    model_name: str = None,
    provider_id: str = None,
) -> MultiVideoState:
    """
    运行示例视频处理查询（使用example目录下的视频）
    
    Args:
        question: 用户问题
        video_ids: 视频ID列表
        user_id: 用户ID
        session_id: 会话ID（可选）
        conversation_id: 对话ID（可选，如果提供则加载历史消息）
        model_name: 模型名称（可选）
        provider_id: 提供商ID（可选）
        
    Returns:
        MultiVideoState: 包含答案、笔记结果等信息的最终状态
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # 处理对话历史
    history = []
    current_conversation_id = conversation_id
    
    if conversation_id:
        # 加载历史消息
        messages = get_messages_by_conversation_id(conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        logger.info(f"加载对话历史: conversation_id={conversation_id}, 消息数={len(history)}")
    else:
        # 创建新对话（标题暂为空，后续自动生成）
        conversation = create_conversation(user_id=user_id, title="")
        current_conversation_id = conversation.id
        logger.info(f"创建新对话: conversation_id={current_conversation_id}")
    
    # Build graph（使用example视频图）
    graph = build_example_video_graph()
    
    # Initialize state
    initial_state: MultiVideoState = {
        "question": question,
        "user_id": user_id,
        "session_id": session_id,
        "history": history,
        "timestamp": None,
        "video_urls": [],  # example模式下不需要
        "video_ids": video_ids,  # 传入视频ID列表
        "search_query": None,
        "note_results": [],
        "model_name": model_name,
        "provider_id": provider_id,
        "note_generation_status": None,
        "summary_result": None,
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    # Run graph (异步)
    logger.info(f"Starting Example Video Graph - User ID: {user_id}, Conversation ID: {current_conversation_id}, Video IDs: {video_ids}")
    
    result = await graph.ainvoke(initial_state)
    
    # 保存消息到数据库
    answer = result.get("answer", "")
    if current_conversation_id and answer:
        try:
            # 保存用户消息
            create_message(
                user_id=user_id,
                conversation_id=current_conversation_id,
                role="user",
                content=question
            )
            # 保存助手回复
            create_message(
                user_id=user_id,
                conversation_id=current_conversation_id,
                role="assistant",
                content=answer
            )
            logger.info(f"消息已保存到对话: conversation_id={current_conversation_id}")
            
            # 如果对话标题为空，自动生成标题
            conversation = get_conversation_by_id(current_conversation_id)
            if conversation and not conversation.title:
                try:
                    title = await generate_conversation_title(
                        question=question,
                        answer=answer,
                        model_name=model_name,
                        provider_id=provider_id
                    )
                    update_conversation_title(current_conversation_id, title)
                    logger.info(f"对话标题已生成: {title}")
                except Exception as e:
                    logger.error(f"生成对话标题失败: {e}")
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            traceback.print_exc()
    
    return result


@app.post("/api/example_video")
async def example_video_endpoint(
    request: ExampleVideoRequest,
    current_user: User = Depends(get_current_user)
):
    """
    处理示例视频处理请求的接口（需要认证）
    
    流程：
    1. 直接从example目录读取指定视频ID的视频文件
    2. 并发生成每个视频的笔记
    3. Agent2 对多个笔记进行多角度总结
    
    Args:
        request: 包含 question 和 video_ids 的请求
        current_user: 当前认证用户（通过JWT token自动获取）
        
    Returns:
        MultiVideoResponse: 包含答案和元数据的响应
    """
    try:
        # 从认证用户获取 user_id
        user_id = current_user.id
        
        # 调用示例视频工作流
        result = await run_example_video_query(
            question=request.question,
            video_ids=request.video_ids,
            user_id=user_id,
            session_id=request.session_id or f"session_{user_id}",
            conversation_id=request.conversation_id,
            model_name=request.model_name,
            provider_id=request.provider_id,
        )
        
        # 提取响应数据
        answer = result.get("answer", "")
        metadata = result.get("metadata")
        
        # 确保answer不为空
        if not answer:
            answer = "抱歉，暂时无法生成总结内容。"
        
        # 返回标准化的响应（使用ResponseWrapper以匹配前端期望的格式）
        return R.success(data=MultiVideoResponse(
            success=True,
            answer=answer,
            metadata=metadata
        ))
        
    except ValueError as e:
        return R.error(code=400, msg=f"输入验证失败: {str(e)}")
    except Exception as e:
        error_detail = str(e)
        logger.error(f"Error in example_video_endpoint: {error_detail}")
        traceback.print_exc()
        return R.error(code=500, msg=f"处理失败: {error_detail}")


@app.get("/health")
async def health_check():
    """
    健康检查接口
    用于Go后端检查Python AI服务是否可用
    """
    return {
        "status": "healthy",
        "service": "python-ai",
        "version": "1.0.0"
    }









if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8483))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=False)