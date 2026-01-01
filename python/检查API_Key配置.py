"""
快速检查 API Key 配置

运行方式：
python python/检查API_Key配置.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

os.chdir(backend_path)

from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers, get_provider_by_id, get_all_providers
from agent.utils.config_helper import get_default_model_config
from app.services.provider import ProviderService

def main():
    print("\n" + "="*60)
    print("检查 API Key 配置")
    print("="*60 + "\n")
    
    # 初始化数据库
    init_db()
    seed_default_providers()
    
    # 获取默认配置
    try:
        model_name, provider_id = get_default_model_config()
        print(f"默认模型: {model_name}")
        print(f"默认提供商ID: {provider_id}\n")
    except Exception as e:
        print(f"✗ 获取默认配置失败: {e}\n")
        return
    
    # 获取提供商信息
    provider = ProviderService.get_provider_by_id(provider_id)
    if not provider:
        print(f"✗ 未找到提供商: {provider_id}")
        return
    
    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "")
    provider_name = provider.get("name", "N/A")
    
    print(f"提供商名称: {provider_name}")
    print(f"Base URL: {base_url}")
    print(f"API Key 长度: {len(api_key) if api_key else 0}")
    print(f"API Key 前10字符: {api_key[:10] if api_key and len(api_key) > 10 else '(空或太短)'}...")
    print(f"API Key 后10字符: ...{api_key[-10:] if api_key and len(api_key) > 10 else '(空或太短)'}")
    
    # 检查问题
    print("\n" + "-"*60)
    print("检查结果:")
    print("-"*60)
    
    if not api_key or api_key.strip() == "":
        print("✗ API Key 为空！")
        print("\n解决方法：")
        print("1. 通过 API 接口更新提供商：POST /api/update_provider")
        print("2. 或者直接在数据库中更新 providers 表的 api_key 字段")
        return
    
    placeholder_keys = ['your_api_key_here', 'your_deepseek_api_key_here', 
                       'your_qwen_api_key_here', 'your_openai_api_key_here']
    if api_key.lower() in placeholder_keys:
        print("✗ API Key 是占位符！")
        print(f"   当前值: {api_key}")
        print("\n解决方法：")
        print("1. 通过 API 接口更新提供商：POST /api/update_provider")
        print("2. 或者直接在数据库中更新 providers 表的 api_key 字段")
        return
    
    print("✓ API Key 看起来是有效的")
    
    # 尝试创建 OpenAI 客户端
    print("\n" + "-"*60)
    print("测试 API 连接:")
    print("-"*60)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        print("✓ OpenAI 客户端创建成功")
        
        # 尝试列出模型
        print("正在测试 API 连接...")
        models = client.models.list()
        model_list = list(models)
        print(f"✓ API 连接成功！")
        print(f"✓ 找到 {len(model_list)} 个可用模型")
        if model_list:
            print(f"  示例模型: {model_list[0].id if hasattr(model_list[0], 'id') else 'N/A'}")
    except Exception as e:
        print(f"✗ API 连接失败: {e}")
        print("\n可能的原因：")
        print("1. API Key 无效或已过期")
        print("2. Base URL 不正确")
        print("3. 网络连接问题")
        import traceback
        traceback.print_exc()
    
    # 列出所有提供商
    print("\n" + "-"*60)
    print("所有提供商列表:")
    print("-"*60)
    try:
        all_providers = get_all_providers()
        for p in all_providers:
            p_api_key = p.get("api_key", "")
            print(f"\n- {p.get('name', 'N/A')} (ID: {p.get('id', 'N/A')})")
            print(f"  API Key 长度: {len(p_api_key) if p_api_key else 0}")
            print(f"  Base URL: {p.get('base_url', 'N/A')}")
            print(f"  是否启用: {p.get('enabled', 0)}")
            if not p_api_key or p_api_key.strip() == "":
                print(f"  ⚠ API Key 为空")
            elif p_api_key.lower() in placeholder_keys:
                print(f"  ⚠ API Key 是占位符")
    except Exception as e:
        print(f"✗ 获取提供商列表失败: {e}")

if __name__ == "__main__":
    main()



