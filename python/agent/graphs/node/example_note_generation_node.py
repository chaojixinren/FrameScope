"""
示例视频笔记生成节点
直接从 example 目录读取视频文件，跳过下载步骤
"""

import asyncio
import sys
import os
import uuid
import ffmpeg
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

from graphs.state import AIState

# 添加 backend/app 到路径
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

# 添加 backend/agent 到路径
agent_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(agent_path))

from app.services.note import NoteGenerator
from app.models.audio_model import AudioDownloadResult
from app.models.transcriber_model import TranscriptResult
from app.models.notes_model import NoteResult
from app.enmus.note_enums import DownloadQuality
from app.enmus.task_status_enums import TaskStatus
from utils.config_helper import get_model_config_from_state


def get_video_duration(video_path: str) -> float:
    """
    使用 ffmpeg 获取视频时长（秒）
    """
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        return duration
    except Exception as e:
        print(f"无法获取视频时长 {video_path}: {e}")
        return 0.0


def create_audio_meta_from_example_file(video_id: str, example_dir: Path) -> AudioDownloadResult:
    """
    从 example 目录的文件创建 AudioDownloadResult
    
    Args:
        video_id: 视频ID（如 BV1Dk4y1X71E）
        example_dir: example 目录路径
        
    Returns:
        AudioDownloadResult 对象
    """
    audio_path = example_dir / f"{video_id}.mp3"
    video_path = example_dir / f"{video_id}.mp4"
    
    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    # 获取视频时长
    duration = get_video_duration(str(video_path))
    
    # 创建基本的 raw_info（模拟 yt-dlp 的 info）
    raw_info = {
        "id": video_id,
        "title": f"视频 {video_id}",  # 默认标题
        "duration": duration,
        "thumbnail": None,
        "tags": [],
    }
    
    return AudioDownloadResult(
        file_path=str(audio_path),
        title=raw_info["title"],
        duration=duration,
        cover_url=None,
        platform="bilibili",
        video_id=video_id,
        raw_info=raw_info,
        video_path=str(video_path)  # 包含视频路径
    )


def generate_single_note_from_example_sync(video_id: str, example_dir: Path, model_name: str, provider_id: str) -> Dict:
    """
    同步生成单个示例视频的笔记（跳过下载步骤）
    
    Args:
        video_id: 视频ID（如 BV1Dk4y1X71E）
        example_dir: example 目录路径
        model_name: GPT 模型名称
        provider_id: 提供商 ID
        
    Returns:
        Dict: 笔记结果
    """
    generator = NoteGenerator()
    
    try:
        # 为每个视频生成唯一的 task_id
        task_id = str(uuid.uuid4())
        
        # 从 example 目录创建 AudioDownloadResult
        audio_meta = create_audio_meta_from_example_file(video_id, example_dir)
        
        # 设置视频路径，供后续使用
        generator.video_path = Path(audio_meta.video_path) if audio_meta.video_path else None
        
        # 获取 GPT 实例
        from app.services.provider import ProviderService
        provider = ProviderService.get_provider_by_id(provider_id)
        if not provider:
            raise Exception(f"未找到模型供应商: provider_id={provider_id}")
        
        from app.gpt.gpt_factory import GPTFactory
        from app.models.model_config import ModelConfig
        config = ModelConfig(
            api_key=provider["api_key"],
            base_url=provider["base_url"],
            model_name=model_name,
            provider=provider["type"],
            name=provider["name"],
        )
        gpt = GPTFactory().from_config(config)
        
        # 缓存文件路径
        from app.services.note import NOTE_OUTPUT_DIR
        transcript_cache_file = NOTE_OUTPUT_DIR / f"{task_id}_transcript.json"
        markdown_cache_file = NOTE_OUTPUT_DIR / f"{task_id}_markdown.md"
        
        # 更新状态
        generator._update_status(task_id, TaskStatus.PARSING)
        
        # 1. 转写音频（跳过下载）
        generator._update_status(task_id, TaskStatus.TRANSCRIBING)
        transcript = generator._transcribe_audio(
            audio_file=audio_meta.file_path,
            transcript_cache_file=transcript_cache_file,
            status_phase=TaskStatus.TRANSCRIBING,
        )
        
        # 2. GPT 总结
        markdown = generator._summarize_text(
            audio_meta=audio_meta,
            transcript=transcript,
            gpt=gpt,
            markdown_cache_file=markdown_cache_file,
            link=False,
            screenshot=False,
            formats=[],
            style=None,
            extras=None,
            video_img_urls=[],
        )
        
        # 3. 保存记录到数据库
        generator._update_status(task_id, TaskStatus.SAVING)
        generator._save_metadata(video_id=audio_meta.video_id, platform=audio_meta.platform, task_id=task_id)
        
        # 4. 完成
        generator._update_status(task_id, TaskStatus.SUCCESS)
        
        # 构建返回结果
        note_result = NoteResult(
            markdown=markdown,
            transcript=transcript,
            audio_meta=audio_meta
        )
        
        result_dict = {
            "url": f"https://www.bilibili.com/video/{video_id}",  # 构造一个假的URL
            "platform": audio_meta.platform,
            "title": audio_meta.title,
            "markdown": note_result.markdown,
            "transcript": {
                "language": note_result.transcript.language or "unknown",
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
                "cover_url": note_result.audio_meta.cover_url or "",
            }
        }
        
        return result_dict
    except Exception as e:
        raise Exception(f"笔记生成失败 {video_id}: {str(e)}")


async def example_note_generation_node(state: AIState) -> AIState:
    """
    示例视频笔记生成节点 - 直接从 example 目录读取文件
    
    Args:
        state: AIState，需要包含 video_ids 字段（视频ID列表）
        
    Returns:
        AIState: 包含 note_results 的状态
    """
    # 获取视频ID列表（从 state 中获取）
    video_ids = state.get("video_ids", [])
    
    if not video_ids:
        print("[Example Note Generation Node] 没有视频ID需要处理")
        state["note_results"] = []
        return state
    
    # 获取 example 目录路径
    example_dir = Path(__file__).parent.parent.parent.parent / "example"
    if not example_dir.exists():
        raise Exception(f"example 目录不存在: {example_dir}")
    
    # 强制使用 Groq 转录器
    os.environ["TRANSCRIBER_TYPE"] = "groq"
    if not os.getenv("GROQ_TRANSCRIBER_MODEL"):
        os.environ["GROQ_TRANSCRIBER_MODEL"] = "whisper-large-v3"
    print(f"[Example Note Generation Node] 使用 Groq 转录器")
    
    # 获取模型配置
    try:
        model_name, provider_id = get_model_config_from_state(state)
        state["model_name"] = model_name
        state["provider_id"] = provider_id
        print(f"[Example Note Generation Node] 使用模型: {model_name}, 提供商: {provider_id}")
    except Exception as e:
        raise Exception(f"获取模型配置失败: {str(e)}")
    
    # 获取当前事件循环
    loop = asyncio.get_event_loop()
    
    # 创建线程池（限制并发数量为5）
    max_workers = min(5, len(video_ids))
    executor = ThreadPoolExecutor(max_workers=max_workers)
    
    print(f"[Example Note Generation Node] 开始并发生成 {len(video_ids)} 个视频的笔记（并发数: {max_workers}）")
    
    # 定义异步任务
    async def generate_single_note_async(video_id: str) -> Dict:
        try:
            return await loop.run_in_executor(
                executor,
                generate_single_note_from_example_sync,
                video_id,
                example_dir,
                model_name,
                provider_id
            )
        except Exception as e:
            print(f"[Example Note Generation Node] 视频处理失败 {video_id}: {str(e)}")
            raise
    
    # 创建所有任务
    tasks = [generate_single_note_async(video_id) for video_id in video_ids]
    
    try:
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤出成功的结果和失败的任务
        note_results = []
        failed_videos = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                video_id = video_ids[i]
                failed_videos.append((video_id, str(result)))
                print(f"[Example Note Generation Node] ⚠ 视频处理失败（已跳过）: {video_id}")
                print(f"   错误原因: {str(result)}")
            else:
                note_results.append(result)
        
        # 输出统计信息
        success_count = len(note_results)
        fail_count = len(failed_videos)
        total_count = len(video_ids)
        
        print(f"[Example Note Generation Node] 笔记生成完成: 成功 {success_count}/{total_count}, 失败 {fail_count}/{total_count}")
        
        # 验证结果
        if not note_results:
            error_msg = "所有视频的笔记生成都失败了，无法继续处理"
            print(f"[Example Note Generation Node] ✗ {error_msg}")
            raise Exception(error_msg)
        
        if fail_count > 0:
            print(f"[Example Note Generation Node] ⚠ 警告: {fail_count} 个视频的笔记生成失败，将继续处理成功生成的 {success_count} 个笔记")
        
        state["note_results"] = note_results
        return state
        
    except Exception as e:
        executor.shutdown(wait=False)
        error_msg = f"笔记生成过程中出错: {str(e)}"
        print(f"[Example Note Generation Node] {error_msg}")
        raise Exception(error_msg)
    finally:
        executor.shutdown(wait=True)

