from typing import Optional
from app.models.model_config import ModelConfig
from app.services.provider import ProviderService
from app.gpt.gpt_factory import GPTFactory
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_conversation_title(
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
        # 如果 model_name 或 provider_id 为 None，使用默认配置（优先 qwen）
        if not model_name or not provider_id:
            try:
                # 尝试从 agent.utils.config_helper 导入（如果可用）
                import sys
                from pathlib import Path
                # 获取当前文件的路径：python/app/utils/conversation_helper.py
                # agent 路径应该是：python/agent
                current_file = Path(__file__)  # python/app/utils/conversation_helper.py
                agent_path = current_file.parent.parent.parent / "agent"
                if str(agent_path) not in sys.path:
                    sys.path.insert(0, str(agent_path))
                
                from utils.config_helper import get_default_model_config
                default_model_name, default_provider_id = get_default_model_config()
                model_name = model_name or default_model_name
                provider_id = provider_id or default_provider_id
                logger.info(f"[generate_conversation_title] 使用默认配置: model_name={model_name}, provider_id={provider_id}")
            except Exception as e:
                logger.warning(f"[generate_conversation_title] 获取默认配置失败: {e}，将尝试使用其他方式")
        
        # 获取提供商
        providers = ProviderService.get_all_providers_safe()
        provider = None
        
        if provider_id:
            provider = next((p for p in providers if p.get("id") == provider_id), None)
        
        # 如果找不到指定的provider，优先选择 qwen，否则使用第一个enabled的provider
        if not provider:
            enabled_providers = [p for p in providers if p.get("enabled", 1) == 1]
            if enabled_providers:
                # 优先选择 qwen 提供商
                qwen_provider = next((p for p in enabled_providers if p.get("id", "").lower() == "qwen"), None)
                if qwen_provider:
                    provider = qwen_provider
                    # 如果没有指定 model_name，尝试使用 qwen 相关的模型
                    if not model_name:
                        # 尝试从数据库中获取 qwen 的模型
                        from app.db.engine import get_db
                        from sqlalchemy import text
                        db = next(get_db())
                        try:
                            qwen_models = db.execute(
                                text("SELECT model_name FROM models WHERE provider_id = :provider_id ORDER BY id LIMIT 1"),
                                {"provider_id": "qwen"}
                            ).fetchall()
                            if qwen_models:
                                model_name = qwen_models[0][0]
                            else:
                                model_name = "qwen-max"  # 默认 qwen 模型
                        except Exception as e:
                            logger.warning(f"获取 qwen 模型失败: {e}，使用默认模型")
                            model_name = "qwen-max"
                        finally:
                            db.close()
                else:
                    provider = enabled_providers[0]
                    model_name = model_name or "gpt-3.5-turbo"  # 默认模型
            else:
                logger.warning("没有可用的provider，使用默认标题")
                return question[:20] + "..." if len(question) > 20 else question
        
        # 验证 API Key
        api_key = provider.get("api_key", "")
        if not api_key or api_key.strip() == "":
            logger.warning(f"[generate_conversation_title] 提供商 {provider.get('name', provider_id)} 的 API Key 为空，使用默认标题")
            return question[:20] + "..." if len(question) > 20 else question
        
        # 检查是否是占位符
        placeholder_keys = ['your_api_key_here', 'your_deepseek_api_key_here', 
                           'your_qwen_api_key_here', 'your_openai_api_key_here']
        if api_key.lower() in placeholder_keys:
            logger.warning(f"[generate_conversation_title] 提供商 {provider.get('name', provider_id)} 的 API Key 是占位符，使用默认标题")
            return question[:20] + "..." if len(question) > 20 else question
        
        # 构建ModelConfig
        config = ModelConfig(
            api_key=api_key,
            base_url=provider.get("base_url"),
            model_name=model_name or provider.get("name", "gpt-3.5-turbo"),
            provider=provider.get("type"),
            name=provider.get("name")
        )
        
        logger.info(f"[generate_conversation_title] 使用提供商: {provider.get('name', provider_id)}, 模型: {model_name}, Base URL: {provider.get('base_url', 'N/A')}")
        
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
        logger.info(f"[generate_conversation_title] ✓ 生成的标题: {title}")
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

