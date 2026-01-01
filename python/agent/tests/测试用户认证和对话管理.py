"""
测试用户认证和对话管理功能

测试说明：
1. 测试用户注册、登录、JWT token验证
2. 测试对话的创建、查询、更新、删除
3. 测试消息的创建和查询
4. 测试对话历史加载

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/测试用户认证和对话管理.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/测试用户认证和对话管理.py
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

# 设置工作目录为 backend 目录（确保相对路径正确）
os.chdir(backend_path)

# 初始化数据库
from app.db.init_db import init_db
from app.db.user_dao import (
    create_user,
    get_user_by_id,
    get_user_by_username,
    get_user_by_phone,
    verify_user_password,
    update_user_online_status
)
from app.db.conversation_dao import (
    create_conversation,
    get_conversations_by_user_id,
    get_conversation_by_id,
    update_conversation_title,
    delete_conversation
)
from app.db.message_dao import (
    create_message,
    get_messages_by_conversation_id,
    get_message_count_by_conversation_id
)
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_access_token
)

# 测试配置
TEST_USERNAME = "test_user_" + str(os.getpid())  # 使用进程ID确保唯一性
TEST_PASSWORD = "test_password_123"
TEST_PHONE = "13800138000"


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def test_user_creation():
    """测试用户创建"""
    print_section("测试1: 用户创建")
    
    try:
        # 创建用户
        user = create_user(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            phone_number=TEST_PHONE,
            avatar=None
        )
        
        print(f"✓ 用户创建成功")
        print(f"  - ID: {user.id}")
        print(f"  - 用户名: {user.username}")
        print(f"  - 手机号: {user.phone_number}")
        print(f"  - 在线状态: {user.is_online}")
        
        # 验证密码已加密
        assert user.password != TEST_PASSWORD, "密码应该被加密"
        assert user.password.startswith("$2b$"), "密码应该使用bcrypt加密"
        print(f"  - 密码已加密: {user.password[:20]}...")
        
        return user
        
    except ValueError as e:
        if "已存在" in str(e):
            print(f"⚠ 用户已存在，跳过创建")
            user = get_user_by_username(TEST_USERNAME)
            return user
        else:
            raise
    except Exception as e:
        print(f"✗ 用户创建失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_user_authentication():
    """测试用户认证"""
    print_section("测试2: 用户认证")
    
    try:
        # 获取用户
        user = get_user_by_username(TEST_USERNAME)
        if not user:
            print("⚠ 用户不存在，先创建用户")
            user = test_user_creation()
        
        # 测试密码验证
        is_valid = verify_user_password(user, TEST_PASSWORD)
        assert is_valid, "密码验证应该成功"
        print(f"✓ 密码验证成功")
        
        # 测试错误密码
        is_invalid = verify_user_password(user, "wrong_password")
        assert not is_invalid, "错误密码应该验证失败"
        print(f"✓ 错误密码验证失败（符合预期）")
        
        # 测试JWT token生成
        token = create_access_token(user.id)
        assert token, "Token应该被生成"
        print(f"✓ JWT token生成成功")
        print(f"  - Token: {token[:50]}...")
        
        # 测试JWT token验证
        user_id = verify_access_token(token)
        assert user_id == user.id, "Token验证应该返回正确的用户ID"
        print(f"✓ JWT token验证成功")
        print(f"  - 验证后的用户ID: {user_id}")
        
        # 测试无效token
        invalid_user_id = verify_access_token("invalid_token")
        assert invalid_user_id is None, "无效token应该返回None"
        print(f"✓ 无效token验证失败（符合预期）")
        
        return user, token
        
    except Exception as e:
        print(f"✗ 用户认证测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_conversation_management():
    """测试对话管理"""
    print_section("测试3: 对话管理")
    
    try:
        # 获取用户
        user = get_user_by_username(TEST_USERNAME)
        if not user:
            user = test_user_creation()
        
        # 创建对话
        conversation = create_conversation(user_id=user.id, title="测试对话")
        print(f"✓ 对话创建成功")
        print(f"  - 对话ID: {conversation.id}")
        print(f"  - 用户ID: {conversation.user_id}")
        print(f"  - 标题: {conversation.title}")
        
        # 查询对话
        retrieved = get_conversation_by_id(conversation.id)
        assert retrieved is not None, "应该能查询到对话"
        assert retrieved.id == conversation.id, "对话ID应该匹配"
        print(f"✓ 对话查询成功")
        
        # 更新对话标题
        new_title = "更新后的对话标题"
        success = update_conversation_title(conversation.id, new_title)
        assert success, "标题更新应该成功"
        
        updated = get_conversation_by_id(conversation.id)
        assert updated.title == new_title, "标题应该已更新"
        print(f"✓ 对话标题更新成功")
        print(f"  - 新标题: {updated.title}")
        
        # 获取用户的所有对话
        conversations = get_conversations_by_user_id(user.id, limit=10)
        assert len(conversations) > 0, "应该至少有一个对话"
        print(f"✓ 获取用户对话列表成功")
        print(f"  - 对话数量: {len(conversations)}")
        
        return conversation
        
    except Exception as e:
        print(f"✗ 对话管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_message_management():
    """测试消息管理"""
    print_section("测试4: 消息管理")
    
    try:
        # 获取用户和对话
        user = get_user_by_username(TEST_USERNAME)
        if not user:
            user = test_user_creation()
        
        conversation = create_conversation(user_id=user.id, title="消息测试对话")
        
        # 创建用户消息
        user_message = create_message(
            user_id=user.id,
            conversation_id=conversation.id,
            role="user",
            content="这是一条用户消息"
        )
        print(f"✓ 用户消息创建成功")
        print(f"  - 消息ID: {user_message.id}")
        print(f"  - 角色: {user_message.role}")
        print(f"  - 内容: {user_message.content[:50]}...")
        
        # 创建助手消息
        assistant_message = create_message(
            user_id=user.id,
            conversation_id=conversation.id,
            role="assistant",
            content="这是一条助手回复消息"
        )
        print(f"✓ 助手消息创建成功")
        print(f"  - 消息ID: {assistant_message.id}")
        print(f"  - 角色: {assistant_message.role}")
        
        # 查询对话的所有消息
        messages = get_messages_by_conversation_id(conversation.id)
        assert len(messages) == 2, "应该有两条消息"
        print(f"✓ 消息查询成功")
        print(f"  - 消息数量: {len(messages)}")
        
        # 验证消息顺序（应该按时间正序）
        assert messages[0].role == "user", "第一条消息应该是用户消息"
        assert messages[1].role == "assistant", "第二条消息应该是助手消息"
        print(f"✓ 消息顺序正确")
        
        # 测试消息数量统计
        count = get_message_count_by_conversation_id(conversation.id)
        assert count == 2, "消息数量应该为2"
        print(f"✓ 消息数量统计正确: {count}")
        
        return conversation
        
    except Exception as e:
        print(f"✗ 消息管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_conversation_cascade_delete():
    """测试对话级联删除"""
    print_section("测试5: 对话级联删除")
    
    try:
        # 获取用户
        user = get_user_by_username(TEST_USERNAME)
        if not user:
            user = test_user_creation()
        
        # 创建对话并添加消息
        conversation = create_conversation(user_id=user.id, title="待删除对话")
        
        # 添加多条消息
        for i in range(3):
            create_message(
                user_id=user.id,
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"消息 {i+1}"
            )
        
        # 验证消息存在
        messages_before = get_messages_by_conversation_id(conversation.id)
        assert len(messages_before) == 3, "应该有3条消息"
        print(f"✓ 删除前消息数量: {len(messages_before)}")
        
        # 删除对话
        success = delete_conversation(conversation.id)
        assert success, "对话删除应该成功"
        print(f"✓ 对话删除成功")
        
        # 验证对话已删除
        deleted = get_conversation_by_id(conversation.id)
        assert deleted is None, "对话应该已被删除"
        print(f"✓ 对话已从数据库删除")
        
        # 验证消息也被级联删除
        messages_after = get_messages_by_conversation_id(conversation.id)
        assert len(messages_after) == 0, "消息应该被级联删除"
        print(f"✓ 消息已级联删除（消息数量: {len(messages_after)}）")
        
    except Exception as e:
        print(f"✗ 级联删除测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_user_online_status():
    """测试用户在线状态"""
    print_section("测试6: 用户在线状态")
    
    try:
        # 获取用户
        user = get_user_by_username(TEST_USERNAME)
        if not user:
            user = test_user_creation()
        
        # 更新在线状态
        success = update_user_online_status(user.id, 1)
        assert success, "在线状态更新应该成功"
        
        updated_user = get_user_by_id(user.id)
        assert updated_user.is_online == 1, "用户应该是在线状态"
        print(f"✓ 用户在线状态更新成功")
        print(f"  - 在线状态: {updated_user.is_online}")
        
        # 更新为离线状态
        update_user_online_status(user.id, 0)
        updated_user = get_user_by_id(user.id)
        assert updated_user.is_online == 0, "用户应该是离线状态"
        print(f"✓ 用户离线状态更新成功")
        
    except Exception as e:
        print(f"✗ 在线状态测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试用户认证和对话管理功能")
    print("="*60)
    
    # 初始化数据库
    try:
        init_db()
        print("\n✓ 数据库初始化完成")
    except Exception as e:
        print(f"\n⚠ 数据库初始化警告: {e}")
    
    try:
        # 测试用户相关功能
        user = test_user_creation()
        user, token = test_user_authentication()
        test_user_online_status()
        
        # 测试对话相关功能
        conversation = test_conversation_management()
        test_message_management()
        test_conversation_cascade_delete()
        
        print_section("所有测试完成")
        print("✓ 用户认证功能正常")
        print("✓ 对话管理功能正常")
        print("✓ 消息管理功能正常")
        print("✓ 级联删除功能正常")
        
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

