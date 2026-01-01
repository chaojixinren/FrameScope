"""
测试 video_search_node
测试视频搜索节点的功能：查询扩展、Bilibili API 搜索、热度计算、视频筛选

测试说明：
1. 测试查询扩展功能（如 "索尼 A7M4 怎么样" -> "索尼 A7M4 评测"）
2. 测试 Bilibili API 搜索功能
3. 测试热度得分计算
4. 测试营销关键词过滤
5. 测试返回的视频 URL 格式和数量

运行方式：
   方式1：从项目根目录运行（推荐）
   python python/agent/tests/测试video_search_node.py
   
   方式2：从 python 目录运行
   cd python
   python agent/tests/测试video_search_node.py
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

from graphs.node.video_search_node import video_search_node
from graphs.state import AIState
from tools.video_tools import (
    expand_search_query,
    search_bilibili_api,
    calculate_popularity_score,
    filter_marketing_videos,
    search_and_filter_videos
)

# 测试配置
TEST_QUESTIONS = [
    "索尼 A7M4 怎么样",
    "佳能相机推荐",
    "尼康 Z6 值得买吗",
    "富士相机如何",
]

# 测试用例：查询扩展
TEST_QUERY_EXPANSION = [
    ("索尼 A7M4 怎么样", "索尼 A7M4 评测"),
    ("佳能相机推荐", "佳能相机 评测"),
    ("尼康 Z6 值得买吗", "尼康 Z6 评测"),
    ("富士相机如何", "富士相机 评测"),
]


def test_query_expansion():
    """测试查询扩展功能"""
    print("\n" + "="*60)
    print("测试 1: 查询扩展功能")
    print("="*60)
    
    for original, expected_pattern in TEST_QUERY_EXPANSION:
        expanded = expand_search_query(original)
        print(f"\n原始查询: {original}")
        print(f"扩展后: {expanded}")
        
        # 检查是否包含关键词
        keywords = ["评测", "实拍", "选购", "推荐", "对比"]
        has_keyword = any(kw in expanded for kw in keywords)
        
        if has_keyword:
            print("✓ 查询扩展成功（包含搜索关键词）")
        else:
            print("⚠ 查询扩展可能未添加关键词")
    
    print("\n" + "-"*60)


def test_popularity_score():
    """测试热度得分计算"""
    print("\n" + "="*60)
    print("测试 2: 热度得分计算")
    print("="*60)
    
    test_cases = [
        (1000000, 100000, "高播放量高点赞"),
        (500000, 50000, "中等播放量中等点赞"),
        (100000, 10000, "低播放量低点赞"),
        (0, 0, "零播放量零点赞"),
    ]
    
    for view, like, description in test_cases:
        score = calculate_popularity_score(view, like)
        print(f"\n{description}:")
        print(f"  播放量: {view:,}, 点赞数: {like:,}")
        print(f"  热度得分: {score:.4f}")
        
        # 检查得分是否在合理范围内（0-1）
        if 0 <= score <= 1:
            print("  ✓ 得分在合理范围内")
        else:
            print("  ⚠ 得分超出预期范围")
    
    print("\n" + "-"*60)


def test_marketing_filter():
    """测试营销关键词过滤"""
    print("\n" + "="*60)
    print("测试 3: 营销关键词过滤")
    print("="*60)
    
    test_titles = [
        ("索尼 A7M4 相机评测", True, "正常标题"),
        ("拼多多特价相机", False, "包含营销关键词"),
        ("抽奖活动相机推荐", False, "包含营销关键词"),
        ("纯搬运视频", False, "包含营销关键词"),
        ("佳能相机深度评测", True, "正常标题"),
        ("限时秒杀相机", False, "包含营销关键词"),
    ]
    
    for title, should_pass, description in test_titles:
        result = filter_marketing_videos(title)
        status = "✓" if result == should_pass else "✗"
        print(f"{status} {description}: '{title}' -> {'保留' if result else '过滤'}")
    
    print("\n" + "-"*60)


def test_bilibili_api_search():
    """测试 Bilibili API 搜索（需要网络连接）"""
    print("\n" + "="*60)
    print("测试 4: Bilibili API 搜索")
    print("="*60)
    
    test_query = "索尼相机"
    
    print(f"\n搜索关键词: {test_query}")
    print("正在调用 Bilibili API...")
    
    try:
        result = search_bilibili_api(test_query, page=1, page_size=10)
        
        if result:
            print("✓ API 调用成功")
            
            # 检查返回数据结构
            data = result.get("data", {})
            video_list = data.get("result", [])
            
            print(f"  找到 {len(video_list)} 个视频")
            
            if video_list:
                # 显示前3个视频的信息
                print("\n  前3个视频信息:")
                for i, video in enumerate(video_list[:3], 1):
                    title = video.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", "")
                    bvid = video.get("bvid", "")
                    view = video.get("play", 0)
                    like = video.get("like", 0)
                    
                    print(f"    {i}. {title}")
                    print(f"       BV号: {bvid}")
                    print(f"       播放量: {view:,}, 点赞数: {like:,}")
        else:
            print("⚠ API 调用失败或返回空结果")
            
    except Exception as e:
        print(f"✗ API 调用出错: {str(e)}")
    
    print("\n" + "-"*60)


def test_search_and_filter():
    """测试完整的搜索和筛选流程（需要网络连接）"""
    print("\n" + "="*60)
    print("测试 5: 完整搜索和筛选流程")
    print("="*60)
    
    test_query = "索尼相机"
    
    print(f"\n搜索关键词: {test_query}")
    print("正在搜索并筛选视频...")
    
    try:
        videos = search_and_filter_videos(
            query=test_query,
            max_results=5,
            page=1,
            page_size=50
        )
        
        if videos:
            print(f"✓ 成功找到 {len(videos)} 个高质量视频\n")
            
            for i, video in enumerate(videos, 1):
                print(f"  {i}. {video['title']}")
                print(f"     URL: {video['url']}")
                print(f"     热度得分: {video['popularity_score']:.4f}")
                print()
        else:
            print("⚠ 未找到符合条件的视频")
            
    except Exception as e:
        print(f"✗ 搜索过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-"*60)


def test_video_search_node():
    """测试 video_search_node 节点（需要网络连接）"""
    print("\n" + "="*60)
    print("测试 6: video_search_node 节点完整测试")
    print("="*60)
    
    # 使用第一个测试问题
    test_question = TEST_QUESTIONS[0]
    
    print(f"\n测试问题: {test_question}")
    print("正在运行 video_search_node...")
    
    # 创建初始状态
    initial_state: AIState = {
        "question": test_question,
        "user_id": None,
        "timestamp": None,
        "session_id": None,
        "history": [],
        "answer": None,
        "video_urls": None,
        "search_query": None,
        "note_results": None,
        "model_name": None,
        "provider_id": None,
        "note_generation_status": None,
        "summary_result": None,
        "metadata": None,
    }
    
    try:
        # 运行节点
        result_state = video_search_node(initial_state)
        
        # 检查结果
        video_urls = result_state.get("video_urls", [])
        search_query = result_state.get("search_query")
        
        print(f"\n✓ 节点执行成功")
        print(f"  扩展后的查询: {search_query}")
        print(f"  找到视频数量: {len(video_urls)}")
        
        if video_urls:
            print(f"\n  返回的视频列表:")
            for i, video in enumerate(video_urls, 1):
                print(f"    {i}. {video['title']}")
                print(f"       URL: {video['url']}")
                print(f"       热度得分: {video['popularity_score']:.4f}")
                print()
            
            # 验证 URL 格式
            print("  验证 URL 格式:")
            all_valid = True
            for video in video_urls:
                url = video.get("url", "")
                if url.startswith("https://www.bilibili.com/video/BV"):
                    print(f"    ✓ {url}")
                else:
                    print(f"    ✗ 无效的 URL 格式: {url}")
                    all_valid = False
            
            if all_valid:
                print("\n  ✓ 所有 URL 格式正确")
        else:
            print("  ⚠ 未找到视频（可能是网络问题或 API 限制）")
            
    except Exception as e:
        print(f"\n✗ 节点执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-"*60)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 video_search_node")
    print("="*60)
    
    # 基础功能测试（不需要网络）
    test_query_expansion()
    test_popularity_score()
    test_marketing_filter()
    
    # 网络相关测试（需要网络连接）
    print("\n" + "="*60)
    print("网络相关测试（需要网络连接）")
    print("="*60)
    
    try:
        test_bilibili_api_search()
        test_search_and_filter()
        test_video_search_node()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()

