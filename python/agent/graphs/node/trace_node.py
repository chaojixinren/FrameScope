"""
证据链回溯节点
从总结Markdown中提取时间戳，生成关键帧，并插入到Markdown中
"""

import re
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from graphs.state import AIState

# 添加 backend/app 到路径
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.utils.video_helper import generate_screenshot
from app.utils.url_parser import extract_video_id
from app.utils.path_helper import get_data_dir
from app.downloaders.bilibili_downloader import BilibiliDownloader
from dotenv import load_dotenv

load_dotenv()
IMAGE_OUTPUT_DIR = os.getenv("OUT_DIR", "./static/screenshots")
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "/static/screenshots")
api_path = os.getenv("API_BASE_URL", "http://localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8483")
BACKEND_BASE_URL = f"{api_path}:{BACKEND_PORT}"


def extract_timestamp_markers(markdown: str) -> List[Tuple[str, int, Optional[int], str]]:
    """
    从Markdown中提取时间戳标记（*Content-[mm:ss]格式）及其上下文
    
    支持格式：
    - *Content-[mm:ss]
    - *Content-[mm:ss]-video1 (指定视频索引)
    - Content-[mm:ss] (不带星号)
    
    返回: [(原始标记, 时间戳秒数, 视频索引, 上下文文本), ...]
    视频索引可能为None（如果标记中没有指定）
    上下文文本是标记前的结论/观点文本（最多200字符）
    """
    # 匹配 *Content-[mm:ss] 或 *Content-[mm:ss]-video1 格式
    # 也支持不带星号的格式
    pattern = r"(?:\*?)Content-\[(\d{2}):(\d{2})\](?:-video(\d+))?"
    results: List[Tuple[str, int, Optional[int], str]] = []
    
    for match in re.finditer(pattern, markdown):
        mm = int(match.group(1))
        ss = int(match.group(2))
        video_idx_str = match.group(3)
        video_idx = int(video_idx_str) - 1 if video_idx_str else None  # 转换为0-based索引
        total_seconds = mm * 60 + ss
        
        # 提取标记前的上下文文本（结论/观点）
        marker_start = match.start()
        # 向前查找，获取标记前的文本（最多200字符）
        context_start = max(0, marker_start - 200)
        context_text = markdown[context_start:marker_start].strip()
        
        # 清理上下文文本：移除多余的换行和空格
        context_text = re.sub(r'\s+', ' ', context_text)
        # 如果上下文太长，只保留最后部分（保留完整的句子）
        if len(context_text) > 150:
            # 尝试在句号、问号、感叹号处截断
            truncated = context_text[-150:]
            sentence_end = max(
                truncated.rfind('。'),
                truncated.rfind('？'),
                truncated.rfind('！'),
                truncated.rfind('.'),
                truncated.rfind('?'),
                truncated.rfind('!')
            )
            if sentence_end > 50:  # 确保至少保留50个字符
                context_text = "..." + truncated[sentence_end + 1:].strip()
            else:
                context_text = "..." + truncated
        
        results.append((match.group(0), total_seconds, video_idx, context_text))
    
    return results


def get_video_path_from_id(video_id: str, platform: str) -> Optional[str]:
    """
    根据video_id获取本地视频路径（如果已下载）
    优先查找data目录，如果不存在则查找example目录
    
    Args:
        video_id: 视频ID（如BV号）
        platform: 平台标识（如"bilibili"）
        
    Returns:
        视频路径（如果存在），否则None
    """
    if platform != "bilibili":
        # 目前主要支持bilibili，其他平台可以扩展
        return None
    
    # 先查找data目录
    data_dir = get_data_dir()
    video_path = os.path.join(data_dir, f"{video_id}.mp4")
    if os.path.exists(video_path):
        return video_path
    
    # 如果data目录不存在，查找example目录
    example_dir = Path(__file__).parent.parent.parent.parent / "example"
    example_video_path = example_dir / f"{video_id}.mp4"
    if example_video_path.exists():
        return str(example_video_path)
    
    return None


def match_timestamp_to_video(
    timestamp: int,
    video_idx: Optional[int],
    note_results: List[Dict]
) -> Optional[Dict]:
    """
    将时间戳匹配到对应的视频
    
    Args:
        timestamp: 时间戳（秒）
        video_idx: 视频索引（如果标记中指定了）
        note_results: 笔记结果列表
        
    Returns:
        匹配的视频信息字典，包含url, platform, video_id等
    """
    if video_idx is not None and 0 <= video_idx < len(note_results):
        # 如果标记中指定了视频索引，直接使用
        return note_results[video_idx]
    
    # 否则，尝试在所有视频的transcript中查找匹配的时间戳
    # 优先查找包含该时间戳的视频
    for note in note_results:
        transcript = note.get("transcript", {})
        segments = transcript.get("segments", [])
        
        # 检查是否有segment包含这个时间戳
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            if start <= timestamp <= end:
                return note
    
    # 如果找不到匹配的，使用第一个视频作为默认
    if note_results:
        return note_results[0]
    
    return None


async def trace_node(state: AIState) -> AIState:
    """
    证据链回溯节点
    从总结Markdown中提取时间戳，生成关键帧，并插入到Markdown中
    
    Args:
        state: AIState
        
    Returns:
        AIState: 更新后的state，包含插入关键帧链接后的summary_result
    """
    summary_result = state.get("summary_result", "")
    note_results = state.get("note_results", [])
    
    if not summary_result:
        print("[Trace Node] 没有总结内容需要处理")
        return state
    
    if not note_results:
        print("[Trace Node] 没有视频笔记结果，无法生成关键帧")
        return state
    
    # 确保输出目录存在
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
    print(f"[Trace Node] 输出目录: {IMAGE_OUTPUT_DIR}")
    
    print(f"[Trace Node] 开始提取时间戳并生成关键帧...")
    
    # 提取所有时间戳标记
    timestamp_markers = extract_timestamp_markers(summary_result)
    
    if not timestamp_markers:
        print("[Trace Node] 未找到时间戳标记（格式：*Content-[mm:ss]）")
        return state
    
    print(f"[Trace Node] 找到 {len(timestamp_markers)} 个时间戳标记")
    
    # 存储时间戳到关键帧URL的映射
    trace_data: Dict[str, Dict[str, Any]] = {}
    updated_markdown = summary_result
    screenshot_index = 0
    success_count = 0
    fail_count = 0
    
    # 处理每个时间戳标记
    for marker, timestamp_seconds, video_idx, context_text in timestamp_markers:
        try:
            # 匹配到对应的视频
            video_info = match_timestamp_to_video(timestamp_seconds, video_idx, note_results)
            
            if not video_info:
                print(f"[Trace Node] ⚠ 无法匹配时间戳 {timestamp_seconds}s 到视频，跳过")
                fail_count += 1
                continue
            
            video_url = video_info.get("url", "")
            platform = video_info.get("platform", "bilibili")
            audio_meta = video_info.get("audio_meta", {})
            video_id = audio_meta.get("video_id", "")
            
            if not video_id:
                # 尝试从URL中提取video_id
                video_id = extract_video_id(video_url, platform)
            
            if not video_id:
                print(f"[Trace Node] ⚠ 视频 {video_url} 缺少video_id，跳过")
                fail_count += 1
                continue
            
            # 获取本地视频路径
            video_path = get_video_path_from_id(video_id, platform)
            
            # 如果视频未下载，尝试按需下载（目前仅支持bilibili）
            if not video_path:
                if platform == "bilibili":
                    print(f"[Trace Node] 📥 视频 {video_id} 未下载到本地，尝试下载...")
                    try:
                        downloader = BilibiliDownloader()
                        video_path = downloader.download_video(video_url)
                        print(f"[Trace Node] ✓ 视频下载成功: {video_path}")
                    except Exception as download_error:
                        print(f"[Trace Node] ✗ 视频下载失败: {str(download_error)}")
                        fail_count += 1
                        continue
                else:
                    print(f"[Trace Node] ⚠ 平台 {platform} 暂不支持按需下载视频")
                    fail_count += 1
                    continue
            
            # 验证时间戳是否在视频时长范围内
            duration = audio_meta.get("duration", 0)
            if duration and timestamp_seconds > duration:
                print(f"[Trace Node] ⚠ 时间戳 {timestamp_seconds}s 超出视频时长 {duration}s，跳过")
                fail_count += 1
                continue
            
            # 生成关键帧截图
            print(f"[Trace Node] 📸 为视频 {video_id} 在 {timestamp_seconds}s 生成关键帧...")
            try:
                screenshot_path = generate_screenshot(
                    video_path=video_path,
                    output_dir=IMAGE_OUTPUT_DIR,
                    timestamp=timestamp_seconds,
                    index=screenshot_index
                )
                
                # 验证截图文件是否真的存在
                if not os.path.exists(screenshot_path):
                    raise FileNotFoundError(f"截图文件不存在: {screenshot_path}")
                
                # 验证文件大小（确保不是空文件）
                file_size = os.path.getsize(screenshot_path)
                if file_size == 0:
                    raise ValueError(f"截图文件为空: {screenshot_path}")
                
                print(f"[Trace Node] ✓ 截图生成成功: {screenshot_path} (大小: {file_size} bytes)")
                
            except subprocess.CalledProcessError as e:
                print(f"[Trace Node] ✗ ffmpeg 执行失败: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                fail_count += 1
                continue
            except FileNotFoundError as e:
                print(f"[Trace Node] ✗ {str(e)}")
                fail_count += 1
                continue
            except Exception as e:
                print(f"[Trace Node] ✗ 生成截图时出错: {str(e)}")
                fail_count += 1
                continue
            
            screenshot_index += 1
            
            # 构建前端可访问的URL（改进路径拼接）
            filename = Path(screenshot_path).name
            # 确保URL路径正确
            if IMAGE_BASE_URL.startswith('/'):
                img_url = f"{BACKEND_BASE_URL.rstrip('/')}{IMAGE_BASE_URL}/{filename}"
            else:
                img_url = f"{BACKEND_BASE_URL.rstrip('/')}/{IMAGE_BASE_URL.lstrip('/')}/{filename}"
            
            # 保存到trace_data（处理重复时间戳的情况）
            trace_key = f"{video_id}_{timestamp_seconds}"
            # 如果已存在相同的trace_key，添加序号
            if trace_key in trace_data:
                counter = 1
                while f"{trace_key}_{counter}" in trace_data:
                    counter += 1
                trace_key = f"{trace_key}_{counter}"
            
            trace_data[trace_key] = {
                "video_url": video_url,
                "video_id": video_id,
                "timestamp": timestamp_seconds,
                "frame_url": img_url,
                "frame_path": screenshot_path,
                "platform": platform
            }
            
            # 将时间戳标记替换为关键帧图片链接，并与结论强关联
            # 格式：使用引用块格式，将结论和关键帧关联显示
            mm = timestamp_seconds // 60
            ss = timestamp_seconds % 60
            if platform == "bilibili":
                video_link_url = f"{video_url}?t={timestamp_seconds}"
            else:
                video_link_url = video_url
            
            # 提取结论文本（从上下文文本中提取，去除时间戳标记）
            # 由于提示词要求时间戳标记紧跟在结论后面，上下文文本应该就是结论
            conclusion_text = context_text
            # 如果上下文文本包含时间戳标记，移除它
            conclusion_text = re.sub(r'\*?Content-\[\d{2}:\d{2}\](?:-video\d+)?', '', conclusion_text).strip()
            
            # 清理结论文本：移除Markdown格式标记（如**、*、#等），但保留内容
            conclusion_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', conclusion_text)  # 移除加粗
            conclusion_text = re.sub(r'\*([^*]+)\*', r'\1', conclusion_text)  # 移除斜体
            conclusion_text = re.sub(r'#{1,6}\s+', '', conclusion_text)  # 移除标题标记
            conclusion_text = conclusion_text.strip()
            
            # 如果结论文本为空或太短，尝试从更远的上下文提取
            if not conclusion_text or len(conclusion_text) < 5:
                # 在 updated_markdown 中查找标记位置
                marker_pos = updated_markdown.find(marker)
                if marker_pos > 0:
                    # 尝试从标记前更远的文本中提取（最多300字符）
                    extended_start = max(0, marker_pos - 300)
                    extended_context = updated_markdown[extended_start:marker_pos].strip()
                    extended_context = re.sub(r'\s+', ' ', extended_context)
                    # 提取最后一个句子（以句号、问号、感叹号结尾）
                    sentences = re.split(r'[。！？.!?]\s*', extended_context)
                    if sentences:
                        conclusion_text = sentences[-1].strip()
                        if len(conclusion_text) > 100:
                            conclusion_text = "..." + conclusion_text[-100:]
                if not conclusion_text or len(conclusion_text) < 5:
                    conclusion_text = "上述结论"
            
            # 将时间戳标记替换为关键帧图片和链接，自然融入文本
            # 格式：结论文本 + 关键帧图片 + 原片链接（自然排列）
            replacement = (
                f"{conclusion_text}\n\n"
                f"![关键帧 @ {mm:02d}:{ss:02d}]({img_url})\n\n"
                f"[查看原片 @ {mm:02d}:{ss:02d}]({video_link_url})"
            )
            
            # 替换标记（只替换第一次出现的，避免重复替换）
            updated_markdown = updated_markdown.replace(marker, replacement, 1)
            
            success_count += 1
            print(f"[Trace Node] ✓ 成功生成关键帧: {img_url}")
            
        except Exception as e:
            fail_count += 1
            print(f"[Trace Node] ✗ 处理时间戳 {timestamp_seconds}s 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # 更新state
    state["summary_result"] = updated_markdown
    state["answer"] = updated_markdown  # 同时更新answer
    state["trace_data"] = trace_data
    
    print(f"[Trace Node] 完成！成功: {success_count}, 失败: {fail_count}, 总计: {len(timestamp_markers)}")
    
    return state

