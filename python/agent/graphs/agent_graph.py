"""
Multi-Video Graph 模块
多视频搜索和总结功能
"""

from langgraph.graph import StateGraph, END

from graphs.state import AIState
from graphs.node.video_search_node import video_search_node
from graphs.node.note_generation_node import note_generation_node
from graphs.node.summary_node import summary_node


def build_multi_video_graph() -> StateGraph:
    """
    构建多视频搜索和总结的主工作流
    
    Returns:
        StateGraph: 编译后的图工作流
    """
    workflow = StateGraph(AIState)
    
    # 添加节点
    workflow.add_node("video_search", video_search_node)  # Agent1: 视频搜索
    workflow.add_node("note_generation", note_generation_node)  # 批量生成笔记
    workflow.add_node("summary", summary_node)  # Agent2: 多视频总结
    
    # 设置边
    workflow.set_entry_point("video_search")
    workflow.add_edge("video_search", "note_generation")
    workflow.add_edge("note_generation", "summary")
    workflow.add_edge("summary", END)
    
    return workflow.compile()

