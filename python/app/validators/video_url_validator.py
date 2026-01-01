import re
from urllib.parse import urlparse

# Bilibili 视频 URL 正则表达式
BILIBILI_VIDEO_PATTERN = r"(https?://)?(www\.)?bilibili\.com/video/[a-zA-Z0-9]+"


def is_supported_video_url(url: str) -> bool:
    """
    检查 URL 是否为支持的视频平台链接
    目前只支持 Bilibili
    
    Args:
        url: 视频 URL
        
    Returns:
        bool: 如果 URL 是支持的平台链接则返回 True，否则返回 False
    """
    parsed = urlparse(url)

    # 检查是否为 Bilibili 的短链接
    if parsed.netloc == "b23.tv":
        return True

    # 检查是否为 Bilibili 视频链接
    if re.match(BILIBILI_VIDEO_PATTERN, url):
        return True

    return False
