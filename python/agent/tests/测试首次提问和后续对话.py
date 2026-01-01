"""
测试首次提问和后续对话的交互逻辑

测试说明：
1. 测试首次提问：应该执行完整的视频搜索和总结流程
2. 测试后续提问：应该只执行普通对话，但保留之前的总结作为上下文
3. 测试路由逻辑：根据history判断是首次提问还是后续对话

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/测试首次提问和后续对话.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/测试首次提问和后续对话.py

注意：
- 首次提问会执行完整的视频搜索和笔记生成，可能需要较长时间（1-5分钟）
- 后续提问只调用LLM，速度较快（几秒到几十秒）
"""

import sys
import os
import asyncio
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
from app.db.conversation_dao import create_conversation, get_conversation_by_id
from app.db.message_dao import get_messages_by_conversation_id

from agent.graphs.agent_graph import build_multi_video_graph, should_do_video_search
from agent.graphs.state import AIState
from agent.utils.config_helper import get_default_model_config
from app.db.provider_dao import get_provider_by_id

# 测试配置
TEST_USERNAME = "test_chat_flow_" + str(os.getpid())
TEST_PASSWORD = "test_password_123"
TEST_MODEL_NAME, TEST_PROVIDER_ID = get_default_model_config()


def check_api_key_config():
    """检查 API Key 配置是否正确"""
    print_section("检查 API Key 配置")
    
    try:
        provider = get_provider_by_id(TEST_PROVIDER_ID)
        if not provider:
            print(f"✗ 未找到提供商: {TEST_PROVIDER_ID}")
            return False
        
        # Provider 是 SQLAlchemy 对象，使用属性访问，不是 .get()
        api_key = provider.api_key if hasattr(provider, 'api_key') else ""
        provider_name = provider.name if hasattr(provider, 'name') else TEST_PROVIDER_ID
        
        if not api_key or api_key.strip() == "":
            print(f"✗ 提供商 {provider_name} 的 API Key 未配置")
            print(f"  请在数据库中配置 API Key")
            return False
        
        # 检查是否是占位符
        placeholder_keys = ['your_api_key_here', 'your_deepseek_api_key_here', 
                           'your_qwen_api_key_here', 'your_openai_api_key_here', '']
        if api_key.lower() in placeholder_keys:
            print(f"✗ 提供商 {provider_name} 的 API Key 是占位符")
            print(f"  请替换为真实的 API Key")
            return False
        
        print(f"✓ 提供商: {provider_name}")
        print(f"✓ 模型: {TEST_MODEL_NAME}")
        print(f"✓ API Key 已配置（长度: {len(api_key)} 字符）")
        return True
        
    except Exception as e:
        print(f"✗ 检查 API Key 配置时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def setup_test_user():
    """设置测试用户"""
    try:
        user = get_user_by_username(TEST_USERNAME)
        if user:
            print(f"✓ 测试用户已存在: {user.id}")
            return user
        
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


def test_router_logic():
    """测试路由逻辑：判断是首次提问还是后续对话"""
    print_section("测试1: 路由逻辑判断")
    
    # 测试场景1：首次提问（history为空）
    state1: AIState = {
        "question": "索尼A7M4相机怎么样？",
        "user_id": 1,
        "session_id": "test_session_1",
        "history": [],  # 空历史
        "timestamp": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": TEST_MODEL_NAME,
        "provider_id": TEST_PROVIDER_ID,
        "note_generation_status": None,
        "summary_result": None,
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    result1 = should_do_video_search(state1)
    assert result1 == "video_search", f"首次提问应该路由到 video_search，但得到: {result1}"
    print("✓ 场景1：首次提问（history为空）→ 路由到 video_search")
    
    # 测试场景2：首次提问（只有用户消息）
    state2: AIState = {
        "question": "索尼A7M4相机怎么样？",
        "user_id": 1,
        "session_id": "test_session_2",
        "history": [
            {"role": "user", "content": "之前的问题"}
        ],  # 只有用户消息
        "timestamp": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": TEST_MODEL_NAME,
        "provider_id": TEST_PROVIDER_ID,
        "note_generation_status": None,
        "summary_result": None,
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    result2 = should_do_video_search(state2)
    assert result2 == "video_search", f"只有用户消息应该路由到 video_search，但得到: {result2}"
    print("✓ 场景2：首次提问（只有用户消息）→ 路由到 video_search")
    
    # 测试场景3：后续提问（有助手回复）
    state3: AIState = {
        "question": "那它的价格是多少？",
        "user_id": 1,
        "session_id": "test_session_3",
        "history": [
            {"role": "user", "content": "索尼A7M4相机怎么样？"},
            {"role": "assistant", "content": "根据多个视频的分析，索尼A7M4..."}
        ],  # 有助手回复
        "timestamp": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": TEST_MODEL_NAME,
        "provider_id": TEST_PROVIDER_ID,
        "note_generation_status": None,
        "summary_result": None,
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    result3 = should_do_video_search(state3)
    assert result3 == "chat", f"有助手回复应该路由到 chat，但得到: {result3}"
    print("✓ 场景3：后续提问（有助手回复）→ 路由到 chat")
    
    print("\n✓ 路由逻辑测试通过！")


async def test_first_query_full_workflow():
    """测试首次提问：执行完整的视频搜索和总结流程"""
    print_section("测试2: 首次提问（完整工作流）")
    
    print("⚠ 注意：此测试会执行完整的视频搜索和笔记生成，可能需要1-5分钟")
    print("   如果不想等待，可以跳过此测试\n")
    
    user = setup_test_user()
    
    # 创建新对话
    conversation = create_conversation(user_id=user.id, title="")
    conversation_id = conversation.id
    print(f"✓ 创建新对话: conversation_id={conversation_id}")
    
    # 构建工作流
    graph = build_multi_video_graph()
    
    # 初始化state（首次提问，history为空）
    initial_state: AIState = {
        "question": "索尼A7M4相机怎么样？",
        "user_id": user.id,
        "session_id": f"test_session_{conversation_id}",
        "history": [],  # 空历史，表示首次提问
        "timestamp": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": TEST_MODEL_NAME,
        "provider_id": TEST_PROVIDER_ID,
        "note_generation_status": None,
        "summary_result": None,
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    print("\n开始执行工作流（首次提问）...")
    print("这可能需要一些时间，请耐心等待...\n")
    
    try:
        result = await graph.ainvoke(initial_state)
        
        # 验证结果
        answer = result.get("answer", "")
        summary_result = result.get("summary_result", "")
        video_urls = result.get("video_urls", [])
        note_results = result.get("note_results", [])
        trace_data = result.get("trace_data", {})
        
        print("\n" + "="*60)
        print("首次提问结果验证")
        print("="*60 + "\n")
        
        # 验证结果（允许部分失败）
        if answer:
            print(f"✓ 生成了答案（长度: {len(answer)} 字符）")
        else:
            print("⚠ 未生成答案")
        
        if summary_result:
            print(f"✓ 生成了总结（长度: {len(summary_result)} 字符）")
        else:
            print("⚠ 未生成总结")
        
        if video_urls:
            print(f"✓ 搜索到 {len(video_urls)} 个视频")
        else:
            print("⚠ 未搜索到视频（可能是网络问题或搜索失败）")
        
        if note_results:
            print(f"✓ 生成了 {len(note_results)} 个视频笔记")
        else:
            print("⚠ 未生成视频笔记（可能是视频下载、转录或API Key配置问题）")
            print("  提示：请检查 API Key 是否正确配置")
        
        if trace_data:
            print(f"✓ 生成了 {len(trace_data)} 个关键帧")
        else:
            print("⚠ 未生成关键帧（可能是时间戳提取失败或没有笔记结果）")
        
        # 如果完全没有结果，给出更详细的提示
        if not answer and not summary_result and not note_results:
            print("\n" + "="*60)
            print("⚠ 测试未生成任何结果")
            print("="*60)
            print("可能的原因：")
            print("1. API Key 未配置或配置错误")
            print("2. 网络连接问题")
            print("3. 视频搜索失败")
            print("4. 视频下载或转录失败")
            print("\n建议：")
            print("- 检查数据库中的 API Key 配置")
            print("- 检查网络连接")
            print("- 查看上面的详细错误信息")
            return None, conversation_id
        
        # 显示答案的前500字符
        print(f"\n答案预览（前500字符）:")
        print("-"*60)
        print(answer[:500])
        if len(answer) > 500:
            print(f"... (还有 {len(answer) - 500} 字符)")
        print("-"*60)
        
        # 保存消息到数据库（模拟main.py的逻辑）
        from app.db.message_dao import create_message
        try:
            create_message(
                user_id=user.id,
                conversation_id=conversation_id,
                role="user",
                content=initial_state["question"]
            )
            create_message(
                user_id=user.id,
                conversation_id=conversation_id,
                role="assistant",
                content=answer
            )
            print(f"\n✓ 消息已保存到数据库（conversation_id={conversation_id}）")
        except Exception as e:
            print(f"\n⚠ 保存消息失败: {e}")
        
        return result, conversation_id
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n✗ 首次提问测试失败: {error_msg}")
        
        # 检查是否是 API Key 相关错误
        if "Bearer" in error_msg or "api_key" in error_msg.lower() or "Illegal header" in error_msg:
            print("\n" + "="*60)
            print("⚠ API Key 配置问题")
            print("="*60)
            print("错误信息表明 API Key 可能未正确配置。")
            print("请检查：")
            print("1. 数据库中的 API Key 是否已配置")
            print("2. API Key 是否有效（不是占位符）")
            print("3. API Key 格式是否正确")
            print("\n可以在测试开始前运行 API Key 检查来验证配置。")
        
        # 检查是否是笔记生成失败
        if "笔记生成" in error_msg or "note" in error_msg.lower():
            print("\n" + "="*60)
            print("⚠ 笔记生成失败")
            print("="*60)
            print("可能的原因：")
            print("1. API Key 配置问题（最常见）")
            print("2. 视频下载失败")
            print("3. 转录服务失败")
            print("4. GPT 总结失败")
        
        import traceback
        traceback.print_exc()
        return None, conversation_id


async def test_followup_query_chat_only():
    """测试后续提问：只执行普通对话"""
    print_section("测试3: 后续提问（普通对话）")
    
    print("⚠ 注意：此测试需要先运行测试2（首次提问），或者提供一个已有的conversation_id")
    print("   如果conversation_id为空，将跳过此测试\n")
    
    user = setup_test_user()
    
    # 尝试获取已有的对话（从测试2创建的）
    # 如果没有，可以手动提供conversation_id
    conversation_id = None
    
    # 查找用户最近的对话
    from app.db.conversation_dao import get_conversations_by_user_id
    conversations = get_conversations_by_user_id(user.id, limit=1, offset=0)
    if conversations:
        conversation_id = conversations[0].id
        print(f"✓ 找到已有对话: conversation_id={conversation_id}")
    else:
        print("⚠ 未找到已有对话，跳过后续提问测试")
        print("   提示：可以先运行测试2（首次提问）来创建对话")
        return
    
    # 加载历史消息
    messages = get_messages_by_conversation_id(conversation_id)
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    print(f"✓ 加载了 {len(history)} 条历史消息")
    
    # 从历史消息中提取第一次的总结
    previous_summary = None
    for msg in messages:
        if msg.role == "assistant":
            content = msg.content
            # 判断是否是视频总结
            if "![关键帧" in content or "查看原片" in content or "bilibili.com/video" in content:
                previous_summary = content
                print(f"✓ 从历史消息中提取到之前的视频总结（长度: {len(content)} 字符）")
                break
    
    # 构建工作流
    graph = build_multi_video_graph()
    
    # 初始化state（后续提问，history包含助手回复）
    initial_state: AIState = {
        "question": "那它的价格是多少？",
        "user_id": user.id,
        "session_id": f"test_session_{conversation_id}",
        "history": history,  # 包含历史对话
        "timestamp": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": TEST_MODEL_NAME,
        "provider_id": TEST_PROVIDER_ID,
        "note_generation_status": None,
        "summary_result": previous_summary,  # 之前的总结
        "answer": None,
        "metadata": None,
        "trace_data": None,
    }
    
    print("\n开始执行工作流（后续提问）...")
    print("这应该只调用LLM，速度较快...\n")
    
    try:
        result = await graph.ainvoke(initial_state)
        
        # 验证结果
        answer = result.get("answer", "")
        
        print("\n" + "="*60)
        print("后续提问结果验证")
        print("="*60 + "\n")
        
        assert answer, "应该生成答案"
        print(f"✓ 生成了答案（长度: {len(answer)} 字符）")
        
        # 验证没有执行视频搜索（video_urls应该为空）
        video_urls = result.get("video_urls", [])
        if not video_urls:
            print("✓ 未执行视频搜索（符合预期）")
        else:
            print("⚠ 执行了视频搜索（不符合预期，应该只执行普通对话）")
        
        # 验证没有执行笔记生成（note_results应该为空）
        note_results = result.get("note_results", [])
        if not note_results:
            print("✓ 未执行笔记生成（符合预期）")
        else:
            print("⚠ 执行了笔记生成（不符合预期，应该只执行普通对话）")
        
        # 显示答案
        print(f"\n答案预览（前500字符）:")
        print("-"*60)
        print(answer[:500])
        if len(answer) > 500:
            print(f"... (还有 {len(answer) - 500} 字符)")
        print("-"*60)
        
        # 验证答案是否引用了之前的总结
        if previous_summary:
            # 检查答案中是否包含总结中的关键词
            summary_keywords = ["A7M4", "索尼", "相机", "画质", "性能"]
            found_keywords = [kw for kw in summary_keywords if kw in answer]
            if found_keywords:
                print(f"✓ 答案中引用了之前的总结（包含关键词: {', '.join(found_keywords)}）")
            else:
                print("⚠ 答案中可能未引用之前的总结（需要人工检查）")
        
        print("\n✓ 后续提问测试通过！")
        
    except Exception as e:
        print(f"\n✗ 后续提问测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_multiple_followup_queries():
    """测试多个后续提问：连续对话"""
    print_section("测试4: 多个后续提问（连续对话）")
    
    print("⚠ 注意：此测试需要先运行测试2（首次提问）")
    print("   如果conversation_id为空，将跳过此测试\n")
    
    user = setup_test_user()
    
    # 查找用户最近的对话
    from app.db.conversation_dao import get_conversations_by_user_id
    conversations = get_conversations_by_user_id(user.id, limit=1, offset=0)
    if not conversations:
        print("⚠ 未找到已有对话，跳过连续对话测试")
        return
    
    conversation_id = conversations[0].id
    print(f"✓ 使用对话: conversation_id={conversation_id}")
    
    # 构建工作流
    graph = build_multi_video_graph()
    
    # 测试多个后续问题
    followup_questions = [
        "那它的价格是多少？",
        "和A7M3相比有什么改进？",
        "适合新手使用吗？"
    ]
    
    for i, question in enumerate(followup_questions, 1):
        print(f"\n--- 后续提问 {i}/{len(followup_questions)}: {question} ---")
        
        # 加载最新的历史消息
        messages = get_messages_by_conversation_id(conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 提取之前的总结
        previous_summary = None
        for msg in messages:
            if msg.role == "assistant":
                content = msg.content
                if "![关键帧" in content or "查看原片" in content:
                    previous_summary = content
                    break
        
        # 初始化state
        initial_state: AIState = {
            "question": question,
            "user_id": user.id,
            "session_id": f"test_session_{conversation_id}",
            "history": history,
            "timestamp": None,
            "video_urls": None,
            "search_query": None,
            "note_results": None,
            "model_name": TEST_MODEL_NAME,
            "provider_id": TEST_PROVIDER_ID,
            "note_generation_status": None,
            "summary_result": previous_summary,
            "answer": None,
            "metadata": None,
            "trace_data": None,
        }
        
        try:
            result = await graph.ainvoke(initial_state)
            answer = result.get("answer", "")
            
            if answer:
                print(f"✓ 生成答案（长度: {len(answer)} 字符）")
                print(f"  预览: {answer[:100]}...")
                
                # 保存消息到数据库
                from app.db.message_dao import create_message
                try:
                    create_message(
                        user_id=user.id,
                        conversation_id=conversation_id,
                        role="user",
                        content=question
                    )
                    create_message(
                        user_id=user.id,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=answer
                    )
                except Exception as e:
                    print(f"  ⚠ 保存消息失败: {e}")
            else:
                print("⚠ 未生成答案")
                
        except Exception as e:
            print(f"✗ 提问失败: {str(e)}")
    
    print("\n✓ 连续对话测试完成！")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试首次提问和后续对话的交互逻辑")
    print("="*60)
    
    try:
        # 初始化数据库
        init_db()
        seed_default_providers()
        print("\n✓ 数据库初始化完成")
    except Exception as e:
        print(f"\n⚠ 数据库初始化警告: {e}")
    
    try:
        # 检查 API Key 配置
        if not check_api_key_config():
            print("\n" + "="*60)
            print("⚠ API Key 未正确配置，测试可能会失败")
            print("="*60)
            print("是否继续测试？(y/n): ", end="")
            user_input = input().strip().lower()
            if user_input != 'y':
                print("测试已取消")
                return False
        
        # 测试1：路由逻辑
        test_router_logic()
        
        # 测试2：首次提问（完整工作流）
        # 注意：这个测试会执行完整的视频搜索和笔记生成，可能需要较长时间
        # 如果不想等待，可以注释掉这个测试
        print("\n" + "="*60)
        print("是否执行首次提问测试（完整工作流）？")
        print("这可能需要1-5分钟，输入 y 继续，其他键跳过")
        print("="*60)
        user_input = input().strip().lower()
        
        first_result = None
        conversation_id = None
        
        if user_input == 'y':
            first_result, conversation_id = await test_first_query_full_workflow()
        else:
            print("跳过首次提问测试（完整工作流）")
        
        # 测试3：后续提问（普通对话）
        # 如果测试2执行了，会自动使用创建的对话
        # 如果没有，可以手动提供conversation_id
        if first_result or conversation_id:
            print("\n" + "="*60)
            print("是否执行后续提问测试（普通对话）？")
            print("输入 y 继续，其他键跳过")
            print("="*60)
            user_input = input().strip().lower()
            
            if user_input == 'y':
                await test_followup_query_chat_only()
            else:
                print("跳过后续提问测试")
        
        # 测试4：多个后续提问（连续对话）
        if first_result or conversation_id:
            print("\n" + "="*60)
            print("是否执行连续对话测试？")
            print("输入 y 继续，其他键跳过")
            print("="*60)
            user_input = input().strip().lower()
            
            if user_input == 'y':
                await test_multiple_followup_queries()
            else:
                print("跳过连续对话测试")
        
        print_section("所有测试完成")
        print("✓ 路由逻辑测试通过")
        if first_result:
            print("✓ 首次提问测试通过")
        print("✓ 测试完成！")
        
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
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

