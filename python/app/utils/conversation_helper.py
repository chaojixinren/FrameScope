from typing import Optional
from app.models.model_config import ModelConfig
from app.services.provider import ProviderService
from app.gpt.gpt_factory import GPTFactory
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_conversation_title(
    question: str,
    answer: str,
    model_name: Optional[str] = None,
    provider_id: Optional[str] = None
) -> str:
    """
    使用LLM生成对话标题（10-20字）
    
    Args:
        question: 用户问题
        answer: 助手回答（只使用前200字符）
        model_name: 模型名称（可选）
        provider_id: 提供商ID（可选）
        
    Returns:
        str: 生成的标题（如果生成失败，返回默认标题）
    """
    try:
        # 限制回答长度，避免输入过长
        answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
        
        # 构建提示词
        prompt = f"""请为以下对话生成一个10-20字的简短标题。只返回标题，不要其他内容。

问题：{question}

回答：{answer_preview}

标题："""
        
        # 获取模型配置
        providers = ProviderService.get_all_providers_safe()
        provider = None
        
        if model_name and provider_id:
            provider = next((p for p in providers if p.get("id") == provider_id), None)
        
        # 如果找不到指定的provider，使用第一个enabled的provider
        if not provider:
            enabled_providers = [p for p in providers if p.get("enabled", 1) == 1]
            if enabled_providers:
                provider = enabled_providers[0]
                model_name = model_name or "gpt-3.5-turbo"  # 默认模型
            else:
                logger.warning("没有可用的provider，使用默认标题")
                return question[:20] + "..." if len(question) > 20 else question
        
        # 构建ModelConfig
        config = ModelConfig(
            api_key=provider.get("api_key"),
            base_url=provider.get("base_url"),
            model_name=model_name or provider.get("name", "gpt-3.5-turbo"),
            provider=provider.get("type"),
            name=provider.get("name")
        )
        
        # 获取GPT实例
        gpt = GPTFactory.from_config(config)
        
        # 直接使用client发送请求
        messages = [{"role": "user", "content": prompt}]
        response = gpt.client.chat.completions.create(
            model=gpt.model,
            messages=messages,
            temperature=0.7,
            max_tokens=50  # 标题不需要太多token
        )
        
        title = response.choices[0].message.content.strip()
        # 移除可能的markdown格式
        title = title.lstrip('#').strip()
        # 移除引号
        title = title.strip('"').strip("'")
        # 限制长度
        if len(title) > 30:
            title = title[:30] + "..."
        
        return title if title else "新对话"
            
    except Exception as e:
        logger.error(f"生成对话标题失败: {e}")
        # 如果生成失败，使用问题的前20字作为标题
        if question:
            title = question[:20] + "..." if len(question) > 20 else question
            return title
        return "新对话"

