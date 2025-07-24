#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旅游智能体演示程序
Tourist Agent Demo Program
"""

from travel_agent import AdvancedTravelAgent
import time

def print_separator(title="", char="=", length=60):
    """打印分隔线"""
    if title:
        title = f" {title} "
        padding = (length - len(title)) // 2
        print(char * padding + title + char * padding)
    else:
        print(char * length)

def demo_natural_language_processing():
    """演示自然语言处理功能"""
    print_separator("自然语言处理演示")
    
    agent = AdvancedTravelAgent()
    
    test_inputs = [
        "我想去北京旅游3天，预算3000元，喜欢历史文化和美食",
        "计划上海5天行程，预算8000元，喜欢观光和美食",
        "北京2天游，预算1500元，主要想看文化景点"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n测试 {i}: {user_input}")
        preferences = agent.process_user_input(user_input)
        print(f"解析结果: {preferences}")
        print("-" * 50)

def demo_itinerary_generation():
    """演示行程生成功能"""
    print_separator("个性化行程生成演示")
    
    agent = AdvancedTravelAgent()
    
    # 设置用户偏好
    print("设置用户偏好: 北京3天游，预算3000元，喜欢文化和美食")
    agent.set_user_preferences(
        budget=3000, 
        days=3, 
        interests=['culture', 'food'], 
        destination='北京'
    )
    
    # 生成行程
    print("\n正在生成个性化行程...")
    agent.generate_personalized_itinerary()
    
    # 展示行程
    agent.display_itinerary()
    
    return agent

def demo_weather_adjustment(agent):
    """演示天气调整功能"""
    print_separator("天气调整演示")
    
    print("模拟天气变化: 雨天")
    agent.adjust_itinerary_for_weather('雨天')
    
    print("\n🌧️ 调整后的行程:")
    agent.display_itinerary()
    
    print("\n模拟天气变化: 高温")
    agent.adjust_itinerary_for_weather('高温')
    
    print("\n🌡️ 再次调整后的行程:")
    agent.display_itinerary()

def demo_export_functionality(agent):
    """演示导出功能"""
    print_separator("行程导出演示")
    
    filename = f"demo_itinerary_{int(time.time())}.json"
    agent.export_itinerary_to_json(filename)
    
    # 读取并显示导出的文件内容
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"\n导出的行程文件内容预览:")
        print(content[:500] + "..." if len(content) > 500 else content)
    except Exception as e:
        print(f"读取文件时出错: {e}")

def demo_different_destinations():
    """演示不同目的地"""
    print_separator("多目的地演示")
    
    destinations = [
        {'name': '上海', 'budget': 5000, 'days': 4, 'interests': ['sightseeing', 'food']},
        {'name': '北京', 'budget': 2000, 'days': 2, 'interests': ['culture']}
    ]
    
    for dest in destinations:
        print(f"\n--- {dest['name']}行程 ---")
        agent = AdvancedTravelAgent()
        agent.set_user_preferences(
            budget=dest['budget'],
            days=dest['days'],
            interests=dest['interests'],
            destination=dest['name']
        )
        
        agent.generate_personalized_itinerary()
        agent.display_itinerary()
        print("\n" + "=" * 50)

def main():
    """主演示程序"""
    print_separator("🎯 旅游智能体完整演示程序", "🌟", 60)
    print("欢迎使用AI驱动的智能旅游规划助手！")
    print("本演示将展示智能体的各项核心功能。\n")
    
    try:
        # 1. 自然语言处理演示
        demo_natural_language_processing()
        time.sleep(1)
        
        # 2. 行程生成演示
        agent = demo_itinerary_generation()
        time.sleep(1)
        
        # 3. 天气调整演示
        demo_weather_adjustment(agent)
        time.sleep(1)
        
        # 4. 导出功能演示
        demo_export_functionality(agent)
        time.sleep(1)
        
        # 5. 多目的地演示
        demo_different_destinations()
        
        # 6. 实时推荐演示
        print_separator("实时推荐演示")
        recommendations = agent.get_real_time_recommendations()
        print("📱 实时推荐信息:")
        for key, value in recommendations.items():
            print(f"  {key}: {value}")
        
        print_separator("演示完成", "🎉", 60)
        print("感谢您使用旅游智能体演示程序！")
        print("如需更多功能，请参考 README.md 文档。")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        print("请检查代码或联系开发团队。")

if __name__ == "__main__":
    main()
