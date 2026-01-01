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
    1. 获取第一个启用的提供商
    2. 获取数据库中的第一个模型名称
    3. 返回 (model_name, provider_id)
    
    注意：由于 Provider.id (str) 和 Model.provider_id (int) 类型不匹配，
    此函数返回的配置可能不是精确匹配的。建议在使用时明确指定 model_name 和 provider_id。
    
    Returns:
        Tuple[str, str]: (model_name, provider_id) 元组
        
    Raises:
        ValueError: 如果数据库中没有可用的提供商或模型
    """
    try:
        from app.db.engine import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        try:
            # 1. 获取第一个启用的提供商
            from app.db.provider_dao import get_enabled_providers
            enabled_providers = get_enabled_providers()
            
            if not enabled_providers or len(enabled_providers) == 0:
                raise ValueError(
                    "数据库中没有启用的提供商，请先配置至少一个提供商。"
                    "或者在请求中明确指定 provider_id 和 model_name。"
                )
            
            provider_id = enabled_providers[0].id  # Provider.id 是 str 类型
            
            # 2. 获取数据库中的第一个模型名称
            model_result = db.execute(
                text("SELECT model_name FROM models ORDER BY id LIMIT 1")
            ).first()
            
            if not model_result:
                raise ValueError(
                    "数据库中没有可用的模型，请先添加至少一个模型。"
                    "或者在请求中明确指定 provider_id 和 model_name。"
                )
            
            model_name = model_result[0]
            
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

