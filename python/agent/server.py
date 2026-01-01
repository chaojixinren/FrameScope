"""
Python AI服务 - FastAPI服务器
提供HTTP接口供Go后端调用
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
import traceback
import os
import re
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
# 优先从 python/ 目录加载 .env 文件，如果不存在则从项目根目录加载
env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from graphs.agent_graph import build_multi_video_graph
from graphs.state import AIState
import uuid

# 为了向后兼容，保留 MultiVideoState 作为 AIState 的别名
MultiVideoState = AIState


app = FastAPI(
    title="Study++ Python AI Service",
    description="智能学习计划助手AI服务",
    version="1.0.0"
)

# 配置CORS
# 从环境变量读取允许的源，生产环境应设置 CORS_ALLOWED_ORIGINS
# 格式：逗号分隔的域名列表，如 "http://localhost:3000,https://example.com"
cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
if cors_origins_str:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
else:
    # 开发环境默认允许所有源（便于测试）
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class MultiVideoRequest(BaseModel):
    """多视频搜索和总结请求模型"""
    question: str = Field(..., min_length=1, max_length=5000, description="用户问题（例如：某品牌的相机怎么样）")
    user_id: int = Field(..., gt=0, le=2147483647, description="用户ID")
    session_id: Optional[str] = Field(None, max_length=255, description="会话ID")
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


async def run_multi_video_query(
    question: str,
    user_id: int,
    session_id: str = None,
    model_name: str = None,
    provider_id: str = None,
) -> MultiVideoState:
    """
    运行多视频搜索和总结查询
    
    Args:
        question: 用户问题
        user_id: 用户ID
        session_id: 会话ID（可选）
        model_name: 模型名称（可选）
        provider_id: 提供商ID（可选）
        
    Returns:
        MultiVideoState: 包含答案、笔记结果等信息的最终状态
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # Build graph
    graph = build_multi_video_graph()
    
    # Initialize state
    initial_state: MultiVideoState = {
        "question": question,
        "user_id": user_id,
        "session_id": session_id,
        "history": [],
        "timestamp": None,
        "video_urls": [],
        "search_query": None,
        "note_results": [],
        "model_name": model_name,
        "provider_id": provider_id,
        "note_generation_status": None,
        "summary_result": None,
        "answer": None,
        "metadata": None,
    }
    
    # Run graph (异步)
    print(f"\n{'='*50}")
    print(f"Starting Multi-Video Graph")
    print(f"User ID: {user_id}")
    print(f"Question: {question}")
    print(f"{'='*50}\n")
    
    result = await graph.ainvoke(initial_state)
    
    return result


@app.post("/api/multi_video", response_model=MultiVideoResponse)
async def multi_video_endpoint(request: MultiVideoRequest):
    """
    处理多视频搜索和总结请求的核心接口
    
    流程：
    1. Agent1 搜索相关视频（目前使用占位符）
    2. 并发生成每个视频的笔记
    3. Agent2 对多个笔记进行多角度总结
    
    Args:
        request: 包含 question, user_id 等的请求
        
    Returns:
        MultiVideoResponse: 包含答案和元数据的响应
    """
    try:
        # 调用多视频工作流
        result = await run_multi_video_query(
            question=request.question,
            user_id=request.user_id,
            session_id=request.session_id or f"session_{request.user_id}",
            model_name=request.model_name,
            provider_id=request.provider_id,
        )
        
        # 提取响应数据
        answer = result.get("answer", "")
        metadata = result.get("metadata")
        
        # 确保answer不为空
        if not answer:
            answer = "抱歉，暂时无法生成总结内容。"
        
        # 返回标准化的响应
        return MultiVideoResponse(
            success=True,
            answer=answer,
            metadata=metadata
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"输入验证失败: {str(e)}"
        )
    except Exception as e:
        error_detail = str(e)
        print(f"Error in multi_video_endpoint: {error_detail}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {error_detail}"
        )


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
    import uvicorn
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        log_level="info"
    )

