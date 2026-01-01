"""
视频搜索相关工具函数
提供 Bilibili 视频搜索、热度计算、过滤等通用功能
使用 bilibili-api 库进行搜索
"""

import re
import random
import asyncio
import time
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from bilibili_api import misc
    BILIBILI_API_AVAILABLE = True
except ImportError:
    BILIBILI_API_AVAILABLE = False
    print("[Video Tools] 警告: bilibili-api 库未安装，将使用备用方案（直接调用 API）")


# User-Agent 列表，用于随机化请求头
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# 全局 Session 对象，用于保持连接和 Cookie
_session = None
_last_request_time = 0
_min_request_interval = 1.0  # 最小请求间隔（秒）

# 需要过滤的营销关键词
MARKETING_KEYWORDS = [
    "拼多多", "抽奖", "纯搬运", "广告", "推广", "带货", 
    "优惠券", "限时", "秒杀", "特价", "折扣", "返利"
]


def expand_search_query(query: str) -> str:
    """
    扩展搜索查询，添加更具搜索价值的关键词
    
    Args:
        query: 原始查询（如 "索尼 A7M4 怎么样"）
        
    Returns:
        str: 扩展后的查询（如 "索尼 A7M4 评测"）
    """
    # 移除常见的疑问词
    query = re.sub(r"(怎么样|如何|好不好|值得买吗|推荐)", "", query).strip()
    
    # 添加搜索关键词
    search_keywords = ["评测", "实拍", "选购", "推荐", "对比"]
    
    # 如果查询中已经包含这些关键词，就不重复添加
    expanded_query = query
    for keyword in search_keywords:
        if keyword not in query:
            expanded_query = f"{expanded_query} {keyword}"
            break  # 只添加一个关键词，避免查询过长
    
    return expanded_query.strip()


async def search_bilibili_api_async(
    query: str, 
    page: int = 1, 
    page_size: int = 20
) -> Optional[Dict[str, Any]]:
    """
    使用 bilibili-api 库异步搜索视频
    
    Args:
        query: 搜索关键词
        page: 页码（从1开始）
        page_size: 每页结果数（最大50）
        
    Returns:
        Optional[Dict]: API 返回的数据，如果失败返回 None
    """
    if not BILIBILI_API_AVAILABLE:
        print("[Video Tools] bilibili-api 库未安装，无法使用")
        return None
    
    try:
        # 使用 bilibili-api 库进行搜索（新版本使用 misc.web_search_by_type）
        result = await misc.web_search_by_type(
            keyword=query,
            search_type="video"  # 搜索类型：视频
        )
        
        # bilibili-api 返回的数据格式可能不同，需要适配
        # 检查返回结果的结构
        if result:
            # 如果 result 是字典且包含 'result' 键
            if isinstance(result, dict) and "result" in result:
                # 包装成与原来 API 格式兼容的结构
                return {
                    "code": 0,
                    "data": {
                        "result": result.get("result", [])
                    }
                }
            # 如果 result 直接是列表
            elif isinstance(result, list):
                return {
                    "code": 0,
                    "data": {
                        "result": result
                    }
                }
            # 其他情况，尝试直接使用
            else:
                return {
                    "code": 0,
                    "data": {
                        "result": result if isinstance(result, list) else []
                    }
                }
        else:
            print(f"[Video Tools] 搜索返回空结果: {query}")
            return None
            
    except Exception as e:
        print(f"[Video Tools] 搜索时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def _get_session() -> requests.Session:
    """
    获取全局 Session 对象，配置重试策略和连接池
    
    Returns:
        requests.Session: 配置好的 Session 对象
    """
    global _session
    
    if _session is None:
        _session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 重试间隔：1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504, 412],  # 对这些状态码重试
            allowed_methods=["GET"]  # 只对 GET 请求重试
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    
    return _session


def _get_enhanced_headers() -> Dict[str, str]:
    """
    生成增强的请求头，模拟真实浏览器
    
    Returns:
        Dict[str, str]: 完整的请求头字典
    """
    user_agent = random.choice(USER_AGENTS)
    
    # 根据 User-Agent 选择对应的 Sec-Fetch-* 头
    if "Chrome" in user_agent:
        sec_fetch_site = "none"
        sec_fetch_mode = "cors"
        sec_fetch_dest = "empty"
    else:
        sec_fetch_site = None
        sec_fetch_mode = None
        sec_fetch_dest = None
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    
    # 添加 Chrome 特有的 Sec-Fetch-* 头
    if sec_fetch_site:
        headers.update({
            "Sec-Fetch-Site": sec_fetch_site,
            "Sec-Fetch-Mode": sec_fetch_mode,
            "Sec-Fetch-Dest": sec_fetch_dest,
        })
    
    return headers


def _rate_limit():
    """
    请求频率限制：确保两次请求之间有足够的间隔
    """
    global _last_request_time
    
    current_time = time.time()
    elapsed = current_time - _last_request_time
    
    if elapsed < _min_request_interval:
        # 添加随机延迟，模拟人类行为
        sleep_time = _min_request_interval - elapsed + random.uniform(0.5, 1.5)
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def search_bilibili_api_direct(query: str, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
    """
    备用方案：直接调用 Bilibili 搜索 API（当 bilibili-api 库未安装时使用）
    包含反爬虫策略：请求头伪装、频率限制、重试机制
    
    Args:
        query: 搜索关键词
        page: 页码（从1开始）
        page_size: 每页结果数（最大50）
        
    Returns:
        Optional[Dict]: API 返回的 JSON 数据，如果失败返回 None
    """
    # 请求频率限制
    _rate_limit()
    
    url = "https://api.bilibili.com/x/web-interface/search/type"
    
    params = {
        "search_type": "video",  # 搜索类型：视频
        "keyword": query,
        "page": page,
        "pagesize": page_size,
        "order": "totalrank",  # 排序方式：综合排序（totalrank）
    }
    
    # 使用增强的请求头
    headers = _get_enhanced_headers()
    
    # 使用 Session 保持连接
    session = _get_session()
    
    try:
        response = session.get(url, params=params, headers=headers, timeout=15)
        
        # 处理 412 错误（Precondition Failed）
        if response.status_code == 412:
            print(f"[Video Tools] 遇到 412 错误，可能是反爬虫限制，等待后重试...")
            time.sleep(random.uniform(2, 5))  # 等待 2-5 秒
            # 更换 User-Agent 重试一次
            headers = _get_enhanced_headers()
            response = session.get(url, params=params, headers=headers, timeout=15)
        
        response.raise_for_status()
        
        data = response.json()
        
        # 检查 API 返回状态
        if data.get("code") != 0:
            error_msg = data.get("message", "未知错误")
            print(f"[Video Tools] Bilibili API 返回错误: {error_msg}")
            return None
        
        return data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 412:
            print(f"[Video Tools] 412 错误：反爬虫限制，建议降低请求频率或使用代理")
        else:
            print(f"[Video Tools] HTTP 错误 {e.response.status_code}: {str(e)}")
        return None
    except requests.exceptions.Timeout:
        print(f"[Video Tools] 请求超时: {query}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Video Tools] 网络请求失败: {str(e)}")
        return None
    except Exception as e:
        print(f"[Video Tools] 搜索时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def search_bilibili_api(query: str, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
    """
    同步包装器：调用 Bilibili 搜索 API 搜索视频
    优先使用 bilibili-api 库，如果未安装则使用直接调用 API 的备用方案
    
    Args:
        query: 搜索关键词
        page: 页码（从1开始）
        page_size: 每页结果数（最大50）
        
    Returns:
        Optional[Dict]: API 返回的 JSON 数据，如果失败返回 None
    """
    if not BILIBILI_API_AVAILABLE:
        # 使用备用方案：直接调用 API
        return search_bilibili_api_direct(query, page, page_size)
    
    try:
        # 使用 asyncio.run 运行异步函数
        # 如果已经在事件循环中，使用不同的方法
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用 nest_asyncio
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    return loop.run_until_complete(
                        search_bilibili_api_async(query, page, page_size)
                    )
                except ImportError:
                    # 如果 nest_asyncio 未安装，创建一个新的事件循环
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            search_bilibili_api_async(query, page, page_size)
                        )
                        return future.result()
        except RuntimeError:
            # 没有事件循环，直接使用 asyncio.run
            pass
        
        # 如果没有运行的事件循环，使用 asyncio.run
        return asyncio.run(search_bilibili_api_async(query, page, page_size))
        
    except Exception as e:
        print(f"[Video Tools] 同步调用异步函数时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def calculate_popularity_score(view: int, like: int) -> float:
    """
    计算视频热度得分
    
    公式: Score = view * 0.2 + like * 0.8（归一化后）
    
    Args:
        view: 播放量
        like: 点赞数
        
    Returns:
        float: 热度得分（0-1之间）
    """
    # 归一化处理：将数值转换为更合理的范围
    # 假设播放量在 0-1000万，点赞数在 0-100万
    normalized_view = min(view / 10000000, 1.0)  # 归一化到 0-1
    normalized_like = min(like / 1000000, 1.0)  # 归一化到 0-1
    
    score = normalized_view * 0.2 + normalized_like * 0.8
    return score


def filter_marketing_videos(title: str) -> bool:
    """
    过滤包含营销关键词的视频
    
    Args:
        title: 视频标题
        
    Returns:
        bool: True 表示应该保留，False 表示应该过滤掉
    """
    for keyword in MARKETING_KEYWORDS:
        if keyword in title:
            return False
    return True


def parse_bilibili_search_results(data: Dict[str, Any], max_duration_seconds: int = 1800) -> List[Dict[str, Any]]:
    """
    解析 Bilibili 搜索 API 返回的数据
    
    Args:
        data: API 返回的 JSON 数据
        max_duration_seconds: 最大视频时长（秒），默认1800秒（30分钟）
        
    Returns:
        List[Dict]: 视频信息列表，每个包含 url, title, view, like, score 等
    """
    videos = []
    
    result = data.get("data", {})
    video_list = result.get("result", [])
    
    for item in video_list:
        # 提取视频信息
        bvid = item.get("bvid", "")  # BV号
        title = item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", "")
        description = item.get("description", "")
        
        # 提取视频时长（Bilibili API 可能返回 "MM:SS" 格式或秒数）
        duration_str = item.get("duration", "")  # 可能是 "10:30" 或 "630" 格式
        
        # 将时长转换为秒数
        duration_seconds = 0
        if duration_str:
            try:
                # 如果是 "MM:SS" 格式
                if ":" in str(duration_str):
                    parts = str(duration_str).split(":")
                    if len(parts) == 2:
                        duration_seconds = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:  # "HH:MM:SS" 格式
                        duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    # 如果已经是秒数
                    duration_seconds = int(duration_str)
            except (ValueError, AttributeError):
                # 如果解析失败，跳过时长检查（保留该视频）
                duration_seconds = 0
        
        # 过滤超过最大时长的视频（如果时长信息可用）
        if duration_seconds > 0 and duration_seconds > max_duration_seconds:
            continue
        
        # 提取统计数据
        view = item.get("play", 0)  # 播放量
        like = item.get("like", 0)  # 点赞数
        danmaku = item.get("video_review", 0)  # 弹幕数
        favorite = item.get("favorites", 0)  # 收藏数
        
        # 过滤营销视频
        if not filter_marketing_videos(title):
            continue
        
        # 构建视频 URL
        if bvid:
            video_url = f"https://www.bilibili.com/video/{bvid}"
        else:
            continue  # 如果没有 BV 号，跳过
        
        # 计算热度得分
        score = calculate_popularity_score(view, like)
        
        videos.append({
            "url": video_url,
            "platform": "bilibili",
            "title": title,
            "description": description,
            "bvid": bvid,
            "view": view,
            "like": like,
            "danmaku": danmaku,
            "favorite": favorite,
            "popularity_score": score,
            "duration": duration_seconds,  # 添加时长信息
        })
    
    return videos


def search_and_filter_videos(
    query: str, 
    max_results: int = 5,
    page: int = 1,
    page_size: int = 50,
    max_duration_seconds: int = 1800  # 最大视频时长（秒），默认30分钟
) -> List[Dict[str, Any]]:
    """
    搜索并筛选 Bilibili 视频的完整流程
    
    Args:
        query: 搜索关键词
        max_results: 最大返回结果数（默认5）
        page: 页码（从1开始）
        page_size: 每页结果数（最大50）
        max_duration_seconds: 最大视频时长（秒），默认1800秒（30分钟）
        
    Returns:
        List[Dict]: 筛选后的视频列表，按热度得分排序
    """
    # 调用 API 搜索
    search_data = search_bilibili_api(query, page=page, page_size=page_size)
    
    if not search_data:
        return []
    
    # 解析搜索结果（传入最大时长限制）
    all_videos = parse_bilibili_search_results(search_data, max_duration_seconds=max_duration_seconds)
    
    if not all_videos:
        return []
    
    # 按热度得分排序，取前 max_results 个
    sorted_videos = sorted(all_videos, key=lambda x: x["popularity_score"], reverse=True)
    top_videos = sorted_videos[:max_results]
    
    # 格式化输出（仅保留必要的字段）
    formatted_videos = []
    for video in top_videos:
        formatted_videos.append({
            "url": video["url"],
            "platform": video["platform"],
            "title": video["title"],
            "description": video.get("description", ""),
            "popularity_score": video["popularity_score"],
        })
    
    return formatted_videos

