"""
Google Custom Search API 快速配置脚本
用于设置 Custom Search Engine ID (CX)
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

def setup_google_search():
    """设置 Google Custom Search API 配置"""
    print("=" * 60)
    print("Google Custom Search API 配置向导")
    print("=" * 60)
    print()
    
    # 查找 .env 文件
    python_dir = Path(__file__).parent
    env_file = python_dir / ".env"
    
    # 如果 .env 文件不存在，创建一个
    if not env_file.exists():
        print(f"创建 .env 文件: {env_file}")
        env_file.touch()
    
    # 加载现有环境变量
    load_dotenv(env_file)
    
    # 显示当前配置
    current_api_key = os.getenv("GOOGLE_API_KEY", "")
    current_cx = os.getenv("GOOGLE_CX", "")
    
    print("当前配置：")
    if current_api_key:
        print(f"  [OK] GOOGLE_API_KEY: {current_api_key[:20]}...")
    else:
        print(f"  [X] GOOGLE_API_KEY: 未配置")
    
    if current_cx:
        print(f"  [OK] GOOGLE_CX: {current_cx}")
    else:
        print(f"  [X] GOOGLE_CX: 未配置")
    print()
    
    # 如果 CX 已配置，询问是否要更新
    if current_cx:
        update = input("CX 已配置，是否要更新？(y/n): ").strip().lower()
        if update != 'y':
            print("保持当前配置不变。")
            return
    
    # 获取新的 CX
    print()
    print("请按照以下步骤获取 Custom Search Engine ID (CX)：")
    print("1. 访问 https://programmablesearchengine.google.com/")
    print("2. 创建或选择一个搜索引擎")
    print("3. 在控制面板中找到 '搜索引擎 ID' 或 'Search engine ID'")
    print("4. 复制该 ID（格式类似：017576662512468239146:omuauf_lfve）")
    print()
    
    new_cx = input("请输入 Custom Search Engine ID (CX): ").strip()
    
    if not new_cx:
        print("未输入 CX，取消配置。")
        return
    
    # 确保 API Key 已配置
    if not current_api_key:
        print()
        print("检测到 API Key 未配置。")
        api_key = input("请输入 Google API Key (或按 Enter 使用默认值): ").strip()
        if api_key:
            set_key(env_file, "GOOGLE_API_KEY", api_key)
            print(f"[OK] 已设置 GOOGLE_API_KEY")
        else:
            # 使用默认值
            default_key = "AIzaSyAAFi02nzkteEEKCSsL4s3UG1niJHsi1yQ"
            set_key(env_file, "GOOGLE_API_KEY", default_key)
            print(f"[OK] 已设置默认 GOOGLE_API_KEY")
    
    # 设置 CX
    set_key(env_file, "GOOGLE_CX", new_cx)
    print(f"[OK] 已设置 GOOGLE_CX: {new_cx}")
    print()
    
    # 验证配置
    print("=" * 60)
    print("配置完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 运行测试脚本验证配置：")
    print("   python agent/tests/测试视频url搜索节点.py")
    print()
    print("2. 如果遇到问题，请检查：")
    print("   - CX 是否正确")
    print("   - API Key 是否有效")
    print("   - 是否已启用 Custom Search JSON API")
    print()

if __name__ == "__main__":
    try:
        setup_google_search()
    except KeyboardInterrupt:
        print("\n\n配置已取消。")
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

