"""
笔记生成节点
使用方案三（异步节点）+ ThreadPoolExecutor 并发生成笔记
"""

import asyncio
import sys
import os
import uuid
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

from graphs.state import AIState

# 添加 backend/app 到路径
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

# 添加 backend/agent 到路径，以便导入 utils
agent_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(agent_path))

# 默认使用 Groq 转录器（如果未设置环境变量，在 note_generation_node 函数中设置）

from app.services.note import NoteGenerator
from app.enmus.note_enums import DownloadQuality
from utils.config_helper import get_model_config_from_state


def generate_single_note_sync(video: Dict, model_name: str, provider_id: str) -> Dict:
    """
    同步生成单个视频的笔记
    
    Args:
        video: 视频信息 {"url": str, "platform": str, "title": str}
        model_name: GPT 模型名称
        provider_id: 提供商 ID
        
    Returns:
        Dict: 笔记结果
        
    Raises:
        Exception: 如果笔记生成失败
    """
    generator = NoteGenerator()
    
    try:
        # 为每个视频生成唯一的 task_id，用于状态跟踪、缓存和元数据保存
        task_id = str(uuid.uuid4())
        
        # 为了 trace_node 能够生成关键帧，需要下载视频
        # 设置 video_understanding=True 但 grid_size=None，这样会下载视频但不会生成缩略图网格
        note_result = generator.generate(
            video_url=video["url"],
            platform=video["platform"],
            quality=DownloadQuality.medium,
            task_id=task_id,
            model_name=model_name,
            provider_id=provider_id,
            link=False,
            screenshot=False,
            _format=None,
            style=None,
            extras=None,
            output_path=None,
            video_understanding=True,  # 设置为 True 以下载视频（供 trace_node 使用）
            video_interval=0,
            grid_size=None,  # 不生成缩略图网格，只下载视频
        )
        
        if not note_result:
            raise Exception(f"笔记生成返回 None: {video.get('url', 'unknown')}")
        
        # 构建返回的笔记结果字典（确保与 summary_node 期望的格式匹配）
        # 注意：NoteResult 的字段都是必需的（除了 Optional 标注的），所以不需要过多的 None 检查
        result_dict = {
            "url": video.get("url", ""),
            "platform": video.get("platform", note_result.audio_meta.platform),
            "title": note_result.audio_meta.title,
            "markdown": note_result.markdown,
            "transcript": {
                "language": note_result.transcript.language or "unknown",  # language 是 Optional[str]
                "full_text": note_result.transcript.full_text,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text
                    }
                    for seg in note_result.transcript.segments
                ]
            },
            "audio_meta": {
                "title": note_result.audio_meta.title,
                "duration": note_result.audio_meta.duration,
                "video_id": note_result.audio_meta.video_id,
                "platform": note_result.audio_meta.platform,
                "cover_url": note_result.audio_meta.cover_url or "",  # cover_url 是 Optional[str]
            }
        }
        
        return result_dict
    except Exception as e:
        raise Exception(f"笔记生成失败 {video.get('url', 'unknown')}: {str(e)}")


async def note_generation_node(state: AIState) -> AIState:
    """
    笔记生成节点 - 异步并发生成所有视频的笔记
    
    使用方案三：异步节点 + ThreadPoolExecutor
    
    注意：默认使用 Groq 转录器（支持并发，速度快）
    可以通过环境变量 TRANSCRIBER_TYPE 覆盖
    
    Args:
        state: AIState
        
    Returns:
        AIState: 包含 note_results 的状态
        
    Raises:
        Exception: 如果任何视频的笔记生成失败
    """
    video_urls = state.get("video_urls", [])
    
    if not video_urls:
        print("[Note Generation Node] 没有视频需要处理")
        state["note_results"] = []
        return state
    
    # 强制使用 Groq 转录器（覆盖环境变量中的旧值）
    os.environ["TRANSCRIBER_TYPE"] = "groq"
    # 设置 Groq 转录模型
    if not os.getenv("GROQ_TRANSCRIBER_MODEL"):
        os.environ["GROQ_TRANSCRIBER_MODEL"] = "whisper-large-v3"
    print(f"[Note Generation Node] 使用 Groq 转录器（支持并发，速度快）")
    
    # 获取模型配置
    try:
        model_name, provider_id = get_model_config_from_state(state)
        state["model_name"] = model_name
        state["provider_id"] = provider_id
        print(f"[Note Generation Node] 使用模型: {model_name}, 提供商: {provider_id}")
    except Exception as e:
        raise Exception(f"获取模型配置失败: {str(e)}")
    
    # 获取当前事件循环
    loop = asyncio.get_event_loop()
    
    # 创建线程池（限制并发数量为5）
    max_workers = min(5, len(video_urls))
    executor = ThreadPoolExecutor(max_workers=max_workers)
    
    print(f"[Note Generation Node] 开始并发生成 {len(video_urls)} 个视频的笔记（并发数: {max_workers}）")
    
    # 定义异步任务（将同步函数在线程池中运行）
    async def generate_single_note_async(video: Dict) -> Dict:
        try:
            return await loop.run_in_executor(
                executor,
                generate_single_note_sync,
                video,
                model_name,
                provider_id
            )
        except Exception as e:
            # 记录单个视频处理失败的错误，但不中断其他视频的处理
            video_url = video.get("url", "unknown")
            print(f"[Note Generation Node] 视频处理失败 {video_url}: {str(e)}")
            raise  # 重新抛出异常，让 asyncio.gather 处理
    
    # 创建所有任务
    tasks = [generate_single_note_async(video) for video in video_urls]
    
    try:
        # 并发执行所有任务（使用 return_exceptions=True 允许部分失败）
        # 这样可以继续处理成功生成的笔记，而不是因为一个失败就全部失败
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤出成功的结果和失败的任务
        note_results = []
        failed_videos = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 这是一个异常，记录失败的视频
                video_url = video_urls[i].get("url", "unknown")
                failed_videos.append((video_url, str(result)))
                print(f"[Note Generation Node] ⚠ 视频处理失败（已跳过）: {video_url}")
                print(f"   错误原因: {str(result)}")
            else:
                # 这是一个成功的笔记结果
                note_results.append(result)
        
        # 输出统计信息
        success_count = len(note_results)
        fail_count = len(failed_videos)
        total_count = len(video_urls)
        
        print(f"[Note Generation Node] 笔记生成完成: 成功 {success_count}/{total_count}, 失败 {fail_count}/{total_count}")
        
        # 验证结果
        if not note_results:
            error_msg = "所有视频的笔记生成都失败了，无法继续处理"
            print(f"[Note Generation Node] ✗ {error_msg}")
            raise Exception(error_msg)
        
        if fail_count > 0:
            print(f"[Note Generation Node] ⚠ 警告: {fail_count} 个视频的笔记生成失败，将继续处理成功生成的 {success_count} 个笔记")
        
        state["note_results"] = note_results
        return state
        
    except Exception as e:
        # 关闭线程池
        executor.shutdown(wait=False)
        error_msg = f"笔记生成过程中出错: {str(e)}"
        print(f"[Note Generation Node] {error_msg}")
        raise Exception(error_msg)
    finally:
        # 确保关闭线程池
        executor.shutdown(wait=True)

