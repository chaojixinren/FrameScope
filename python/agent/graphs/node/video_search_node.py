"""
视频搜索节点
根据用户问题在 Bilibili 上搜索高质量评测视频，并返回视频 URL 列表
"""

from graphs.state import AIState
from tools.video_tools import expand_search_query, search_and_filter_videos


def video_search_node(state: AIState) -> AIState:
    """
    视频搜索节点
    
    功能：
    1. 接收用户问题（如 "索尼 A7M4 怎么样"）
    2. 扩展查询关键词（添加 "评测"、"实拍"、"选购" 等）
    3. 调用 Bilibili API 搜索视频
    4. 计算热度得分并筛选前 5 个高质量视频
    5. 过滤营销关键词视频
    6. 返回视频 URL 列表供下游节点使用
    
    Args:
        state: AIState，包含 question 字段
        
    Returns:
        AIState: 更新后的状态，包含 video_urls 和 search_query 字段
    """
    question = state.get("question", "")
    
    if not question:
        print("[Video Search Node] 未提供问题，返回空结果")
        state["video_urls"] = []
        state["search_query"] = None
        return state
    
    print(f"[Video Search Node] 开始搜索视频，问题: {question}")
    
    # 扩展搜索查询
    expanded_query = expand_search_query(question)
    print(f"[Video Search Node] 扩展后的查询: {expanded_query}")
    
    # 搜索并筛选视频（使用 video_tools 中的工具函数）
    # 限制视频时长在30分钟以内，优化下载和处理时间
    formatted_videos = search_and_filter_videos(
        query=expanded_query,
        max_results=5,
        page=1,
        page_size=50,
        max_duration_seconds=1400 
    )
    
    if not formatted_videos:
        print("[Video Search Node] 未找到符合条件的视频")
        state["video_urls"] = []
        state["search_query"] = expanded_query
        return state
    
    print(f"[Video Search Node] 筛选出前 {len(formatted_videos)} 个高质量视频:")
    for i, video in enumerate(formatted_videos, 1):
        print(f"  {i}. {video['title']} (得分: {video['popularity_score']:.4f})")
        print(f"     URL: {video['url']}")
    
    # 更新状态
    state["video_urls"] = formatted_videos
    state["search_query"] = expanded_query
    
    return state

