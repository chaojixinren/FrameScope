"""
转录器提供者/工厂模块
管理不同类型的转录器实例，提供统一的获取接口
目前只支持 Groq 转录器
"""

from enum import Enum

from app.transcriber.groq import GroqTranscriber
from app.transcriber.base import Transcriber
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TranscriberType(str, Enum):
    """转录器类型枚举"""
    GROQ = "groq"

logger.info('初始化转录服务提供器')

# 转录器单例缓存
_transcribers = {
    TranscriberType.GROQ: None,
}

# 公共实例初始化函数
def _init_transcriber(key: TranscriberType, cls, *args, **kwargs):
    """初始化转录器实例（单例模式）"""
    if _transcribers[key] is None:
        logger.info(f'创建 {cls.__name__} 实例: {key}')
        try:
            _transcribers[key] = cls(*args, **kwargs)
            logger.info(f'{cls.__name__} 创建成功')
        except Exception as e:
            logger.error(f"{cls.__name__} 创建失败: {e}")
            raise
    return _transcribers[key]

# 各类型获取方法
def get_groq_transcriber():
    """获取 Groq 转录器实例"""
    return _init_transcriber(TranscriberType.GROQ, GroqTranscriber)

# 通用入口
def get_transcriber(transcriber_type: str = "groq") -> Transcriber:
    """
    获取指定类型的转录器实例
    
    参数:
        transcriber_type: 转录器类型，目前只支持 "groq"
    
    返回:
        对应类型的转录器实例
    """
    logger.info(f'请求转录器类型: {transcriber_type}')
    
    # 统一转换为小写
    transcriber_type = transcriber_type.lower()
    
    # 如果请求的是 groq 或未知类型，都使用 Groq
    if transcriber_type == "groq" or transcriber_type not in [t.value for t in TranscriberType]:
        if transcriber_type != "groq":
            logger.warning(f'未知转录器类型 "{transcriber_type}"，使用 Groq 作为默认')
        return get_groq_transcriber()
    
    # 理论上不会到达这里，但为了完整性保留
    logger.warning(f'未识别转录器类型 "{transcriber_type}"，使用 Groq 作为默认')
    return get_groq_transcriber()
