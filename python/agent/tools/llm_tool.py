"""
LLM 工具模块
使用 app 的逻辑从数据库获取 LLM 客户端实例
"""

import sys
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI

# 添加 backend/app 到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

try:
    from app.services.provider import ProviderService
    from app.models.model_config import ModelConfig
except ImportError as e:
    raise ImportError(f"无法导入 app 服务: {e}")


def get_llm_client(model_name: Optional[str] = None, provider_id: Optional[str] = None) -> ChatOpenAI:
    """
    根据 model_name 和 provider_id 获取 LLM 客户端实例
    使用 app 的逻辑从数据库获取配置（与 note.py 的 _get_gpt 方法逻辑一致）
    
    Args:
        model_name: 模型名称（可选，如果不提供则使用默认）
        provider_id: 提供商 ID（可选，如果不提供则使用默认）
    
    Returns:
        ChatOpenAI: LangChain 的 ChatOpenAI 客户端
        
    Raises:
        ValueError: 如果 API Key 未配置或配置无效
        Exception: 如果无法获取提供商或模型配置
    """
    # 如果没有提供 model_name 或 provider_id，使用默认配置
    if not model_name or not provider_id:
        from utils.config_helper import get_default_model_config
        default_model_name, default_provider_id = get_default_model_config()
        model_name = model_name or default_model_name
        provider_id = provider_id or default_provider_id
    
    # 使用 app 的逻辑获取提供商配置（和 note.py 的 _get_gpt 方法一致）
    provider = ProviderService.get_provider_by_id(provider_id)
    if not provider:
        raise Exception(f"未找到提供商: provider_id={provider_id}")
    
    # 创建 ModelConfig（使用和 note.py 的 _get_gpt 方法相同的逻辑）
    config = ModelConfig(
        api_key=provider["api_key"],
        base_url=provider["base_url"],
        model_name=model_name,
        provider=provider["type"],
        name=provider["name"],
    )
    
    # 验证 API Key
    if not config.api_key or config.api_key.strip() == "":
        raise ValueError(
            f"提供商 {provider.get('name', provider_id)} 的 API Key 未配置！\n"
            f"请先在系统中配置该提供商的 API Key"
        )
    
    # 检查 API Key 是否看起来有效（不是占位符）
    if config.api_key.lower() in ['your_api_key_here', 'your_deepseek_api_key_here', 
                           'your_qwen_api_key_here', 'your_openai_api_key_here', '']:
        raise ValueError(
            f"提供商 {provider.get('name', provider_id)} 的 API Key 似乎是占位符，请替换为真实的 API Key！\n"
            f"当前值: {config.api_key[:10]}..."
        )
    
    # 从 ModelConfig 创建 ChatOpenAI 客户端（LangGraph 需要）
    # 注意：这里使用的是 ModelConfig 中的配置，与 note.py 中创建 GPT 实例使用的配置完全一致
    # timeout 设置为 180 秒，因为总结多个视频笔记时，输入内容较长，可能需要更长的处理时间
    client = ChatOpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model_name,
        temperature=0.7,  # 默认温度，可以根据需要调整
        timeout=180.0,  # 超时时间设置为 180 秒（3分钟），适用于处理长文本总结
    )
    
    return client
