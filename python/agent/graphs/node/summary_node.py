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
import re

# 创建 agent executor（单例模式，但会根据 state 中的配置动态创建）
_agent_executors = {}  # 使用字典存储不同配置的 executor


def _deduplicate_summary(summary: str) -> str:
    """
    去除摘要中的重复内容
    
    策略：
    1. 检测重复的标题（相同或相似的 Markdown 标题）
    2. 检测重复的段落内容（相似度高的段落）
    3. 保留第一个出现的，删除后续重复的
    
    Args:
        summary: 原始摘要文本
        
    Returns:
        去重后的摘要文本
    """
    if not summary or not summary.strip():
        return summary
    
    lines = summary.split('\n')
    seen_headers = {}  # 记录已见过的标题及其位置
    seen_content = []  # 记录已见过的内容片段
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检测 Markdown 标题（#、##、### 等）
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if header_match:
            header_level = len(header_match.group(1))
            header_text = header_match.group(2).strip()
            
            # 标准化标题文本（去除特殊字符，转为小写）用于比较
            normalized_header = re.sub(r'[^\w\u4e00-\u9fff]+', '', header_text.lower())
            
            # 检查是否已见过相同或相似的标题
            if normalized_header in seen_headers:
                # 找到重复的标题，跳过这个标题及其后续内容，直到下一个同级或更高级的标题
                print(f"[Summary Agent] 检测到重复标题: {header_text}，将跳过")
                skip_level = header_level
                i += 1
                # 跳过直到下一个同级或更高级的标题，或文档结束
                while i < len(lines):
                    next_line = lines[i]
                    next_header_match = re.match(r'^(#{1,6})\s+(.+)$', next_line.strip())
                    if next_header_match:
                        next_level = len(next_header_match.group(1))
                        # 如果遇到同级或更高级的标题，停止跳过
                        if next_level <= skip_level:
                            break
                    i += 1
                continue
            else:
                # 新标题，记录并保留
                seen_headers[normalized_header] = i
                result_lines.append(line)
                i += 1
                continue
        
        # 检测重复的列表项或段落
        # 对于包含时间戳标记的内容，提取核心文本进行比较
        line_stripped = line.strip()
        if line_stripped:
            # 移除时间戳标记用于比较
            content_without_timestamp = re.sub(r'\*?Content-\[\d{2}:\d{2}\](?:-video\d+)?', '', line_stripped)
            content_without_timestamp = re.sub(r'\[\[|\]\]', '', content_without_timestamp)
            content_normalized = re.sub(r'[^\w\u4e00-\u9fff]+', '', content_without_timestamp.lower())
            
            # 如果内容太短（少于5个字符），可能是格式标记，直接保留
            if len(content_normalized) < 5:
                result_lines.append(line)
                i += 1
                continue
            
            # 检查是否与已见过的内容高度相似（相似度>80%）
            is_duplicate = False
            for seen in seen_content:
                if len(seen) > 0 and len(content_normalized) > 0:
                    # 简单的相似度检查：如果一个是另一个的子串，或者两者非常相似
                    similarity = 0
                    if content_normalized in seen or seen in content_normalized:
                        similarity = min(len(content_normalized), len(seen)) / max(len(content_normalized), len(seen))
                    else:
                        # 计算字符重叠度
                        common_chars = set(content_normalized) & set(seen)
                        total_chars = set(content_normalized) | set(seen)
                        if len(total_chars) > 0:
                            similarity = len(common_chars) / len(total_chars)
                    
                    if similarity > 0.8:
                        is_duplicate = True
                        print(f"[Summary Agent] 检测到重复内容，相似度: {similarity:.2f}")
                        break
            
            if is_duplicate:
                i += 1
                continue
            else:
                # 记录新内容（只记录较长的内容，避免短格式标记干扰）
                if len(content_normalized) >= 10:
                    seen_content.append(content_normalized)
                result_lines.append(line)
                i += 1
        else:
            # 空行直接保留
            result_lines.append(line)
            i += 1
    
    result = '\n'.join(result_lines)
    
    # 清理多余的空行（连续3个以上空行合并为2个）
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    
    return result


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
    
    # 构建所有笔记的 Markdown 内容（包含原始 transcript 时间戳信息）
    notes_text = ""
    for i, note in enumerate(note_results, 1):
        notes_text += f"\n## 视频 {i}: {note.get('title', '未知标题')}\n\n"
        notes_text += f"**来源**: {note.get('platform', '未知平台')} - [{note.get('url', '未知链接')}]({note.get('url', '#')})\n\n"
        
        # 添加原始 transcript segments 信息（帮助 LLM 理解时间戳和内容的对应关系）
        transcript = note.get('transcript', {})
        segments = transcript.get('segments', [])
        if segments:
            notes_text += "**原始时间戳参考**（用于准确引用时间戳）：\n"
            # 只显示前30个segment作为参考（避免输入过长），如果segments太多则采样
            max_segments = 30
            if len(segments) > max_segments:
                # 均匀采样
                step = len(segments) // max_segments
                sampled_segments = [segments[i] for i in range(0, len(segments), step)][:max_segments]
            else:
                sampled_segments = segments
            
            for seg in sampled_segments:
                start = seg.get('start', 0)
                mm = int(start) // 60
                ss = int(start) % 60
                text = seg.get('text', '').strip()
                # 限制文本长度，避免单个segment太长
                if len(text) > 150:
                    text = text[:150] + "..."
                notes_text += f"- `[{mm:02d}:{ss:02d}]` {text}\n"
            notes_text += "\n"
        
        # 添加处理后的笔记内容
        notes_text += "**笔记内容**：\n"
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
                # 对摘要进行去重处理
                original_length = len(summary)
                summary = _deduplicate_summary(summary)
                deduplicated_length = len(summary)
                if original_length != deduplicated_length:
                    print(f"[Summary Agent] ✓ 已去除重复内容，长度从 {original_length} 减少到 {deduplicated_length} 字符")
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
