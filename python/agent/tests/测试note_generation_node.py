"""
测试 note_generation_node
手动提供多个视频 URL 和单个平台，测试并发生成多个笔记

测试说明：
1. 确保数据库中已配置好 qwen 提供商和 qwen-max 模型
2. 手动指定多个视频 URL（所有视频使用同一个平台）
3. 测试 note_generation_node 是否能并发生成多个笔记

运行方式：
   方式1：从项目根目录运行（推荐）
   python backend/agent/tests/测试note_generation_node.py
   
   方式2：从 backend 目录运行
   cd backend
   python agent/tests/测试note_generation_node.py
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
from app.transcriber.transcriber_provider import get_transcriber
from graphs.node.note_generation_node import note_generation_node
from graphs.state import AIState
from sqlalchemy import text

# 测试配置
TEST_MODEL_NAME = "qwen-max"
TEST_PROVIDER_ID = "qwen"
TEST_PLATFORM = "bilibili"  # 所有视频使用同一个平台

# Groq 配置（如果需要使用 Groq 转录器）
GROQ_API_KEY = "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"  # 替换为实际的 Groq API Key
USE_GROQ_TRANSCRIBER = True  # 设置为 True 使用 Groq，False 使用 Whisper

# 手动指定的多个视频 URL（可以根据需要修改）
TEST_VIDEO_URLS = [
    "https://www.bilibili.com/video/BV1QgsAzzEwY",  
    "https://www.bilibili.com/video/BV1An2SYiEQY",
    "https://www.bilibili.com/video/BV1T64y1A7vK",
]


def setup_database_config():
    """
    设置数据库配置：确保 qwen 提供商和 qwen-max 模型存在
    如果 USE_GROQ_TRANSCRIBER=True，还会配置 Groq 提供商
    """
    print("\n[设置] 设置数据库配置...")
    
    db = next(get_db())
    try:
        # 0. 如果使用 Groq 转录器，配置 Groq 提供商
        if USE_GROQ_TRANSCRIBER:
            groq_provider = db.query(Provider).filter_by(id="groq").first()
            if not groq_provider:
                print(f"  添加 Groq 提供商...")
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
                    print(f"  ✓ Groq 提供商添加成功")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "unique constraint" in error_msg or "already exists" in error_msg:
                        print(f"  ✓ Groq 提供商已存在")
                    else:
                        print(f"  ⚠ 添加 Groq 提供商时出错: {e}")
                        raise
            else:
                print(f"  ✓ Groq 提供商已存在")
                # 更新 API Key（如果需要）
                if groq_provider.api_key != GROQ_API_KEY:
                    groq_provider.api_key = GROQ_API_KEY
                    db.commit()
                    print(f"  ✓ Groq API Key 已更新")
        
        # 1. 检查并添加/更新提供商
        existing_provider = db.query(Provider).filter_by(id=TEST_PROVIDER_ID).first()
        
        if not existing_provider:
            print(f"  添加提供商: {TEST_PROVIDER_ID}")
            try:
                insert_provider(
                    id=TEST_PROVIDER_ID,
                    name="Qwen",
                    api_key="sk-c61481ce440445db9dc8b12298f7aecb",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    logo="qwen",
                    type_="qwen",
                    enabled=1
                )
                print(f"  ✓ 提供商 '{TEST_PROVIDER_ID}' 添加成功")
            except Exception as e:
                error_msg = str(e).lower()
                if "unique constraint" in error_msg or "already exists" in error_msg:
                    print(f"  ✓ 提供商 '{TEST_PROVIDER_ID}' 已存在")
                else:
                    print(f"  ⚠ 添加提供商时出错: {e}")
                    raise
        else:
            print(f"  ✓ 提供商 '{TEST_PROVIDER_ID}' 已存在")
            
            # 更新配置（确保 API Key 和 base_url 正确）
            updated = False
            if existing_provider.api_key != "sk-c61481ce440445db9dc8b12298f7aecb":
                existing_provider.api_key = "sk-c61481ce440445db9dc8b12298f7aecb"
                updated = True
            if existing_provider.base_url != "https://dashscope.aliyuncs.com/compatible-mode/v1":
                existing_provider.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                updated = True
            if existing_provider.enabled != 1:
                existing_provider.enabled = 1
                updated = True
            if updated:
                db.commit()
                print(f"  ✓ 提供商配置已更新")
        
        # 2. 检查模型是否存在（通过 model_name 查找）
        existing_model = db.execute(
            text("SELECT * FROM models WHERE model_name = :model_name"),
            {"model_name": TEST_MODEL_NAME}
        ).first()
        
        if not existing_model:
            print(f"  添加模型: {TEST_MODEL_NAME}")
            try:
                db.execute(
                    text("INSERT INTO models (provider_id, model_name) VALUES (0, :model_name)"),
                    {"model_name": TEST_MODEL_NAME}
                )
                db.commit()
                print(f"  ✓ 模型 '{TEST_MODEL_NAME}' 添加成功")
            except Exception as e:
                error_msg = str(e).lower()
                if "unique constraint" in error_msg:
                    print(f"  ✓ 模型 '{TEST_MODEL_NAME}' 已存在")
                else:
                    print(f"  ⚠ 添加模型时出错: {e}")
        else:
            print(f"  ✓ 模型 '{TEST_MODEL_NAME}' 已存在")
            
        print("✓ 数据库配置设置完成")
        
    except Exception as e:
        print(f"  ✗ 设置数据库配置时出错: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def setup_environment():
    """
    初始化环境和数据库
    """
    print("=" * 60)
    print("初始化环境...")
    print("=" * 60)
    
    # 1. 初始化数据库（创建表）
    print("\n[1/3] 初始化数据库...")
    try:
        init_db()
        print("✓ 数据库初始化成功")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        raise
    
    # 2. 种子化默认提供商（如果数据库为空）
    print("\n[2/3] 种子化默认提供商...")
    try:
        seed_default_providers()
        print("✓ 默认提供商种子化完成（如果数据库为空）")
    except Exception as e:
        print(f"⚠ 种子化提供商时出错（可能已经存在）: {e}")
    
    # 3. 设置数据库配置
    print("\n[3/3] 设置数据库配置...")
    setup_database_config()
    
    # 初始化转录器
    print("\n[4/4] 初始化转录器...")
    try:
        # 根据 USE_GROQ_TRANSCRIBER 设置转录器类型
        if USE_GROQ_TRANSCRIBER:
            transcriber_type = "groq"
            os.environ["TRANSCRIBER_TYPE"] = "groq"
            # 可选：设置 Groq 转录模型
            if not os.getenv("GROQ_TRANSCRIBER_MODEL"):
                os.environ["GROQ_TRANSCRIBER_MODEL"] = "whisper-large-v3"
            print(f"  使用 Groq 转录器")
            print(f"  模型: {os.getenv('GROQ_TRANSCRIBER_MODEL', 'whisper-large-v3')}")
        else:
            transcriber_type = os.getenv("TRANSCRIBER_TYPE", "fast-whisper")
            print(f"  使用 Whisper 转录器 (类型: {transcriber_type})")
        
        get_transcriber(transcriber_type=transcriber_type)
        print(f"✓ 转录器初始化成功")
    except Exception as e:
        print(f"✗ 转录器初始化失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("环境初始化完成")
    print("=" * 60 + "\n")


def create_test_video_urls() -> list:
    """
    创建测试用的视频 URL 列表
    
    返回格式: [{"url": str, "platform": str, "title": str}, ...]
    """
    video_urls = []
    for i, url in enumerate(TEST_VIDEO_URLS, 1):
        video_urls.append({
            "url": url,
            "platform": TEST_PLATFORM,
            "title": f"测试视频 {i}"  # 标题会在实际下载时被替换为真实标题
        })
    return video_urls


async def test_note_generation_node():
    """
    测试 note_generation_node
    """
    print("=" * 60)
    print("开始测试 note_generation_node")
    print("=" * 60)
    
    # 创建测试用的视频 URL 列表
    video_urls = create_test_video_urls()
    
    print(f"\n【测试参数】")
    print(f"  视频数量: {len(video_urls)}")
    print(f"  平台: {TEST_PLATFORM}")
    print(f"  模型名称: {TEST_MODEL_NAME}")
    print(f"  提供商ID: {TEST_PROVIDER_ID}")
    print(f"\n【视频列表】")
    for i, video in enumerate(video_urls, 1):
        print(f"  {i}. {video['url']}")
    
    # 创建测试用的 state
    test_state: AIState = {
        "question": "测试多视频笔记生成",
        "user_id": 1,
        "session_id": "test_note_generation_session",
        "timestamp": None,
        "history": [],
        "answer": None,
        "video_urls": video_urls,  # 手动提供的视频 URL 列表
        "search_query": None,
        "note_results": [],
        "model_name": TEST_MODEL_NAME,  # 明确指定模型配置
        "provider_id": TEST_PROVIDER_ID,  # 明确指定提供商配置
        "note_generation_status": None,
        "summary_result": None,
        "metadata": None,
    }
    
    print(f"\n【开始生成笔记】")
    print("  这可能需要较长时间，请耐心等待...")
    print("  流程：并发下载视频 → 提取音频 → 转录 → GPT 生成笔记\n")
    
    try:
        # 调用 note_generation_node
        result_state = await note_generation_node(test_state)
        
        # 获取结果
        note_results = result_state.get("note_results", [])
        
        print("\n" + "=" * 60)
        print("笔记生成完成！")
        print("=" * 60)
        
        print(f"\n【生成结果统计】")
        print(f"  成功生成笔记数: {len(note_results)}")
        print(f"  预期笔记数: {len(video_urls)}")
        
        if len(note_results) != len(video_urls):
            print(f"  ⚠ 警告：生成的笔记数量与预期不符")
        
        # 显示每个视频的笔记
        print(f"\n【笔记详情】")
        for i, note in enumerate(note_results, 1):
            print(f"\n--- 笔记 {i} ---")
            print(f"  标题: {note.get('title', '未知标题')}")
            print(f"  平台: {note.get('platform', '未知平台')}")
            print(f"  URL: {note.get('url', '未知链接')}")
            
            # 音频元信息
            audio_meta = note.get('audio_meta', {})
            if audio_meta:
                print(f"  时长: {audio_meta.get('duration', 0):.2f} 秒")
                print(f"  视频ID: {audio_meta.get('video_id', '未知')}")
            
            # 转录信息
            transcript = note.get('transcript', {})
            if transcript:
                full_text = transcript.get('full_text', '')
                print(f"  转录文本长度: {len(full_text)} 字符")
                if full_text:
                    preview = full_text[:100]
                    print(f"  转录预览: {preview}...")
            
            # 笔记内容
            markdown = note.get('markdown', '')
            if markdown:
                print(f"  笔记长度: {len(markdown)} 字符")
                print(f"  笔记预览:")
                # 显示前 200 个字符
                preview = markdown[:200]
                print(f"    {preview}...")
            else:
                print(f"  ⚠ 警告：笔记内容为空")
        
        # 保存完整的笔记到文件（可选）
        print(f"\n【保存结果】")
        output_dir = Path("note_results")
        output_dir.mkdir(exist_ok=True)
        
        import json
        output_file = output_dir / "note_generation_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(note_results, f, ensure_ascii=False, indent=2)
        print(f"  完整结果已保存到: {output_file}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        return result_state
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """
    主函数
    """
    try:
        # 初始化环境
        setup_environment()
        
        # 运行测试
        result = await test_note_generation_node()
        
        if result:
            print("\n✅ 测试通过！")
            return 0
        else:
            print("\n❌ 测试失败")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
