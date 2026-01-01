"""
调试 API Key 配置问题

用于检查 API Key 是否正确从数据库读取和传递
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# 添加 agent 目录到路径
agent_path = Path(__file__).parent.parent
sys.path.insert(0, str(agent_path))

# 设置工作目录
os.chdir(backend_path)

from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers, get_provider_by_id, get_all_providers
from agent.utils.config_helper import get_default_model_config
from app.services.provider import ProviderService

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def debug_api_key():
    """调试 API Key 配置"""
    print_section("调试 API Key 配置")
    
    # 初始化数据库
    init_db()
    seed_default_providers()
    
    # 获取默认配置
    try:
        model_name, provider_id = get_default_model_config()
        print(f"默认模型: {model_name}")
        print(f"默认提供商ID: {provider_id}")
    except Exception as e:
        print(f"✗ 获取默认配置失败: {e}")
        return
    
    # 方法1：通过 ProviderService 获取
    print("\n--- 方法1: 通过 ProviderService 获取 ---")
    try:
        provider1 = ProviderService.get_provider_by_id(provider_id)
        if provider1:
            api_key1 = provider1.get("api_key", "")
            print(f"✓ 提供商名称: {provider1.get('name', 'N/A')}")
            print(f"✓ API Key 长度: {len(api_key1) if api_key1 else 0}")
            print(f"✓ API Key 前10字符: {api_key1[:10] if api_key1 else '(空)'}...")
            print(f"✓ API Key 是否为空: {not api_key1 or api_key1.strip() == ''}")
            print(f"✓ Base URL: {provider1.get('base_url', 'N/A')}")
            
            # 检查是否是占位符
            placeholder_keys = ['your_api_key_here', 'your_deepseek_api_key_here', 
                               'your_qwen_api_key_here', 'your_openai_api_key_here', '']
            if api_key1.lower() in placeholder_keys:
                print(f"⚠ API Key 是占位符: {api_key1}")
            else:
                print(f"✓ API Key 看起来是有效的")
        else:
            print(f"✗ 未找到提供商: {provider_id}")
    except Exception as e:
        print(f"✗ 获取提供商失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 方法2：通过 provider_dao 直接获取（返回 Provider 对象，不是字典）
    print("\n--- 方法2: 通过 provider_dao 直接获取 ---")
    try:
        provider2 = get_provider_by_id(provider_id)
        if provider2:
            # Provider 是 SQLAlchemy 对象，使用属性访问，不是 .get()
            api_key2 = provider2.api_key if hasattr(provider2, 'api_key') else ""
            print(f"✓ 提供商名称: {provider2.name if hasattr(provider2, 'name') else 'N/A'}")
            print(f"✓ API Key 长度: {len(api_key2) if api_key2 else 0}")
            print(f"✓ API Key 前10字符: {api_key2[:10] if api_key2 else '(空)'}...")
            print(f"✓ API Key 是否为空: {not api_key2 or api_key2.strip() == ''}")
        else:
            print(f"✗ 未找到提供商: {provider_id}")
    except Exception as e:
        print(f"✗ 获取提供商失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 列出所有提供商（返回 Provider 对象列表）
    print("\n--- 所有提供商列表 ---")
    try:
        all_providers = get_all_providers()
        for p in all_providers:
            # Provider 是 SQLAlchemy 对象，使用属性访问
            api_key = p.api_key if hasattr(p, 'api_key') else ""
            print(f"\n提供商: {p.name if hasattr(p, 'name') else 'N/A'} (ID: {p.id if hasattr(p, 'id') else 'N/A'})")
            print(f"  API Key 长度: {len(api_key) if api_key else 0}")
            print(f"  API Key 前10字符: {api_key[:10] if api_key else '(空)'}...")
            print(f"  Base URL: {p.base_url if hasattr(p, 'base_url') else 'N/A'}")
            print(f"  是否启用: {p.enabled if hasattr(p, 'enabled') else 0}")
    except Exception as e:
        print(f"✗ 获取所有提供商失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试创建 OpenAI 客户端
    print("\n--- 测试创建 OpenAI 客户端 ---")
    try:
        provider = ProviderService.get_provider_by_id(provider_id)
        if provider:
            api_key = provider.get("api_key", "")
            base_url = provider.get("base_url", "")
            
            print(f"API Key 值: {repr(api_key)}")  # 使用 repr 显示实际值
            print(f"API Key 类型: {type(api_key)}")
            print(f"Base URL: {base_url}")
            
            if not api_key or api_key.strip() == "":
                print("✗ API Key 为空，无法创建客户端")
            else:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    print("✓ OpenAI 客户端创建成功")
                    
                    # 尝试列出模型（这会触发实际的 API 调用）
                    print("正在测试 API 连接...")
                    models = client.models.list()
                    print(f"✓ API 连接成功，找到 {len(list(models))} 个模型")
                except Exception as e:
                    print(f"✗ 创建或测试 OpenAI 客户端失败: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"✗ 未找到提供商: {provider_id}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_api_key()

