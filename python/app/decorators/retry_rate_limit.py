import functools
import re
import time
import logging
from typing import Callable, Any
from openai import RateLimitError

logger = logging.getLogger(__name__)


def parse_retry_after(error_message: str) -> int:
    """
    从错误信息中解析需要等待的秒数
    
    例如: "Please try again in 7m34s" -> 454 (秒)
          "Please try again in 5m35s" -> 335 (秒)
    """
    # 匹配 "Please try again in XmYs" 或 "Please try again in Xs" 或 "Please try again in Xm"
    # 支持多种格式：7m34s, 5m35s, 34s, 7m
    pattern = r'Please try again in\s+((\d+)m)?\s*((\d+)s)?'
    match = re.search(pattern, error_message, re.IGNORECASE)
    
    if match:
        minutes_str = match.group(2)  # 分钟数（如果有）
        seconds_str = match.group(4)  # 秒数（如果有）
        
        minutes = int(minutes_str) if minutes_str else 0
        seconds = int(seconds_str) if seconds_str else 0
        total_seconds = minutes * 60 + seconds
        
        if total_seconds > 0:
            return total_seconds
    
    # 如果没有匹配到，返回默认值（5分钟）
    logger.warning(f"无法从错误信息中解析等待时间，使用默认值: {error_message[:200]}")
    return 300  # 默认等待 5 分钟


def retry_on_rate_limit(max_retries: int = 3, base_delay: int = 60):
    """
    重试装饰器，专门处理 RateLimitError
    
    :param max_retries: 最大重试次数
    :param base_delay: 基础延迟时间（秒），当无法解析等待时间时使用
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    last_exception = e
                    error_message = str(e)
                    
                    # 解析需要等待的时间
                    wait_time = parse_retry_after(error_message)
                    
                    if attempt < max_retries - 1:
                        wait_minutes = wait_time // 60
                        wait_seconds = wait_time % 60
                        logger.warning(
                            f"[重试 {attempt + 1}/{max_retries}] 遇到速率限制错误，"
                            f"等待 {wait_minutes}分{wait_seconds}秒 ({wait_time}秒) 后重试..."
                        )
                        # 添加一些缓冲时间（额外等待 10 秒，确保速率限制已重置）
                        time.sleep(wait_time + 10)
                    else:
                        logger.error(
                            f"[重试失败] 已达到最大重试次数 ({max_retries})，"
                            f"最后一次错误: {error_message[:500]}"
                        )
                except Exception as e:
                    # 其他类型的异常直接抛出，不重试
                    raise
            
            # 如果所有重试都失败了，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator

