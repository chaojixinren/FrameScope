"""
视频搜索节点
根据用户问题在 Bilibili 上搜索高质量评测视频，并返回视频 URL 列表
支持用户提供URL的优先级处理
"""

from graphs.state import AIState
from tools.video_tools import expand_search_query, search_and_filter_videos
from app.utils.url_parser import extract_video_id


def format_user_provided_url(url: str) -> dict:
    """
    将用户提供的URL格式化为视频信息字典
    
    Args:
        url: 用户提供的视频URL
        
    Returns:
        dict: 格式化的视频信息，包含url, platform, title, popularity_score等字段
    """
    # 从URL中提取平台信息
    platform = "bilibili"  # 目前主要支持bilibili
    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"
    elif "douyin.com" in url:
        platform = "douyin"
    
    # 尝试从URL中提取视频ID
    video_id = extract_video_id(url, platform)
    
    # 使用URL作为标题的占位符（后续可以从API获取真实标题）
    title = url
    
    return {
        "url": url,
        "platform": platform,
        "title": title,
        "popularity_score": 1.0,  # 用户提供的URL给予最高优先级得分
    }


def video_search_node(state: AIState) -> AIState:
    """
    视频搜索节点
    
    功能：
    1. 如果用户提供了URL，优先使用这些URL
    2. 如果需要的视频数量大于用户提供的URL数量，再进行搜索补充
    3. 如果需要的视频数量少于用户提供的URL数量，则选择前n个
    4. 如果没有提供URL，则正常搜索
    
    Args:
        state: AIState，包含 question 字段，可选的 user_provided_urls 字段
        
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
    
    # 获取最大视频数量（从state中获取，如果没有则使用默认值5）
    max_videos = state.get("max_videos", 5)
    print(f"[Video Search Node] 从state获取的max_videos: {max_videos}")
    # 确保max_videos在合理范围内（1-20）
    max_videos = max(1, min(20, max_videos))
    print(f"[Video Search Node] 最终需要的视频数量: {max_videos}")
    
    # 检查是否有用户提供的URL
    user_provided_urls = state.get("user_provided_urls")
    formatted_videos = []
    
    if user_provided_urls and len(user_provided_urls) > 0:
        print(f"[Video Search Node] 检测到用户提供了 {len(user_provided_urls)} 个URL")
        
        # 格式化用户提供的URL
        user_videos = [format_user_provided_url(url) for url in user_provided_urls]
        
        if len(user_videos) >= max_videos:
            # 如果用户提供的URL数量大于等于需要的数量，只取前n个
            formatted_videos = user_videos[:max_videos]
            print(f"[Video Search Node] 用户提供的URL数量({len(user_videos)}) >= 需要的数量({max_videos})，使用前{max_videos}个URL")
        else:
            # 如果用户提供的URL数量少于需要的数量，先使用所有用户提供的URL，然后搜索补充
            formatted_videos = user_videos
            needed_count = max_videos - len(user_videos)
            print(f"[Video Search Node] 用户提供的URL数量({len(user_videos)}) < 需要的数量({max_videos})，需要搜索补充{needed_count}个视频")
            
            # 扩展搜索查询
            expanded_query = expand_search_query(question)
            print(f"[Video Search Node] 扩展后的查询: {expanded_query}")
            
            # 搜索补充视频
            search_results = search_and_filter_videos(
                query=expanded_query,
                max_results=needed_count,
                page=1,
                page_size=50,
                max_duration_seconds=1400 
            )
            
            if search_results:
                # 过滤掉与用户提供的URL重复的视频
                user_urls_set = set(user_provided_urls)
                filtered_search_results = [
                    video for video in search_results 
                    if video.get("url") not in user_urls_set
                ]
                
                # 如果过滤后还有结果，添加到列表中
                if filtered_search_results:
                    formatted_videos.extend(filtered_search_results[:needed_count])
                    print(f"[Video Search Node] 搜索补充了 {len(filtered_search_results[:needed_count])} 个视频")
                else:
                    print("[Video Search Node] 搜索结果与用户提供的URL重复，未添加新视频")
            else:
                print("[Video Search Node] 未找到符合条件的补充视频")
            
            state["search_query"] = expanded_query
    else:
        # 没有用户提供的URL，正常搜索
        print("[Video Search Node] 未检测到用户提供的URL，执行正常搜索")
        
        # 扩展搜索查询
        expanded_query = expand_search_query(question)
        print(f"[Video Search Node] 扩展后的查询: {expanded_query}")
        
        # 搜索并筛选视频（使用 video_tools 中的工具函数）
        # 限制视频时长在30分钟以内，优化下载和处理时间
        formatted_videos = search_and_filter_videos(
            query=expanded_query,
            max_results=max_videos,
            page=1,
            page_size=50,
            max_duration_seconds=1400 
        )
        
        state["search_query"] = expanded_query
    
    if not formatted_videos:
        print("[Video Search Node] 未找到符合条件的视频")
        state["video_urls"] = []
        if "search_query" not in state:
            state["search_query"] = None
        return state
    
    print(f"[Video Search Node] 最终筛选出 {len(formatted_videos)} 个视频:")
    for i, video in enumerate(formatted_videos, 1):
        print(f"  {i}. {video.get('title', video.get('url', '未知标题'))}")
        print(f"     URL: {video['url']}")
        if 'popularity_score' in video:
            print(f"     热度得分: {video['popularity_score']:.4f}")
    
    # 更新状态
    state["video_urls"] = formatted_videos
    if "search_query" not in state:
        state["search_query"] = None
    
    return state

