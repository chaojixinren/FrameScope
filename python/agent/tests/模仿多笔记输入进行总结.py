

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到路径
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# 添加 agent 目录到路径（以便导入模块）
agent_path = Path(__file__).parent.parent
sys.path.insert(0, str(agent_path))

from graphs.node.summary_node import summary_node
from graphs.state import AIState

# ============================================================================
# 测试配置（直接在此文件中配置，无需数据库）
# ============================================================================
TEST_CONFIG = {
    "model_name": "qwen-max",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "sk-c61481ce440445db9dc8b12298f7aecb",
    "provider_id": "qwen",  # 用于 state，但实际不会从数据库读取
}


def create_mock_note_results() -> list:
    """
    创建模拟的多笔记结果
    模拟格式与 note_generation_node 输出的格式一致
    """
    return [
        {
            "url": "https://www.bilibili.com/video/BV1test001",
            "platform": "bilibili",
            "title": "索尼 A7M4 相机深度评测 - 专业摄影师的第一手体验",
            "markdown": """# 索尼 A7M4 相机评测

## 优点

1. **画质表现**
   - 3300万像素全画幅传感器，画质细腻
   - 优秀的低光性能，ISO 6400 可用
   - 色彩还原准确，直出效果佳

2. **对焦系统**
   - 759个相位检测点，覆盖范围广
   - 实时眼部对焦，人像拍摄方便
   - 视频追焦能力强

3. **视频功能**
   - 4K 60p 录制能力
   - 10bit 4:2:2 色深
   - S-Log3 和 S-Cinetone 支持

## 缺点

1. **价格偏高**
   - 单机身约 17000 元
   - 相比竞品价格略高

2. **电池续航**
   - 拍摄约 530 张照片
   - 视频录制续航一般

3. **菜单系统**
   - 菜单层级较深
   - 新手需要时间适应

## 总结

索尼 A7M4 是一款性能均衡的专业相机，适合专业摄影师和高级爱好者。""",
            "transcript": {
                "language": "zh",
                "full_text": "索尼A7M4相机评测...",
                "segments": []
            },
            "audio_meta": {
                "title": "索尼 A7M4 相机深度评测 - 专业摄影师的第一手体验",
                "duration": 1200.0,
                "video_id": "BV1test001",
                "platform": "bilibili",
                "cover_url": "https://example.com/cover1.jpg"
            }
        },
        {
            "url": "https://www.bilibili.com/video/BV1test002",
            "platform": "bilibili",
            "title": "索尼 A7M4 vs 佳能 R6 Mark II - 对比评测",
            "markdown": """# 索尼 A7M4 vs 佳能 R6 Mark II 对比

## 画质对比

- **索尼 A7M4**: 3300万像素，细节更丰富
- **佳能 R6 Mark II**: 2420万像素，高感表现更好

## 对焦对比

- **索尼 A7M4**: 759个对焦点，眼部对焦更精准
- **佳能 R6 Mark II**: 动物眼部对焦更强

## 视频功能

- **索尼 A7M4**: 4K 60p，10bit 4:2:2
- **佳能 R6 Mark II**: 4K 60p，但有过热问题

## 价格

- **索尼 A7M4**: 约 17000 元
- **佳能 R6 Mark II**: 约 16000 元

## 推荐

- 需要高像素和视频功能：选择索尼 A7M4
- 需要更好的高感和连拍：选择佳能 R6 Mark II""",
            "transcript": {
                "language": "zh",
                "full_text": "索尼A7M4与佳能R6 Mark II对比...",
                "segments": []
            },
            "audio_meta": {
                "title": "索尼 A7M4 vs 佳能 R6 Mark II - 对比评测",
                "duration": 900.0,
                "video_id": "BV1test002",
                "platform": "bilibili",
                "cover_url": "https://example.com/cover2.jpg"
            }
        },
        {
            "url": "https://www.bilibili.com/video/BV1test003",
            "platform": "bilibili",
            "title": "索尼 A7M4 使用一年后的真实感受",
            "markdown": """# 索尼 A7M4 一年使用体验

## 优点

1. **稳定性**
   - 一年使用下来，没有出现过死机
   - 各种环境下表现稳定

2. **画质**
   - 3300万像素足够日常使用
   - 裁切后仍有较高像素

3. **工作流**
   - 与索尼生态兼容性好
   - 后期处理方便

## 缺点

1. **菜单**
   - 菜单确实复杂
   - 需要自定义设置才能高效使用

2. **价格**
   - 购买时价格偏高
   - 建议等促销时购买

3. **镜头群**
   - 原厂镜头价格较高
   - 副厂镜头选择多但需要适配

## 总结

索尼 A7M4 是一款值得购买的全画幅相机，但需要一定学习成本。""",
            "transcript": {
                "language": "zh",
                "full_text": "索尼A7M4一年使用体验...",
                "segments": []
            },
            "audio_meta": {
                "title": "索尼 A7M4 使用一年后的真实感受",
                "duration": 600.0,
                "video_id": "BV1test003",
                "platform": "bilibili",
                "cover_url": "https://example.com/cover3.jpg"
            }
        }
    ]


def create_test_llm_client(model_name=None, provider_id=None):
    """
    创建测试用的 LLM 客户端（不依赖数据库，直接使用配置）
    """
    from langchain_openai import ChatOpenAI
    
    # 直接使用测试配置创建 ChatOpenAI 实例
        client = ChatOpenAI(
            api_key=TEST_CONFIG["api_key"],
            base_url=TEST_CONFIG["base_url"],
            model=TEST_CONFIG["model_name"],
            temperature=0.7,
            timeout=180.0,  # 增加超时时间，适用于处理长文本总结
        )
    
    return client


async def test_summary_node():
    """
    测试 summary_node 是否能正确处理多个笔记并生成总结
    """
    print("=" * 60)
    print("开始测试 summary_node（多笔记总结功能）")
    print("=" * 60)
    
    print(f"\n【测试配置】")
    print(f"  模型名称: {TEST_CONFIG['model_name']}")
    print(f"  Base URL: {TEST_CONFIG['base_url']}")
    print(f"  API Key: {TEST_CONFIG['api_key'][:10]}...")
    
    # 创建模拟的笔记结果
    mock_note_results = create_mock_note_results()
    
    print(f"\n【模拟笔记】")
    print(f"笔记数量: {len(mock_note_results)}")
    for i, note in enumerate(mock_note_results, 1):
        print(f"  笔记 {i}: {note['title']}")
        print(f"    平台: {note['platform']}")
        print(f"    URL: {note['url']}")
        print(f"    Markdown 长度: {len(note['markdown'])} 字符")
    
    # 创建测试用的 state
    test_state: AIState = {
        "question": "索尼相机怎么样？",
        "user_id": 1,
        "session_id": "test_summary_session_001",
        "timestamp": None,
        "history": [],
        "answer": None,
        "video_urls": [],
        "search_query": None,
        "note_results": mock_note_results,  # 模拟的笔记结果
        "model_name": TEST_CONFIG["model_name"],
        "provider_id": TEST_CONFIG["provider_id"],
        "note_generation_status": None,
        "summary_result": None,
        "metadata": None,
    }
    
    print(f"\n【测试参数】")
    print(f"  问题: {test_state['question']}")
    print(f"  用户ID: {test_state['user_id']}")
    print(f"  模型名称: {test_state['model_name']}")
    print(f"  提供商ID: {test_state['provider_id']}")
    print()
    
    try:
        # 使用 mock 替换 get_llm_client，使其使用测试配置而不是数据库
        # 需要 patch summary_node 模块中导入的 get_llm_client（因为使用了 from import）
        with patch('graphs.node.summary_node.get_llm_client', side_effect=create_test_llm_client):
            # 调用 summary_node
            print("开始调用 summary_node...")
            result_state = await summary_node(test_state)
        
        # 打印结果
        print("\n" + "=" * 60)
        print("测试结果")
        print("=" * 60)
        
        print(f"\n【最终总结】")
        summary = result_state.get("summary_result", "")
        answer = result_state.get("answer", "")
        print(f"{summary or answer}")
        
        print(f"\n【元数据】")
        metadata = result_state.get("metadata", {})
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        return result_state
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_summary_node())

