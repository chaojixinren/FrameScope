"""
单独测试 Groq 转写器功能
用于测试 Groq API 的音频转写功能

注意：
- Groq 提供商配置应从数据库 (framescope.db) 中读取
- 请确保数据库中已配置 Groq 提供商，包含正确的 API Key 和 Base URL
- 如果数据库中不存在，程序会提示如何在数据库中配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# 设置工作目录为 backend 目录
os.chdir(backend_path)

# 导入必要的模块
from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers
from app.transcriber.transcriber_provider import get_transcriber
from app.services.provider import ProviderService

# ==================== 配置区域 ====================
# 测试音频文件路径（如果已有音频文件，直接指定路径）
# 如果没有，可以设置为 None，程序会从视频 URL 下载音频
TEST_AUDIO_FILE = None  # 例如: "test_audio.mp3"

# 可选：测试视频 URL（如果 TEST_AUDIO_FILE 为 None，将下载此视频的音频）
TEST_VIDEO_URL = "https://www.bilibili.com/video/BV16GvmBpEu4"
TEST_PLATFORM = "bilibili"
# ================================================


def setup_groq_provider():
    """从数据库读取并验证 Groq 提供商配置"""
    print("\n" + "="*60)
    print("读取 Groq 提供商配置...")
    print("="*60)
    
    # 直接从数据库读取配置
    provider = ProviderService.get_provider_by_id('groq')
    
    if not provider:
        raise ValueError(
            "数据库中未找到 Groq 提供商配置。\n"
            "请在数据库中添加 Groq 提供商，包含以下字段：\n"
            "  - id: 'groq'\n"
            "  - name: 'Groq'\n"
            "  - api_key: '你的Groq API Key'\n"
            "  - base_url: 'https://api.groq.com/openai/v1'\n"
            "  - logo: 'groq'\n"
            "  - type: 'groq' 或 'built-in'\n"
            "  - enabled: 1"
        )
    
    # 验证配置是否完整
    api_key = provider.get('api_key')
    base_url = provider.get('base_url')
    enabled = provider.get('enabled')
    
    if not api_key or api_key.strip() == '':
        raise ValueError("Groq 提供商的 API Key 为空，请在数据库中配置 API Key")
    
    if not base_url or base_url.strip() == '':
        raise ValueError("Groq 提供商的 Base URL 为空，请在数据库中配置 Base URL")
    
    if enabled != 1:
        print(f"  ⚠ 警告: Groq 提供商当前未启用 (enabled={enabled})")
    
    # 显示配置信息（部分隐藏 API Key）
    print("  ✓ Groq 提供商配置读取成功")
    print(f"    - ID: {provider.get('id')}")
    print(f"    - 名称: {provider.get('name')}")
    print(f"    - Base URL: {base_url}")
    if api_key:
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else f"{api_key[:6]}...{api_key[-2:]}"
        print(f"    - API Key: {masked_key}")
    print(f"    - 启用状态: {'启用' if enabled == 1 else '未启用'}")
    
    return provider


def download_test_audio():
    """下载测试音频文件"""
    print("\n" + "="*60)
    print("下载测试音频...")
    print("="*60)
    
    from app.downloaders.bilibili_downloader import BilibiliDownloader
    
    downloader = BilibiliDownloader()
    print(f"  正在下载视频: {TEST_VIDEO_URL}")
    
    try:
        audio_result = downloader.download(
            video_url=TEST_VIDEO_URL,
            quality="fast",
            need_video=False
        )
        audio_path = audio_result.file_path
        
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path) / (1024 * 1024)
            print(f"  ✓ 音频下载成功")
            print(f"    - 文件路径: {audio_path}")
            print(f"    - 文件大小: {file_size:.2f} MB")
            print(f"    - 视频标题: {audio_result.title}")
            print(f"    - 时长: {audio_result.duration:.2f} 秒")
            return audio_path
        else:
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
    except Exception as e:
        print(f"  ✗ 音频下载失败: {e}")
        raise


def test_groq_transcriber(audio_file: str):
    """测试 Groq 转写器"""
    print("\n" + "="*60)
    print("测试 Groq 转写器...")
    print("="*60)
    
    # 设置环境变量
    os.environ["TRANSCRIBER_TYPE"] = "groq"
    if not os.getenv("GROQ_TRANSCRIBER_MODEL"):
        os.environ["GROQ_TRANSCRIBER_MODEL"] = "whisper-large-v3"
    
    # 获取转写器实例
    print("  初始化转写器...")
    transcriber = get_transcriber(transcriber_type="groq")
    print(f"  ✓ 转写器初始化成功: {type(transcriber).__name__}")
    
    # 检查音频文件
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")
    
    file_size = os.path.getsize(audio_file) / (1024 * 1024)
    print(f"  ✓ 音频文件检查通过")
    print(f"    - 文件路径: {audio_file}")
    print(f"    - 文件大小: {file_size:.2f} MB")
    
    # 执行转写
    print("\n  开始转写音频...")
    try:
        result = transcriber.transcript(file_path=audio_file)
        
        # 显示结果
        print("\n  " + "="*56)
        print("  ✓ 转写成功！")
        print("  " + "="*56)
        print(f"\n  检测语言: {result.language}")
        print(f"  总文本长度: {len(result.full_text)} 字符")
        print(f"  分段数量: {len(result.segments)} 个")
        
        # 显示完整文本（前500字符）
        print("\n  完整文本（前500字符）:")
        print("  " + "-"*56)
        preview_text = result.full_text[:500]
        print(f"  {preview_text}")
        if len(result.full_text) > 500:
            print(f"  ... (还有 {len(result.full_text) - 500} 个字符)")
        print("  " + "-"*56)
        
        # 显示前3个分段
        if result.segments:
            print("\n  前3个分段:")
            print("  " + "-"*56)
            for i, seg in enumerate(result.segments[:3], 1):
                print(f"  [{i}] [{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}")
            print("  " + "-"*56)
        
        return result
        
    except Exception as e:
        print(f"\n  ✗ 转写失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Groq 转写器功能测试")
    print("="*60)
    
    try:
        # 1. 初始化数据库
        print("\n[1/4] 初始化数据库...")
        init_db()
        seed_default_providers()
        print("  ✓ 数据库初始化完成")
        
        # 2. 配置 Groq 提供商
        print("\n[2/4] 配置 Groq 提供商...")
        setup_groq_provider()
        
        # 3. 准备测试音频文件
        print("\n[3/4] 准备测试音频文件...")
        if TEST_AUDIO_FILE and os.path.exists(TEST_AUDIO_FILE):
            audio_file = TEST_AUDIO_FILE
            print(f"  ✓ 使用指定的音频文件: {audio_file}")
        else:
            if TEST_AUDIO_FILE:
                raise FileNotFoundError(f"指定的音频文件不存在: {TEST_AUDIO_FILE}")
            audio_file = download_test_audio()
        
        # 4. 测试转写功能
        print("\n[4/4] 测试转写功能...")
        result = test_groq_transcriber(audio_file)
        
        # 总结
        print("\n" + "="*60)
        print("✓ 所有测试完成！")
        print("="*60)
        print(f"\n转写结果统计:")
        print(f"  - 语言: {result.language}")
        print(f"  - 文本长度: {len(result.full_text)} 字符")
        print(f"  - 分段数量: {len(result.segments)} 个")
        if result.segments:
            total_duration = result.segments[-1].end
            print(f"  - 总时长: {total_duration:.2f} 秒")
        
        return result
        
    except Exception as e:
        print("\n" + "="*60)
        print("✗ 测试失败")
        print("="*60)
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()

