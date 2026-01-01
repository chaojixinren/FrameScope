"""
测试 trace_node（证据链回溯节点）
检查是否能真正进行回溯，生成关键帧截图并插入到Markdown中

测试说明：
1. 模拟 summary_result 包含时间戳标记
2. 模拟 note_results 包含视频信息（需要真实的视频已下载）
3. 测试 trace_node 能否：
   - 正确提取时间戳标记
   - 匹配到对应的视频
   - 生成关键帧截图
   - 将截图链接插入到Markdown中

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/测试trace_node回溯节点.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/测试trace_node回溯节点.py
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

# 导入必要的模块
from graphs.node.trace_node import trace_node
from graphs.node.trace_node import extract_timestamp_markers  # 导入提取函数用于测试
from graphs.state import AIState
from app.utils.path_helper import get_data_dir

# 测试配置
TEST_VIDEO_URLS = [
    "https://www.bilibili.com/video/BV1QgsAzzEwY",  # 视频1
    "https://www.bilibili.com/video/BV1An2SYiEQY",  # 视频2
]

# 从URL中提取video_id（简单实现）
def extract_video_id_from_url(url: str) -> str:
    """从Bilibili URL中提取BV号"""
    import re
    match = re.search(r"BV([0-9A-Za-z]+)", url)
    return f"BV{match.group(1)}" if match else ""


def create_mock_note_results() -> list:
    """
    创建模拟的 note_results
    注意：这些视频需要已经下载到本地，否则trace_node会尝试下载
    """
    note_results = []
    
    for i, url in enumerate(TEST_VIDEO_URLS):
        video_id = extract_video_id_from_url(url)
        
        # 检查视频是否已下载
        data_dir = get_data_dir()
        video_path = os.path.join(data_dir, f"{video_id}.mp4")
        video_exists = os.path.exists(video_path)
        
        note_result = {
            "url": url,
            "platform": "bilibili",
            "title": f"测试视频 {i+1}",
            "markdown": f"这是视频 {i+1} 的笔记内容。",
            "transcript": {
                "language": "zh",
                "full_text": f"这是视频 {i+1} 的完整转录文本。",
                "segments": [
                    {
                        "start": 0,
                        "end": 10,
                        "text": "这是第一段内容"
                    },
                    {
                        "start": 10,
                        "end": 30,
                        "text": "这是第二段内容"
                    },
                    {
                        "start": 30,
                        "end": 60,
                        "text": "这是第三段内容"
                    }
                ]
            },
            "audio_meta": {
                "title": f"测试视频 {i+1}",
                "duration": 300.0,  # 5分钟视频
                "video_id": video_id,
                "platform": "bilibili",
                "cover_url": ""
            }
        }
        
        note_results.append(note_result)
        
        # 打印视频状态
        if video_exists:
            print(f"  ✓ 视频 {i+1} ({video_id}) 已下载: {video_path}")
        else:
            print(f"  ⚠ 视频 {i+1} ({video_id}) 未下载，trace_node 将尝试下载")
            print(f"     路径: {video_path}")
    
    return note_results


def create_mock_summary_with_timestamps() -> str:
    """
    创建包含时间戳标记的模拟总结
    格式：*Content-[mm:ss] 或 *Content-[mm:ss]-video{N}
    """
    summary = """# 多视频总结测试

## 相机画质对比

通过多个视频的测试，我们发现A7M4的画质明显优于A7M3 *Content-[00:30]-video1。

## 价格分析

两款相机在价格上存在差异 *Content-[01:20]-video1 *Content-[00:45]-video2。

## 性能测试

从实际使用来看，A7M4的性能更出色 *Content-[02:15]-video1。

## 总结

综合来看，A7M4是更好的选择 *Content-[03:00]-video2。
"""
    return summary


async def test_trace_node():
    """
    测试 trace_node 回溯功能
    """
    print("\n" + "="*60)
    print("开始测试 trace_node（证据链回溯节点）")
    print("="*60 + "\n")
    
    # 1. 创建模拟的 note_results
    print("[1/4] 创建模拟的 note_results...")
    note_results = create_mock_note_results()
    print(f"  ✓ 创建了 {len(note_results)} 个视频的笔记结果\n")
    
    # 2. 创建包含时间戳标记的 summary_result
    print("[2/4] 创建包含时间戳标记的 summary_result...")
    summary_result = create_mock_summary_with_timestamps()
    
    # 提取并显示时间戳标记
    timestamp_markers = extract_timestamp_markers(summary_result)
    print(f"  ✓ 找到 {len(timestamp_markers)} 个时间戳标记:")
    for marker, seconds, video_idx, context_text in timestamp_markers:
        video_info = f"视频{video_idx+1}" if video_idx is not None else "未指定"
        mm = seconds // 60
        ss = seconds % 60
        print(f"    - {marker} -> {mm:02d}:{ss:02d} ({video_info})")
        if context_text:
            print(f"      上下文: {context_text[:50]}...")
    print()
    
    # 3. 创建测试用的 state
    print("[3/4] 创建测试用的 state...")
    test_state: AIState = {
        "question": "测试回溯节点",
        "user_id": 1,
        "session_id": "test_trace_session",
        "timestamp": None,
        "history": [],
        "answer": None,
        "video_urls": [],
        "search_query": None,
        "note_results": note_results,
        "model_name": None,
        "provider_id": None,
        "note_generation_status": None,
        "summary_result": summary_result,
        "trace_data": None,
        "metadata": None,
    }
    print("  ✓ State 创建完成\n")
    
    # 4. 调用 trace_node
    print("[4/4] 调用 trace_node 进行回溯...")
    print("  这可能需要一些时间（生成截图）...\n")
    
    try:
        result_state = await trace_node(test_state)
        
        # 5. 验证结果
        print("\n" + "="*60)
        print("验证结果")
        print("="*60 + "\n")
        
        # 检查 summary_result 是否更新
        updated_summary = result_state.get("summary_result", "")
        if updated_summary != summary_result:
            print("✓ summary_result 已更新（时间戳标记已替换为关键帧）")
            
            # 检查是否包含图片链接
            if "![关键帧" in updated_summary:
                print("✓ 包含关键帧图片链接")
                # 统计图片数量
                import re
                img_count = len(re.findall(r"!\[关键帧", updated_summary))
                print(f"  - 找到 {img_count} 个关键帧图片")
            else:
                print("⚠ 未找到关键帧图片链接")
            
            # 检查是否包含视频链接
            if "[🔗 原片" in updated_summary:
                print("✓ 包含原片跳转链接")
            else:
                print("⚠ 未找到原片跳转链接")
        else:
            print("⚠ summary_result 未更新（可能没有找到时间戳标记或生成失败）")
        
        # 检查 trace_data
        trace_data = result_state.get("trace_data", {})
        if trace_data:
            print(f"\n✓ trace_data 包含 {len(trace_data)} 个关键帧记录:")
            for key, data in trace_data.items():
                print(f"  - {key}:")
                print(f"    视频ID: {data.get('video_id')}")
                print(f"    时间戳: {data.get('timestamp')}s")
                print(f"    图片URL: {data.get('frame_url')}")
                print(f"    本地路径: {data.get('frame_path')}")
                
                # 验证文件是否存在
                frame_path = data.get('frame_path')
                if frame_path and os.path.exists(frame_path):
                    file_size = os.path.getsize(frame_path)
                    print(f"    ✓ 截图文件存在 (大小: {file_size} bytes)")
                else:
                    print(f"    ✗ 截图文件不存在")
        else:
            print("\n⚠ trace_data 为空（可能没有成功生成关键帧）")
        
        # 显示更新后的 summary_result（前500字符）
        print("\n" + "="*60)
        print("更新后的 summary_result（前500字符）:")
        print("="*60)
        print(updated_summary[:500])
        if len(updated_summary) > 500:
            print("...")
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60 + "\n")
        
        return result_state
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def test_extract_timestamp_markers():
    """
    单独测试时间戳标记提取功能
    """
    print("\n" + "="*60)
    print("测试时间戳标记提取功能")
    print("="*60 + "\n")
    
    test_markdown = """
# 测试文档

这是第一段 *Content-[00:30]-video1。

这是第二段 *Content-[01:20]。

这是第三段 Content-[02:15]-video2。

这是第四段 *Content-[03:00]。
"""
    
    markers = extract_timestamp_markers(test_markdown)
    
    print(f"找到 {len(markers)} 个时间戳标记:\n")
    for i, (marker, seconds, video_idx, context_text) in enumerate(markers, 1):
        mm = seconds // 60
        ss = seconds % 60
        video_info = f"视频{video_idx+1}" if video_idx is not None else "未指定"
        print(f"{i}. 标记: {marker}")
        print(f"   时间戳: {mm:02d}:{ss:02d} ({seconds}秒)")
        print(f"   视频索引: {video_info}")
        if context_text:
            print(f"   上下文: {context_text[:80]}...")
        print()
    
    return markers


async def main():
    """
    主函数
    """
    print("\n" + "="*60)
    print("Trace Node 回溯节点测试")
    print("="*60)
    print("\n注意：")
    print("1. 确保测试视频已下载到本地（在 data/data 目录下）")
    print("2. 确保 ffmpeg 已安装并可用")
    print("3. 确保环境变量 OUT_DIR 和 IMAGE_BASE_URL 已正确设置")
    print("="*60 + "\n")
    
    # 测试1: 时间戳标记提取
    print("\n>>> 测试1: 时间戳标记提取")
    await test_extract_timestamp_markers()
    
    # 测试2: 完整的 trace_node 测试
    print("\n>>> 测试2: 完整的 trace_node 回溯测试")
    await test_trace_node()


if __name__ == '__main__':
    asyncio.run(main())

