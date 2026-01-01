"""
测试API路由认证功能

测试说明：
1. 测试用户注册API
2. 测试用户登录API（OAuth2和JSON格式）
3. 测试获取当前用户信息API
4. 测试对话管理API（需要认证）

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/测试API路由认证.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/测试API路由认证.py

注意：此测试需要FastAPI应用运行，可以通过以下方式启动：
   cd python
   uvicorn app:app --reload --port 8483
"""

import sys
import os
import requests
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# 设置工作目录
os.chdir(backend_path)

# API基础URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8483")


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def test_api_register():
    """测试用户注册API"""
    print_section("测试1: 用户注册API")
    
    import time
    username = f"test_api_{int(time.time())}"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "username": username,
                "password": "test_password_123",
                "phone_number": None,
                "avatar": None
            },
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            if data.get("access_token"):
                print(f"✓ 注册成功，获得token")
                return data.get("access_token"), username
            else:
                print(f"⚠ 注册成功但未返回token")
                return None, username
        else:
            print(f"⚠ 注册失败: {response.json()}")
            return None, username
            
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到API服务器: {API_BASE_URL}")
        print(f"  请确保FastAPI应用正在运行")
        return None, None
    except Exception as e:
        print(f"✗ 注册测试失败: {e}")
        return None, None


def test_api_login_oauth2():
    """测试OAuth2格式登录API"""
    print_section("测试2: OAuth2格式登录API")
    
    try:
        # 先注册一个用户
        token, username = test_api_register()
        if not token:
            print("⚠ 跳过登录测试（注册失败）")
            return None
        
        # 使用OAuth2格式登录
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            data={
                "username": username,
                "password": "test_password_123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            if data.get("access_token"):
                print(f"✓ OAuth2登录成功")
                return data.get("access_token")
            else:
                print(f"⚠ 登录成功但未返回token")
                return None
        else:
            print(f"⚠ 登录失败: {response.json()}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到API服务器")
        return None
    except Exception as e:
        print(f"✗ 登录测试失败: {e}")
        return None


def test_api_login_json():
    """测试JSON格式登录API"""
    print_section("测试3: JSON格式登录API")
    
    try:
        import time
        username = f"test_json_{int(time.time())}"
        
        # 先注册
        register_response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "username": username,
                "password": "test_password_123"
            },
            timeout=10
        )
        
        if register_response.status_code != 200:
            print("⚠ 注册失败，跳过登录测试")
            return None
        
        # 使用JSON格式登录
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login_json",
            json={
                "username": username,
                "password": "test_password_123"
            },
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            if data.get("access_token"):
                print(f"✓ JSON登录成功")
                return data.get("access_token")
            else:
                print(f"⚠ 登录成功但未返回token")
                return None
        else:
            print(f"⚠ 登录失败: {response.json()}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到API服务器")
        return None
    except Exception as e:
        print(f"✗ 登录测试失败: {e}")
        return None


def test_api_get_current_user(token: Optional[str]):
    """测试获取当前用户信息API"""
    print_section("测试4: 获取当前用户信息API")
    
    if not token:
        print("⚠ 跳过测试（没有token）")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            print(f"✓ 获取用户信息成功")
            print(f"  - 用户ID: {data.get('id')}")
            print(f"  - 用户名: {data.get('username')}")
            return True
        else:
            print(f"⚠ 获取用户信息失败: {response.json()}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_api_conversations(token: Optional[str]):
    """测试对话管理API（需要认证）"""
    print_section("测试5: 对话管理API")
    
    if not token:
        print("⚠ 跳过测试（没有token）")
        return False
    
    try:
        # 获取对话列表
        response = requests.get(
            f"{API_BASE_URL}/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            conversations = data.get("conversations", [])
            print(f"✓ 获取对话列表成功")
            print(f"  - 对话数量: {len(conversations)}")
            return True
        else:
            print(f"⚠ 获取对话列表失败: {response.json()}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_api_without_auth():
    """测试未认证访问受保护资源"""
    print_section("测试6: 未认证访问（应该失败）")
    
    try:
        # 尝试不提供token访问受保护资源
        response = requests.get(
            f"{API_BASE_URL}/api/auth/me",
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✓ 未认证访问被正确拒绝（401）")
            return True
        else:
            print(f"⚠ 预期401，但收到: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试API路由认证功能")
    print("="*60)
    print(f"\nAPI服务器地址: {API_BASE_URL}")
    print("注意：请确保FastAPI应用正在运行")
    print("启动命令: cd python && uvicorn app:app --reload --port 8483\n")
    
    try:
        # 测试注册
        token1, username = test_api_register()
        
        # 测试登录
        token2 = test_api_login_oauth2()
        token3 = test_api_login_json()
        
        # 使用token测试受保护资源
        token = token1 or token2 or token3
        if token:
            test_api_get_current_user(token)
            test_api_conversations(token)
        
        # 测试未认证访问
        test_api_without_auth()
        
        print_section("所有测试完成")
        print("注意：部分测试可能需要API服务器运行")
        print("如果看到连接错误，请先启动FastAPI应用")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return False
    except Exception as e:
        print(f"\n\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

