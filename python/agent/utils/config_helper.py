"""
配置辅助模块
用于从 state 中获取模型配置或使用默认配置
"""

import sys
from pathlib import Path
from typing import Tuple, Optional

from graphs.state import AIState

# 添加 backend/app 到路径，以便导入 app 的服务
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

try:
    from app.services.provider import ProviderService
    from app.services.model import ModelService
except ImportError as e:
    raise ImportError(f"无法导入 app 服务: {e}")


def get_default_model_config() -> Tuple[str, str]:
    """
    从数据库获取默认的模型配置
    
    策略：
    1. 优先选择 qwen 提供商（如果存在且启用）
    2. 否则选择第一个启用的提供商
    3. 根据模型名称匹配对应的提供商（如 qwen-max 匹配 qwen）
    4. 如果找不到匹配的模型，使用该提供商的第一个模型
    
    Returns:
        Tuple[str, str]: (model_name, provider_id) 元组
        
    Raises:
        ValueError: 如果数据库中没有可用的提供商或模型
    """
    try:
        from app.db.engine import get_db
        from sqlalchemy import text
        from app.db.provider_dao import get_enabled_providers
        
        db = next(get_db())
        try:
            # 1. 获取所有启用的提供商
            enabled_providers = get_enabled_providers()
            
            if not enabled_providers or len(enabled_providers) == 0:
                raise ValueError(
                    "数据库中没有启用的提供商，请先配置至少一个提供商。"
                    "或者在请求中明确指定 provider_id 和 model_name。"
                )
            
            # 2. 优先选择 qwen 提供商
            provider = None
            for p in enabled_providers:
                if p.id.lower() == "qwen":
                    provider = p
                    break
            
            # 如果没有 qwen，选择第一个启用的提供商
            if not provider:
                provider = enabled_providers[0]
            
            provider_id = provider.id  # Provider.id 是 str 类型
            provider_name_lower = provider.name.lower() if provider.name else ""
            
            # 3. 获取所有模型（Model 表没有 enabled 列，所以获取所有模型）
            all_models = db.execute(
                text("SELECT id, model_name, provider_id FROM models ORDER BY id")
            ).fetchall()
            
            if not all_models:
                raise ValueError(
                    "数据库中没有启用的模型，请先添加至少一个模型。"
                    "或者在请求中明确指定 provider_id 和 model_name。"
                )
            
            # 4. 优先选择模型名称包含提供商名称的模型（如 qwen-max 包含 qwen）
            model_name = None
            for model_row in all_models:
                model_name_candidate = model_row[1]
                # 检查模型名称是否包含提供商名称
                if provider_name_lower and provider_name_lower in model_name_candidate.lower():
                    model_name = model_name_candidate
                    break
            
            # 如果没有匹配的，使用第一个模型
            if not model_name:
                model_name = all_models[0][1]
            
            return (model_name, provider_id)
            
        finally:
            db.close()
            
    except ValueError:
        # ValueError 直接抛出
        raise
    except Exception as e:
        # 其他异常，包装成 ValueError
        raise ValueError(f"从数据库获取默认配置失败: {str(e)}")


def get_model_config_from_state(state: AIState) -> Tuple[str, str]:
    """
    从 state 中获取模型配置，如果 state 中没有，则使用默认配置
    
    Args:
        state: AIState 状态字典
        
    Returns:
        Tuple[str, str]: (model_name, provider_id) 元组
        
    Raises:
        ValueError: 如果无法获取有效的配置
    """
    # 从 state 中获取配置
    model_name = state.get("model_name")
    provider_id = state.get("provider_id")
    
    # 如果 state 中没有配置，使用默认配置
    if not model_name or not provider_id:
        default_model_name, default_provider_id = get_default_model_config()
        model_name = model_name or default_model_name
        provider_id = provider_id or default_provider_id
    
    # 确保配置不为空
    if not model_name or not provider_id:
        raise ValueError(
            "模型配置缺失：请在请求中提供 model_name 和 provider_id，"
            "或确保数据库中有默认配置"
        )
    
    return (model_name, provider_id)

