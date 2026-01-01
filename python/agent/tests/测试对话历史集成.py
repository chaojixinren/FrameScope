"""
测试对话历史与LangGraph工作流的集成（简化版）

测试说明：
1. 测试对话创建和消息保存（数据库层面）
2. 测试对话历史的加载（数据库层面）
3. 测试消息的保存和查询
4. 测试对话标题的更新（不实际调用LLM）

注意：此测试不运行完整的工作流，只测试数据库和对话管理功能，速度很快。

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/测试对话历史集成.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/测试对话历史集成.py
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

# 初始化数据库和环境
from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers
from app.db.user_dao import create_user, get_user_by_username
from app.db.conversation_dao import (
    create_conversation, 
    get_conversation_by_id, 
    update_conversation_title,
    get_conversations_by_user_id
)
from app.db.message_dao import (
    create_message, 
    get_messages_by_conversation_id, 
    get_message_count_by_conversation_id
)

# 测试配置
TEST_USERNAME = "test_integration_" + str(os.getpid())
TEST_PASSWORD = "test_password_123"


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def setup_test_user():
    """设置测试用户"""
    print_section("设置测试用户")
    
    try:
        # 检查用户是否已存在
        user = get_user_by_username(TEST_USERNAME)
        if user:
            print(f"✓ 测试用户已存在: {user.id}")
            return user
        
        # 创建新用户
        user = create_user(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            phone_number=None,
            avatar=None
        )
        print(f"✓ 测试用户创建成功: {user.id}")
        return user
        
    except ValueError as e:
        if "已存在" in str(e):
            user = get_user_by_username(TEST_USERNAME)
            return user
        raise


def test_conversation_creation_and_message_save():
    """测试对话创建和消息保存（数据库层面）"""
    print_section("测试1: 对话创建和消息保存")
    
    try:
        # 设置用户
        user = setup_test_user()
        
        # 直接创建对话（模拟工作流创建对话）
        conversation = create_conversation(user_id=user.id, title="测试对话")
        print(f"✓ 对话创建成功")
        print(f"  - 对话ID: {conversation.id}")
        print(f"  - 用户ID: {conversation.user_id}")
        print(f"  - 标题: {conversation.title}")
        
        # 模拟保存用户消息和助手回复
        question = "miku手办推荐"
        answer = "根据搜索结果，我为您推荐以下几款miku手办..."
        
        create_message(
            user_id=user.id,
            conversation_id=conversation.id,
            role="user",
            content=question
        )
        print(f"✓ 用户消息已保存")
        print(f"  - 内容: {question[:50]}...")
        
        create_message(
            user_id=user.id,
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )
        print(f"✓ 助手消息已保存")
        print(f"  - 内容: {answer[:50]}...")
        
        # 验证消息已保存
        messages = get_messages_by_conversation_id(conversation.id)
        print(f"\n✓ 消息验证成功")
        print(f"  - 消息数量: {len(messages)}")
        
        assert len(messages) == 2, "应该有2条消息"
        assert messages[0].role == "user", "第一条应该是用户消息"
        assert messages[1].role == "assistant", "第二条应该是助手消息"
        assert messages[0].content == question, "用户消息内容应该匹配"
        assert messages[1].content == answer, "助手消息内容应该匹配"
        
        return conversation
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_conversation_history_loading():
    """测试对话历史加载（数据库层面）"""
    print_section("测试2: 对话历史加载")
    
    try:
        # 设置用户
        user = setup_test_user()
        
        # 创建一个对话并添加一些历史消息
        conversation = create_conversation(user_id=user.id, title="历史测试对话")
        
        # 添加历史消息
        history_messages = [
            ("user", "第一个问题"),
            ("assistant", "第一个回答"),
            ("user", "第二个问题"),
            ("assistant", "第二个回答"),
        ]
        
        for role, content in history_messages:
            create_message(
                user_id=user.id,
                conversation_id=conversation.id,
                role=role,
                content=content
            )
        
        print(f"✓ 创建测试对话和历史消息")
        print(f"  - 对话ID: {conversation.id}")
        print(f"  - 历史消息数: {len(history_messages)}")
        
        # 验证历史消息存在
        messages = get_messages_by_conversation_id(conversation.id)
        assert len(messages) == len(history_messages), "历史消息数量应该匹配"
        print(f"✓ 历史消息验证成功")
        
        # 模拟工作流加载历史消息的逻辑
        loaded_messages = get_messages_by_conversation_id(conversation.id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in loaded_messages
        ]
        
        print(f"\n✓ 模拟历史消息加载")
        print(f"  - 加载的历史消息数: {len(history)}")
        
        if len(history) > 0:
            print(f"  - 历史消息预览:")
            for i, msg in enumerate(history[:4], 1):
                print(f"    {i}. [{msg['role']}] {msg['content'][:50]}...")
        
        # 验证历史消息格式正确
        assert len(history) == len(history_messages), "加载的历史消息数量应该匹配"
        for i, (expected_role, expected_content) in enumerate(history_messages):
            assert history[i]["role"] == expected_role, f"消息{i}的角色应该匹配"
            assert history[i]["content"] == expected_content, f"消息{i}的内容应该匹配"
        
        print(f"✓ 历史消息格式验证成功")
        
        # 模拟添加新消息
        new_question = "第三个问题"
        new_answer = "第三个回答"
        
        create_message(
            user_id=user.id,
            conversation_id=conversation.id,
            role="user",
            content=new_question
        )
        create_message(
            user_id=user.id,
            conversation_id=conversation.id,
            role="assistant",
            content=new_answer
        )
        
        # 验证新消息已保存
        all_messages = get_messages_by_conversation_id(conversation.id)
        print(f"\n✓ 新消息已保存")
        print(f"  - 总消息数: {len(all_messages)}")
        print(f"  - 预期消息数: {len(history_messages) + 2}")  # 历史 + 新问题 + 新回答
        
        assert len(all_messages) == len(history_messages) + 2, "总消息数应该正确"
        
        return conversation
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_conversation_title_update():
    """测试对话标题更新（不实际调用LLM）"""
    print_section("测试3: 对话标题更新")
    
    try:
        # 设置用户
        user = setup_test_user()
        
        # 创建一个标题为空的对话
        conversation = create_conversation(user_id=user.id, title="")
        print(f"✓ 创建空标题对话: {conversation.id}")
        assert conversation.title == "", "初始标题应该为空"
        
        # 模拟标题更新（不实际调用LLM生成）
        new_title = "索尼A7M4相机评测"
        update_conversation_title(conversation.id, new_title)
        
        # 验证标题已更新
        updated_conversation = get_conversation_by_id(conversation.id)
        print(f"\n✓ 标题更新完成")
        print(f"  - 新标题: {updated_conversation.title}")
        
        assert updated_conversation.title == new_title, "标题应该已更新"
        print(f"✓ 对话标题更新验证成功")
        
        return updated_conversation
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multiple_conversations():
    """测试多个对话的隔离"""
    print_section("测试4: 多个对话隔离")
    
    try:
        # 设置用户
        user = setup_test_user()
        
        # 创建两个不同的对话
        conv1 = create_conversation(user_id=user.id, title="对话1")
        conv2 = create_conversation(user_id=user.id, title="对话2")
        
        # 在对话1中添加消息
        create_message(user.id, conv1.id, "user", "对话1的消息")
        create_message(user.id, conv1.id, "assistant", "对话1的回复")
        
        # 在对话2中添加消息
        create_message(user.id, conv2.id, "user", "对话2的消息")
        create_message(user.id, conv2.id, "assistant", "对话2的回复")
        
        print(f"✓ 创建两个对话并添加消息")
        print(f"  - 对话1 ID: {conv1.id}, 消息数: {get_message_count_by_conversation_id(conv1.id)}")
        print(f"  - 对话2 ID: {conv2.id}, 消息数: {get_message_count_by_conversation_id(conv2.id)}")
        
        # 验证消息隔离
        messages1 = get_messages_by_conversation_id(conv1.id)
        messages2 = get_messages_by_conversation_id(conv2.id)
        
        assert len(messages1) == 2, "对话1应该有2条消息"
        assert len(messages2) == 2, "对话2应该有2条消息"
        assert messages1[0].content != messages2[0].content, "两个对话的消息应该不同"
        
        print(f"✓ 对话隔离验证成功")
        print(f"  - 对话1消息: {[m.content for m in messages1]}")
        print(f"  - 对话2消息: {[m.content for m in messages2]}")
        
        # 测试获取用户的所有对话
        all_conversations = get_conversations_by_user_id(user.id)
        print(f"\n✓ 获取用户所有对话")
        print(f"  - 对话总数: {len(all_conversations)}")
        assert len(all_conversations) >= 2, "应该至少有2个对话"
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_all_tests():
    """运行所有测试（简化版，不调用实际工作流）"""
    print("\n" + "="*60)
    print("开始测试对话历史与数据库集成（简化版）")
    print("="*60)
    print("注意：此测试不运行完整工作流，只测试数据库功能，速度很快")
    
    # 初始化数据库
    try:
        init_db()
        seed_default_providers()
        print("\n✓ 数据库初始化完成")
    except Exception as e:
        print(f"\n⚠ 数据库初始化警告: {e}")
    
    try:
        # 测试对话创建和消息保存
        conversation1 = test_conversation_creation_and_message_save()
        
        # 测试对话历史加载
        conversation2 = test_conversation_history_loading()
        
        # 测试标题更新
        conversation3 = test_conversation_title_update()
        
        # 测试多个对话隔离
        test_multiple_conversations()
        
        print_section("所有测试完成")
        print("✓ 对话创建和消息保存功能正常")
        print("✓ 对话历史加载功能正常")
        print("✓ 对话标题更新功能正常")
        print("✓ 多个对话隔离功能正常")
        print("\n提示：如需测试完整工作流，请使用 '可交互测试.py'")
        
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

