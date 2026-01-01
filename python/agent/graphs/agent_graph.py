"""
Multi-Video Graph 模块
多视频搜索和总结功能（支持首次提问和后续对话）
"""

from langgraph.graph import StateGraph, END

from graphs.state import AIState
from graphs.node.video_search_node import video_search_node
from graphs.node.note_generation_node import note_generation_node
from graphs.node.example_note_generation_node import example_note_generation_node
from graphs.node.summary_node import summary_node
from graphs.node.trace_node import trace_node
from graphs.node.chat_node import chat_node


def should_do_video_search(state: AIState) -> str:
    """
    判断是否需要进行视频搜索
    
    规则：
    - 如果 history 为空或只有用户消息（没有助手回复），说明是第一次提问，执行视频搜索
    - 如果 history 中有助手消息，说明是后续提问，只进行普通对话
    
    Returns:
        "video_search" 或 "chat"
    """
    history = state.get("history", [])
    
    # 检查是否有助手回复
    has_assistant_message = any(
        msg.get("role") == "assistant" 
        for msg in history
    )
    
    if has_assistant_message:
        print("[Router] 检测到历史对话，使用普通对话模式")
        return "chat"
    else:
        print("[Router] 首次提问，执行视频搜索和总结流程")
        return "video_search"


def router_node(state: AIState) -> AIState:
    """
    路由节点：根据历史对话判断是首次提问还是后续对话
    这个节点不做任何操作，只是用于路由
    """
    return state


def build_multi_video_graph() -> StateGraph:
    """
    构建多视频搜索和总结的主工作流（支持条件路由）
    
    工作流程：
    - 首次提问：router -> video_search -> note_generation -> summary -> trace -> END
    - 后续提问：router -> chat -> END（使用历史总结作为上下文）
    
    Returns:
        StateGraph: 编译后的图工作流
    """
    workflow = StateGraph(AIState)
    
    # 添加节点
    workflow.add_node("router", router_node)  # 路由节点
    workflow.add_node("video_search", video_search_node)  # Agent1: 视频搜索
    workflow.add_node("note_generation", note_generation_node)  # 批量生成笔记
    workflow.add_node("summary", summary_node)  # Agent2: 多视频总结
    workflow.add_node("trace", trace_node)  # 证据链回溯：生成关键帧
    workflow.add_node("chat", chat_node)  # 普通对话节点
    
    # 设置入口点为路由节点
    workflow.set_entry_point("router")
    
    # 从路由节点进行条件分支
    workflow.add_conditional_edges(
        "router",
        should_do_video_search,
        {
            "video_search": "video_search",
            "chat": "chat"
        }
    )
    
    # 视频搜索流程的边
    workflow.add_edge("video_search", "note_generation")
    workflow.add_edge("note_generation", "summary")
    workflow.add_edge("summary", "trace")
    workflow.add_edge("trace", END)
    
    # 普通对话流程的边
    workflow.add_edge("chat", END)
    
    return workflow.compile()


def build_example_video_graph() -> StateGraph:
    """
    构建示例视频处理工作流（跳过视频搜索，直接使用example目录下的视频）
    
    Returns:
        StateGraph: 编译后的图工作流
    """
    workflow = StateGraph(AIState)
    
    # 添加节点
    workflow.add_node("example_note_generation", example_note_generation_node)  # 从example目录生成笔记
    workflow.add_node("summary", summary_node)  # Agent2: 多视频总结
    workflow.add_node("trace", trace_node)  # 证据链回溯：生成关键帧
    
    # 设置边（跳过video_search节点）
    workflow.set_entry_point("example_note_generation")
    workflow.add_edge("example_note_generation", "summary")
    workflow.add_edge("summary", "trace")
    workflow.add_edge("trace", END)
    
    return workflow.compile()

