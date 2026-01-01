"""
交互式测试 chat_node 对话功能

用于测试普通 LLM 对话的上下文保持能力，不进行视频搜索和笔记生成
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

# 设置工作目录
os.chdir(backend_path)

from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers
from agent.graphs.node.chat_node import chat_node
from agent.graphs.state import AIState
from agent.utils.config_helper import get_default_model_config

# 测试配置
TEST_MODEL_NAME = None  # 使用默认
TEST_PROVIDER_ID = None  # 使用默认

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def setup_environment():
    """初始化环境和数据库"""
    print_section("初始化环境")
    
    try:
        init_db()
        seed_default_providers()
        print("✓ 数据库初始化完成")
    except Exception as e:
        print(f"⚠ 数据库初始化警告: {e}")
    
    # 获取默认配置
    try:
        model_name, provider_id = get_default_model_config()
        print(f"✓ 默认模型: {model_name}")
        print(f"✓ 默认提供商: {provider_id}")
        return model_name, provider_id
    except Exception as e:
        print(f"✗ 获取默认配置失败: {e}")
        print("请确保数据库中有启用的提供商和模型")
        sys.exit(1)


def create_mock_summary() -> str:
    """创建一个模拟的视频总结，用于测试上下文"""
    return """# 索尼A7M4相机全面总结

## 概述
索尼A7M4是一款全画幅无反相机，具备出色的视频和拍照功能。本文将基于多个视频的笔记内容，从不同角度对A7M4进行总结。

## 主要特点

### 优点
1. **优秀的视频功能**：支持4K 60fps录制，10比特422色彩采样，以及S-Log3和HLG等多种专业视频格式。
2. **高动态范围**：在动态范围方面表现优秀，适合多种拍摄环境。
3. **强大的自动对焦**：具备先进的人眼和动物眼控对焦功能，对焦速度快且准确。
4. **便携性和设计**：机身紧凑，适合旅行和日常使用，同时具备良好的操控性和人体工程学设计。
5. **高分辨率传感器**：搭载3300万像素背照式传感器，提供出色的解析力和细节表现。

### 缺点
1. **果冻效应**：在某些模式下，如4K 60帧录制时，A7M4仍存在一定的果冻效应。
2. **4K 60帧裁切**：在4K 60帧模式下，A7M4需要进行APS-C裁切，无法使用全画幅传感器。
3. **电池续航**：虽然有改进，但在长时间拍摄时仍需携带备用电池。
4. **单SD卡槽**：只配备一个SD卡槽，对于商业拍摄来说可能不够安全。

## 价格信息
根据多个视频评测，索尼A7M4的官方售价约为 **16999元**（人民币），实际市场价格可能在 **15000-17000元** 之间波动，具体价格取决于购买渠道和促销活动。

## 适用场景
- 专业视频创作者
- 摄影爱好者
- 需要高质量照片和视频的用户
- 旅行摄影师

## 与A7M3的对比
相比A7M3，A7M4的主要改进包括：
- 更高的像素（3300万 vs 2400万）
- 更好的视频功能（4K 60fps vs 4K 30fps）
- 改进的自动对焦系统
- 更好的色彩科学
- 更长的电池续航（虽然仍有改进空间）"""


async def interactive_chat():
    """交互式对话测试"""
    print_section("交互式 chat_node 对话测试")
    
    # 初始化环境
    model_name, provider_id = setup_environment()
    
    # 创建模拟的视频总结
    mock_summary = create_mock_summary()
    print(f"✓ 已创建模拟视频总结（长度: {len(mock_summary)} 字符）")
    
    # 初始化对话历史
    conversation_history = []
    
    # 创建初始 state
    state: AIState = {
        "question": "",  # 将在循环中更新
        "user_id": 1,
        "session_id": "interactive_test_session",
        "timestamp": None,
        "history": conversation_history,
        "answer": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": model_name,
        "provider_id": provider_id,
        "note_generation_status": None,
        "summary_result": mock_summary,  # 模拟的视频总结
        "metadata": None,
        "trace_data": None,
    }
    
    print("\n" + "="*60)
    print("开始交互式对话")
    print("="*60)
    print("\n提示：")
    print("- 输入问题后按回车发送")
    print("- 输入 'quit' 或 'exit' 退出")
    print("- 输入 'clear' 清空对话历史")
    print("- 输入 'history' 查看对话历史")
    print("\n模拟场景：你已经询问过'索尼A7M4相机怎么样？'，并获得了视频总结。")
    print("现在可以进行后续提问，测试上下文保持能力。\n")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n[你] ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n退出对话测试。")
                break
            
            if user_input.lower() == 'clear':
                conversation_history = []
                state["history"] = conversation_history
                print("✓ 对话历史已清空")
                continue
            
            if user_input.lower() == 'history':
                print("\n当前对话历史：")
                if not conversation_history:
                    print("  (空)")
                else:
                    for i, msg in enumerate(conversation_history, 1):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")[:100]  # 只显示前100字符
                        print(f"  {i}. [{role}] {content}...")
                continue
            
            # 更新 state 中的问题
            state["question"] = user_input
            state["history"] = conversation_history
            
            print(f"\n[系统] 正在处理问题，请稍候...")
            
            # 调用 chat_node
            try:
                result_state = await chat_node(state)
                
                # 获取回复
                answer = result_state.get("answer", "")
                
                if answer:
                    print(f"\n[助手] {answer}")
                    
                    # 更新对话历史
                    conversation_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": answer
                    })
                    
                    print(f"\n[系统] 回复已添加到对话历史（当前历史消息数: {len(conversation_history)}）")
                else:
                    print("\n[系统] 未收到回复")
                    
            except Exception as e:
                print(f"\n[错误] 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        except KeyboardInterrupt:
            print("\n\n退出对话测试。")
            break
        except EOFError:
            print("\n\n退出对话测试。")
            break


async def main():
    """主函数"""
    try:
        await interactive_chat()
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())



