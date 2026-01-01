"""
普通对话节点
用于后续提问的普通LLM对话，保留之前的视频总结作为上下文
"""

from graphs.state import AIState
from tools.llm_tool import get_llm_client
from utils.config_helper import get_model_config_from_state
from prompts.chat_prompts import CHAT_SYSTEM_PROMPT_TEMPLATE
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Any

async def chat_node(state: AIState) -> AIState:
    """
    普通对话节点 - 基于历史对话和之前的视频总结进行对话
    
    Args:
        state: AIState
        
    Returns:
        AIState: 包含 answer 的状态
    """
    user_question = state.get("question", "")
    history = state.get("history", [])
    previous_summary = state.get("summary_result", "")
    
    if not user_question:
        state["answer"] = "未提供问题"
        return state
    
    print(f"[Chat Node] 开始普通对话，问题: {user_question}")
    print(f"[Chat Node] 历史消息数: {len(history)}")
    
    # 从 state 中获取模型配置
    model_name, provider_id = get_model_config_from_state(state)
    print(f"[Chat Node] 使用模型: {model_name}, 提供商: {provider_id}")
    
    # 获取 LLM 客户端
    llm = get_llm_client(model_name=model_name, provider_id=provider_id)
    
    # 构建消息列表
    messages: List[Any] = []
    
    # 如果有之前的视频总结，作为系统消息
    # 同时，我们需要判断历史消息中的第一条 assistant 消息是否是总结，如果是则跳过（避免重复）
    first_assistant_is_summary = False
    first_assistant_idx = None
    
    if previous_summary:
        # 使用提示词模板
        system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            previous_summary=previous_summary
        )
        messages.append(SystemMessage(content=system_prompt))
        print(f"[Chat Node] 已添加之前的视频总结作为上下文（长度: {len(previous_summary)} 字符）")
        
        # 检查历史消息中的第一条 assistant 消息是否是总结
        if history:
            for i, msg in enumerate(history):
                if msg.get("role") == "assistant":
                    first_assistant_idx = i
                    break
            if first_assistant_idx is not None:
                first_assistant_content = history[first_assistant_idx].get("content", "")
                # 如果第一条 assistant 消息的内容与 previous_summary 相似（前500字符相同），则认为是总结
                if len(first_assistant_content) > 500 and len(previous_summary) > 500:
                    if first_assistant_content[:500] == previous_summary[:500]:
                        first_assistant_is_summary = True
                        print(f"[Chat Node] 检测到历史消息中的第一条 assistant 消息是总结，将跳过以避免重复")
    
    # 添加历史对话消息（转换为 LangChain 消息格式）
    skip_first_assistant = first_assistant_is_summary
    for i, msg in enumerate(history):
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        # 如果这是第一条 assistant 消息且是总结，则跳过
        if skip_first_assistant and role == "assistant" and i == first_assistant_idx:
            print(f"[Chat Node] 跳过历史消息中的总结内容（已在系统消息中包含）")
            continue
        
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
    
    # 添加当前用户问题
    messages.append(HumanMessage(content=user_question))
    
    print(f"[Chat Node] 总消息数: {len(messages)}")
    print(f"[Chat Node] 正在调用 LLM 生成回复...")
    
    try:
        # 调用 LLM
        response = await llm.ainvoke(messages)
        
        answer = response.content if hasattr(response, 'content') else str(response)
        
        if not answer or not answer.strip():
            answer = "抱歉，无法生成回复。"
        
        print(f"[Chat Node] ✓ 成功生成回复，长度: {len(answer)} 字符")
        
        state["answer"] = answer
        return state
        
    except Exception as e:
        error_msg = f"对话生成失败: {str(e)}"
        print(f"[Chat Node] ✗ {error_msg}")
        import traceback
        traceback.print_exc()
        state["answer"] = error_msg
        return state

