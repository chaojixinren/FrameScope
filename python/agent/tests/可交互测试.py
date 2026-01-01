"""
可交互的完整流程测试
测试 video_search -> note_generation -> summary_node -> trace_node 的完整流程

功能：
1. 用户可以输入问题
2. 自动执行 video_search_node 搜索视频
3. 自动执行 note_generation_node 生成笔记
4. 自动执行 summary_node 生成总结
5. 自动执行 trace_node 进行证据链回溯（生成关键帧）
6. 显示最终结果（包含关键帧截图）

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/可交互测试.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/可交互测试.py
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# 添加 agent 目录到路径
agent_path = Path(__file__).parent.parent
sys.path.insert(0, str(agent_path))

# 设置工作目录为 backend 目录（确保相对路径正确）
os.chdir(backend_path)

# 初始化数据库和环境
from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers, insert_provider
from app.db.models.providers import Provider
from app.db.engine import get_db
from graphs.node.video_search_node import video_search_node
from graphs.node.note_generation_node import note_generation_node
from graphs.node.summary_node import summary_node
from graphs.node.trace_node import trace_node
from graphs.state import AIState

# 测试配置
TEST_MODEL_NAME = "qwen-max"
TEST_PROVIDER_ID = "qwen"

# Groq 配置（用于转录）
GROQ_API_KEY = "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"  # 替换为实际的 Groq API Key
USE_GROQ_TRANSCRIBER = True  # 使用 Groq 转录器


def setup_database_config():
    """
    设置数据库配置：确保 qwen 提供商和 qwen-max 模型存在
    如果 USE_GROQ_TRANSCRIBER=True，还会配置 Groq 提供商
    """
    print("\n" + "="*60)
    print("正在设置数据库配置...")
    print("="*60)
    
    db = next(get_db())
    try:
        # 0. 如果使用 Groq 转录器，配置 Groq 提供商
        if USE_GROQ_TRANSCRIBER:
            groq_provider = db.query(Provider).filter_by(id="groq").first()
            if not groq_provider:
                print("  添加 Groq 提供商...")
                try:
                    insert_provider(
                        id="groq",
                        name="Groq",
                        api_key=GROQ_API_KEY,
                        base_url="https://api.groq.com/openai/v1",
                        logo="groq",
                        type_="groq",
                        enabled=1
                    )
                    print("  ✓ Groq 提供商添加成功")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "unique constraint" in error_msg or "already exists" in error_msg:
                        print("  ✓ Groq 提供商已存在")
                    else:
                        print(f"  ⚠ 添加 Groq 提供商时出错: {e}")
            else:
                print("  ✓ Groq 提供商已存在")
                # 更新 API Key（如果需要）
                if groq_provider.api_key != GROQ_API_KEY:
                    groq_provider.api_key = GROQ_API_KEY
                    db.commit()
                    print("  ✓ Groq API Key 已更新")
        
        # 1. 确保默认提供商存在
        seed_default_providers()
        print("  ✓ 默认提供商已配置")
        
        # 2. 检查 qwen 提供商是否存在
        qwen_provider = db.query(Provider).filter_by(id=TEST_PROVIDER_ID).first()
        if not qwen_provider:
            print(f"  ⚠ 警告: {TEST_PROVIDER_ID} 提供商不存在，请先配置")
            return False
        
        print(f"  ✓ {TEST_PROVIDER_ID} 提供商已存在")
        print("\n" + "="*60)
        return True
        
    except Exception as e:
        print(f"  ✗ 设置数据库配置时出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


async def run_video_search(state: AIState) -> AIState:
    """执行视频搜索节点"""
    print_section("步骤 1: 视频搜索")
    print(f"问题: {state.get('question', '')}")
    print("\n正在搜索相关视频...")
    
    try:
        result_state = video_search_node(state)
        video_urls = result_state.get("video_urls", [])
        
        if video_urls:
            print(f"\n✓ 成功找到 {len(video_urls)} 个高质量视频:\n")
            for i, video in enumerate(video_urls, 1):
                print(f"  {i}. {video.get('title', '未知标题')}")
                print(f"     URL: {video.get('url', '')}")
                print(f"     热度得分: {video.get('popularity_score', 0):.4f}\n")
        else:
            print("\n⚠ 未找到相关视频")
        
        return result_state
    except Exception as e:
        print(f"\n✗ 视频搜索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return state


async def run_note_generation(state: AIState) -> AIState:
    """执行笔记生成节点"""
    print_section("步骤 2: 笔记生成")
    
    video_urls = state.get("video_urls", [])
    if not video_urls:
        print("⚠ 没有视频需要处理，跳过笔记生成")
        state["note_results"] = []
        return state
    
    print(f"正在为 {len(video_urls)} 个视频生成笔记...")
    print("（这可能需要一些时间，请耐心等待）\n")
    
    try:
        result_state = await note_generation_node(state)
        note_results = result_state.get("note_results", [])
        
        if note_results:
            print(f"\n✓ 成功生成 {len(note_results)} 个视频的笔记:\n")
            for i, note in enumerate(note_results, 1):
                title = note.get("title", "未知标题")
                url = note.get("url", "")
                print(f"  {i}. {title}")
                print(f"     URL: {url}")
                markdown_length = len(note.get("markdown", ""))
                print(f"     笔记长度: {markdown_length} 字符\n")
        else:
            print("\n⚠ 未生成任何笔记")
        
        return result_state
    except Exception as e:
        print(f"\n✗ 笔记生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        state["note_results"] = []
        return state


async def run_summary(state: AIState) -> AIState:
    """执行总结节点"""
    print_section("步骤 3: 多视频总结")
    
    note_results = state.get("note_results", [])
    if not note_results:
        print("⚠ 没有笔记内容，跳过总结")
        state["summary_result"] = "没有可用的笔记内容进行总结"
        state["answer"] = state["summary_result"]
        return state
    
    print(f"正在对 {len(note_results)} 个视频的笔记进行总结...")
    print("（这可能需要一些时间，请耐心等待）\n")
    
    try:
        result_state = await summary_node(state)
        summary = result_state.get("summary_result", "")
        answer = result_state.get("answer", "")
        
        if summary or answer:
            print("\n✓ 总结生成成功\n")
            # 检查是否包含时间戳标记
            import re
            timestamp_count = len(re.findall(r'\*?Content-\[\d{2}:\d{2}\](?:-video\d+)?', summary or answer))
            if timestamp_count > 0:
                print(f"  ✓ 发现 {timestamp_count} 个时间戳标记，将在回溯节点中生成关键帧")
            else:
                print("  ⚠ 未发现时间戳标记，回溯节点将跳过")
        else:
            print("\n⚠ 未生成总结内容")
        
        return result_state
    except Exception as e:
        print(f"\n✗ 总结生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        state["summary_result"] = f"总结生成失败: {str(e)}"
        state["answer"] = state["summary_result"]
        return state


async def run_trace(state: AIState) -> AIState:
    """执行证据链回溯节点"""
    print_section("步骤 4: 证据链回溯（生成关键帧）")
    
    summary_result = state.get("summary_result", "")
    note_results = state.get("note_results", [])
    
    if not summary_result:
        print("⚠ 没有总结内容，跳过回溯")
        return state
    
    if not note_results:
        print("⚠ 没有视频笔记结果，无法生成关键帧")
        return state
    
    print("正在提取时间戳并生成关键帧截图...")
    print("（这可能需要一些时间，请耐心等待）\n")
    
    try:
        result_state = await trace_node(state)
        
        # 检查结果
        updated_summary = result_state.get("summary_result", "")
        trace_data = result_state.get("trace_data", {})
        
        if trace_data:
            print(f"\n✓ 成功生成 {len(trace_data)} 个关键帧截图\n")
            for key, data in list(trace_data.items())[:3]:  # 只显示前3个
                video_id = data.get("video_id", "")
                timestamp = data.get("timestamp", 0)
                frame_url = data.get("frame_url", "")
                mm = timestamp // 60
                ss = timestamp % 60
                print(f"  - 视频 {video_id} @ {mm:02d}:{ss:02d}")
                print(f"    关键帧: {frame_url}")
            
            if len(trace_data) > 3:
                print(f"  ... 还有 {len(trace_data) - 3} 个关键帧")
        else:
            print("\n⚠ 未生成关键帧（可能没有找到时间戳标记或视频未下载）")
        
        # 检查总结是否更新
        if updated_summary != summary_result:
            print("\n✓ 总结已更新（时间戳标记已替换为关键帧图片）")
        else:
            print("\n⚠ 总结未更新（可能没有时间戳标记需要处理）")
        
        return result_state
    except Exception as e:
        print(f"\n✗ 回溯失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return state


async def run_full_pipeline(question: str):
    """运行完整流程"""
    print("\n" + "="*60)
    print("开始执行完整流程")
    print("="*60)
    
    # 创建初始状态
    initial_state: AIState = {
        "question": question,
        "user_id": None,
        "timestamp": None,
        "session_id": None,
        "history": [],
        "answer": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": TEST_MODEL_NAME,
        "provider_id": TEST_PROVIDER_ID,
        "note_generation_status": None,
        "summary_result": None,
        "trace_data": None,
        "metadata": None,
    }
    
    # 步骤 1: 视频搜索
    state = await run_video_search(initial_state)
    
    # 检查是否有视频
    if not state.get("video_urls"):
        print("\n⚠ 未找到视频，流程终止")
        return state
    
    # 步骤 2: 笔记生成
    state = await run_note_generation(state)
    
    # 检查是否有笔记
    if not state.get("note_results"):
        print("\n⚠ 未生成笔记，跳过总结步骤")
        return state
    
    # 步骤 3: 总结
    state = await run_summary(state)
    
    # 检查是否有总结
    if not state.get("summary_result"):
        print("\n⚠ 未生成总结，跳过回溯步骤")
        return state
    
    # 步骤 4: 证据链回溯
    state = await run_trace(state)
    
    # 显示最终结果
    print_section("最终结果")
    final_answer = state.get("answer", state.get("summary_result", ""))
    if final_answer:
        print("包含关键帧证据的最终总结:\n")
        print("-"*60)
        # 显示前1000字符，避免输出过长
        print(final_answer[:1000])
        if len(final_answer) > 1000:
            print(f"\n... (还有 {len(final_answer) - 1000} 字符)")
        print("-"*60)
        
        # 显示trace_data统计
        trace_data = state.get("trace_data", {})
        if trace_data:
            print(f"\n✓ 共生成 {len(trace_data)} 个关键帧证据")
    else:
        print("⚠ 未生成最终结果")
    
    print_section("流程完成")
    print("所有步骤已执行完成！")
    
    return state


def main():
    """主函数"""
    print("\n" + "="*60)
    print("可交互的完整流程测试")
    print("="*60)
    print("\n此脚本将测试完整的视频搜索和总结流程：")
    print("  1. 视频搜索 (video_search_node)")
    print("  2. 笔记生成 (note_generation_node)")
    print("  3. 多视频总结 (summary_node)")
    print("  4. 证据链回溯 (trace_node) - 生成关键帧截图")
    print("\n注意：")
    print("  - 回溯节点会为总结中的时间戳标记生成关键帧截图")
    print("  - 确保 ffmpeg 已安装并可用")
    print("  - 视频会在笔记生成阶段下载（供回溯使用）")
    print("\n" + "-"*60)
    
    # 设置数据库配置
    if not setup_database_config():
        print("\n✗ 数据库配置失败，请检查配置后重试")
        return
    
    # 初始化数据库
    try:
        init_db()
        print("✓ 数据库初始化完成")
    except Exception as e:
        print(f"⚠ 数据库初始化警告: {e}")
    
    # 交互式输入
    print("\n" + "-"*60)
    print("请输入您的问题（例如：'索尼 A7M4 怎么样'）")
    print("输入 'quit' 或 'exit' 退出")
    print("-"*60)
    
    while True:
        try:
            question = input("\n问题: ").strip()
            
            if not question:
                print("⚠ 问题不能为空，请重新输入")
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n再见！")
                break
            
            # 运行完整流程
            result = asyncio.run(run_full_pipeline(question))
            
            # 询问是否继续
            print("\n" + "-"*60)
            continue_choice = input("是否继续测试？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("\n再见！")
                break
                
        except KeyboardInterrupt:
            print("\n\n用户中断，退出程序")
            break
        except Exception as e:
            print(f"\n✗ 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            continue_choice = input("\n是否继续测试？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("\n再见！")
                break


if __name__ == "__main__":
    main()
