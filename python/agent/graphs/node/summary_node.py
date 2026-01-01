"""
多视频总结节点（Agent2）
使用 LangGraph prebuilt create_react_agent 实现
"""

from graphs.state import AIState
from tools.llm_tool import get_llm_client
from tools.summary_tools import summary_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from prompts.summary_prompts import SUMMARY_SYSTEM_PROMPT, SUMMARY_USER_PROMPT_TEMPLATE
from utils.config_helper import get_model_config_from_state
from typing import Optional

# 创建 agent executor（单例模式，但会根据 state 中的配置动态创建）
_agent_executors = {}  # 使用字典存储不同配置的 executor


def _get_agent_executor(model_name: Optional[str] = None, provider_id: Optional[str] = None):
    """获取或创建 agent executor"""
    # 使用 (model_name, provider_id) 作为 key，支持不同配置的 executor
    key = (model_name, provider_id)
    
    if key not in _agent_executors:
        llm = get_llm_client(model_name=model_name, provider_id=provider_id)
        _agent_executors[key] = create_react_agent(
            llm,
            summary_tools,
            prompt=SUMMARY_SYSTEM_PROMPT
        )
    return _agent_executors[key]


async def summary_node(state: AIState) -> AIState:
    """
    多视频总结节点 - 使用 ReAct Agent 对多个视频笔记进行总结
    
    Args:
        state: AIState
        
    Returns:
        AIState: 包含 summary_result 和 answer 的状态
    """
    note_results = state.get("note_results", [])
    user_question = state.get("question", "")
    
    if not note_results:
        state["summary_result"] = "没有可用的笔记内容进行总结"
        state["answer"] = state["summary_result"]
        return state
    
    print(f"[Summary Agent] 开始总结 {len(note_results)} 个视频的笔记")
    
    # 构建所有笔记的 Markdown 内容
    notes_text = ""
    for i, note in enumerate(note_results, 1):
        notes_text += f"\n## 视频 {i}: {note.get('title', '未知标题')}\n\n"
        notes_text += f"**来源**: {note.get('platform', '未知平台')} - [{note.get('url', '未知链接')}]({note.get('url', '#')})\n\n"
        notes_text += f"{note.get('markdown', '无内容')}\n\n"
        notes_text += "---\n\n"
    
    # 从 state 中获取模型配置
    model_name, provider_id = get_model_config_from_state(state)
    
    print(f"[Summary Agent] 使用模型: {model_name}, 提供商: {provider_id}")
    print(f"[Summary Agent] 输入内容长度: {len(notes_text)} 字符")
    print(f"[Summary Agent] 用户问题: {user_question}")
    
    # 获取 agent executor（使用 state 中的配置）
    executor = _get_agent_executor(model_name=model_name, provider_id=provider_id)
    
    # 构建提示词
    user_prompt = SUMMARY_USER_PROMPT_TEMPLATE.format(
        question=user_question,
        note_count=len(note_results),
        notes_text=notes_text
    )
    
    print(f"[Summary Agent] 提示词长度: {len(user_prompt)} 字符")
    print(f"[Summary Agent] 正在调用 LLM 生成总结...")
    
    try:
        # 创建运行时的配置，包含 state
        config = {
            "configurable": {
                "user_id": state.get("user_id")
            }
        }
        
        # 执行 agent（异步调用）
        result = await executor.ainvoke(
            {"messages": [HumanMessage(content=user_prompt)]},
            config=config
        )
        
        print(f"[Summary Agent] LLM 调用完成，正在解析结果...")
        
        # 提取最后一条 AI 消息作为总结
        messages = result.get("messages", [])
        print(f"[Summary Agent] 收到 {len(messages)} 条消息")
        
        ai_messages = [msg for msg in messages 
                      if hasattr(msg, "content") and msg.__class__.__name__ == "AIMessage"]
        
        print(f"[Summary Agent] 找到 {len(ai_messages)} 条 AI 消息")
        
        if ai_messages:
            summary = ai_messages[-1].content
            if not summary or not summary.strip():
                print(f"[Summary Agent] ⚠ 警告: AI 消息内容为空")
                summary = "无法生成总结内容"
            else:
                print(f"[Summary Agent] ✓ 成功提取总结内容，长度: {len(summary)} 字符")
        else:
            print(f"[Summary Agent] ⚠ 警告: 未找到 AI 消息")
            summary = "无法生成总结内容"
        
        print(f"[Summary Agent] 总结完成（最终长度: {len(summary)} 字符）")
        
        state["summary_result"] = summary
        state["answer"] = summary
        
        # 添加元数据
        state["metadata"] = {
            "total_videos": len(note_results),
            "videos_processed": len(note_results),
        }
        
        return state
        
    except Exception as e:
        error_msg = f"总结生成失败: {str(e)}"
        print(f"[Summary Agent] {error_msg}")
        import traceback
        print(f"[Summary Agent] 详细错误信息:")
        traceback.print_exc()
        raise Exception(error_msg)
