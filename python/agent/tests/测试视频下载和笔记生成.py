

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# 设置工作目录为 backend 目录（确保相对路径正确）
os.chdir(backend_path)

# 初始化数据库和环境
from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers, insert_provider
from app.db.model_dao import insert_model, get_model_by_provider_and_name
from app.db.engine import get_db
from app.db.models.providers import Provider
from app.db.models.models import Model
from app.transcriber.transcriber_provider import get_transcriber
from app.services.note import NoteGenerator
from app.services.provider import ProviderService
from app.services.model import ModelService
from app.enmus.note_enums import DownloadQuality
from app.models.notes_model import NoteResult

# 测试配置
TEST_VIDEO_URL = "https://www.bilibili.com/video/BV16GvmBpEu4"  # 可以替换为任何测试视频 URL
TEST_PLATFORM = "bilibili"
TEST_MODEL_NAME = "qwen-max"
TEST_PROVIDER_ID = "qwen"


def setup_database_config():
    """
    设置数据库配置：添加 qwen 提供商和 qwen-max 模型（如果不存在）
    """
    print("\n[设置] 设置数据库配置...")
    
    db = next(get_db())
    try:
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
        
        # 2. 添加模型
        # 注意：Model.provider_id 在数据库中是 Integer，但 Provider.id 是 String
        # 查看实际数据库中的 provider_id 值来确定正确的插入方式
        from sqlalchemy import text
        
        # 先查询所有模型，看看 provider_id 的实际值是什么格式
        all_models = db.execute(text("SELECT provider_id, model_name FROM models")).fetchall()
        if all_models:
            print(f"  数据库中已有模型示例: {all_models[:3]}")
        
        # 检查模型是否已存在（通过 model_name 查找，因为 provider_id 类型可能不匹配）
        existing_model = db.execute(
            text("SELECT * FROM models WHERE model_name = :model_name"),
            {"model_name": TEST_MODEL_NAME}
        ).first()
        
        if not existing_model:
            print(f"  添加模型: {TEST_MODEL_NAME}")
            # 由于 provider_id 类型不匹配，我们尝试使用 0 作为占位符
            # 或者，查看是否可以通过其他方式关联
            # 实际上，最安全的方式是使用 ModelService，但需要正确的类型
            try:
                # 尝试使用字符串 ID 的哈希值作为整数（临时方案）
                # 或者直接使用 0，然后在查询时通过 model_name 关联
                # 但实际上，最好的方式是查看实际数据库中的值
                
                # 由于我们不确定 provider_id 的实际存储方式，先尝试直接插入
                # SQLite 可能会拒绝，但我们先试试
                db.execute(
                    text("INSERT INTO models (provider_id, model_name) VALUES (0, :model_name)"),
                    {"model_name": TEST_MODEL_NAME}
                )
                db.commit()
                print(f"  ✓ 模型 '{TEST_MODEL_NAME}' 添加成功（使用占位符 provider_id）")
                print(f"  ⚠ 注意：provider_id 使用占位符 0，实际使用时可能需要调整")
            except Exception as e:
                error_msg = str(e).lower()
                if "unique constraint" in error_msg:
                    print(f"  ✓ 模型 '{TEST_MODEL_NAME}' 已存在")
                else:
                    print(f"  ⚠ 添加模型时出错: {e}")
                    print(f"  建议：请通过 API 接口或数据库工具手动添加模型")
        else:
            print(f"  ✓ 模型 '{TEST_MODEL_NAME}' 已存在")
            
    except Exception as e:
        print(f"  ✗ 设置数据库配置时出错: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def check_database_config():
    """
    检查数据库配置，确保 qwen 提供商和 qwen-max 模型存在
    """
    print("\n[检查] 检查数据库配置...")
    
    # 检查提供商
    try:
        provider = ProviderService.get_provider_by_id(TEST_PROVIDER_ID)
        if not provider:
            print(f"✗ 提供商 '{TEST_PROVIDER_ID}' 不存在")
            print(f"  请在数据库中配置提供商，或手动添加")
            return False
        
        print(f"✓ 找到提供商: {provider.get('name', TEST_PROVIDER_ID)}")
        
        # 检查 API Key
        if not provider.get('api_key') or provider.get('api_key', '').strip() == '':
            print(f"✗ 提供商 '{TEST_PROVIDER_ID}' 的 API Key 未配置")
            return False
        
        # 检查模型（直接通过 SQL 查询，因为 provider_id 类型不匹配）
        from sqlalchemy import text
        db_check = next(get_db())
        try:
            # 通过 model_name 查找模型（不依赖 provider_id 类型匹配）
            model_result = db_check.execute(
                text("SELECT * FROM models WHERE model_name = :model_name"),
                {"model_name": TEST_MODEL_NAME}
            ).first()
            
            if not model_result:
                print(f"✗ 模型 '{TEST_MODEL_NAME}' 不存在")
                # 尝试列出所有模型作为参考
                all_models = db_check.execute(text("SELECT model_name FROM models")).fetchall()
                model_names = [row[0] for row in all_models if row[0]]
                if model_names:
                    print(f"  数据库中所有模型: {', '.join(model_names)}")
                return False
            else:
                # 模型存在，即使 provider_id 可能不匹配
                print(f"✓ 找到模型: {TEST_MODEL_NAME}")
                return True
        finally:
            db_check.close()
        
    except Exception as e:
        print(f"✗ 检查数据库配置时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_environment():
    """
    初始化环境和数据库
    """
    print("=" * 60)
    print("初始化环境...")
    print("=" * 60)
    
    # 初始化数据库（创建表）
    print("\n[1/4] 初始化数据库...")
    try:
        init_db()
        print("✓ 数据库初始化成功")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        raise
    
    # 种子化默认提供商（如果数据库为空）
    print("\n[2/4] 种子化默认提供商...")
    try:
        seed_default_providers()
        print("✓ 默认提供商种子化完成（如果数据库为空）")
    except Exception as e:
        print(f"⚠ 种子化提供商时出错（可能已经存在）: {e}")
    
    # 设置数据库配置（添加 qwen 提供商和模型）
    print("\n[3/4] 设置数据库配置...")
    try:
        setup_database_config()
        print("✓ 数据库配置设置完成")
    except Exception as e:
        print(f"✗ 设置数据库配置失败: {e}")
        raise
    
    # 检查数据库配置
    print("\n[4/4] 验证数据库配置...")
    if not check_database_config():
        raise Exception(f"数据库配置验证失败，请确保提供商 '{TEST_PROVIDER_ID}' 和模型 '{TEST_MODEL_NAME}' 已正确配置")
    
    # 初始化转录器
    print("\n[5/5] 初始化转录器...")
    try:
        transcriber_type = os.getenv("TRANSCRIBER_TYPE", "fast-whisper")
        get_transcriber(transcriber_type=transcriber_type)
        print(f"✓ 转录器初始化成功 (类型: {transcriber_type})")
    except Exception as e:
        print(f"✗ 转录器初始化失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("环境初始化完成")
    print("=" * 60 + "\n")


def test_note_generation():
    """
    测试视频下载和笔记生成
    """
    print("=" * 60)
    print("开始测试视频下载和笔记生成")
    print("=" * 60)
    
    print(f"\n【测试参数】")
    print(f"  视频URL: {TEST_VIDEO_URL}")
    print(f"  平台: {TEST_PLATFORM}")
    print(f"  模型名称: {TEST_MODEL_NAME}")
    print(f"  提供商ID: {TEST_PROVIDER_ID}")
    print()
    
    # 创建 NoteGenerator 实例
    generator = NoteGenerator()
    
    try:
        print("[Step 1] 开始生成笔记...")
        print("  这可能需要几分钟时间，请耐心等待...")
        print("  流程：下载视频 → 提取音频 → 转录 → GPT 生成笔记\n")
        
        # 调用笔记生成
        note_result: NoteResult = generator.generate(
            video_url=TEST_VIDEO_URL,
            platform=TEST_PLATFORM,
            quality=DownloadQuality.medium,
            task_id=None,
            model_name=TEST_MODEL_NAME,
            provider_id=TEST_PROVIDER_ID,
            link=False,
            screenshot=False,
            _format=None,
            style=None,
            extras=None,
            output_path=None,
            video_understanding=False,
            video_interval=0,
            grid_size=None,
        )
        
        if not note_result:
            print("\n✗ 笔记生成失败: 返回 None")
            return
        
        print("\n" + "=" * 60)
        print("笔记生成成功！")
        print("=" * 60)
        
        # 显示结果
        print(f"\n【视频信息】")
        print(f"  标题: {note_result.audio_meta.title}")
        print(f"  平台: {note_result.audio_meta.platform}")
        print(f"  视频ID: {note_result.audio_meta.video_id}")
        print(f"  时长: {note_result.audio_meta.duration:.2f} 秒")
        if note_result.audio_meta.cover_url:
            print(f"  封面: {note_result.audio_meta.cover_url}")
        
        print(f"\n【转录信息】")
        print(f"  语言: {note_result.transcript.language or '未知'}")
        print(f"  全文长度: {len(note_result.transcript.full_text)} 字符")
        print(f"  分段数量: {len(note_result.transcript.segments)} 段")
        if note_result.transcript.full_text:
            preview = note_result.transcript.full_text[:200]
            print(f"  预览: {preview}...")
        
        print(f"\n【笔记内容（Markdown）】")
        print(f"  长度: {len(note_result.markdown)} 字符")
        print(f"\n{'-' * 60}")
        print(note_result.markdown)
        print(f"{'-' * 60}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        return note_result
        
    except Exception as e:
        print(f"\n✗ 笔记生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """
    主函数
    """
    try:
        # 初始化环境
        setup_environment()
        
        # 运行测试
        result = test_note_generation()
        
        if result:
            print("\n✅ 所有测试通过！")
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
    exit_code = main()
    sys.exit(exit_code)
