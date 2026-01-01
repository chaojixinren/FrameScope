from typing import TypedDict, Optional, List, Dict, Any


class AIState(TypedDict):
    """多视频搜索和总结功能的状态定义"""
    # User input
    question: str
    
    # User information
    user_id: Optional[int]

    # Metadata
    timestamp: Optional[str]
    session_id: Optional[str]

    # Context memory
    history: List[Dict[str, Any]]  # 对话历史 [{"role": "user"/"assistant"/"system", "content": str}, ...]
    answer: Optional[str]          # 最近一次助手回复
    
    # 视频搜索相关（多视频功能）
    video_urls: Optional[List[Dict[str, Any]]]  # [{"url": "...", "platform": "...", "title": "...", "description": "...", "popularity_score": float}]
    search_query: Optional[str]  # Agent1 生成的搜索查询
    video_ids: Optional[List[str]]  # 视频ID列表（用于example视频处理）
    max_videos: Optional[int]  # 最大视频数量（可选，默认5）
    user_provided_urls: Optional[List[str]]  # 用户提供的视频URL列表（可选）
    
    # 笔记生成相关（多视频功能）
    note_results: Optional[List[Dict[str, Any]]]  # 每个视频的笔记结果
    model_name: Optional[str]  # 从配置获取
    provider_id: Optional[str]  # 从配置获取
    note_generation_status: Optional[Dict[str, str]]  # 每个任务的状态（可选）
    
    # 总结相关（多视频功能）
    summary_result: Optional[str]  # 最终总结
    
    # 证据链回溯相关
    trace_data: Optional[Dict[str, Any]]  # {时间戳键: {"video_url": str, "frame_url": str, "video_id": str, "timestamp": int, "platform": str}}
    
    # 元数据（多视频功能）
    metadata: Optional[Dict[str, Any]]  # 元数据 {"total_videos": int, "processing_time": float}

