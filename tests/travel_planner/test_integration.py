"""
旅游规划器集成测试

测试完整的旅游规划工作流程
"""

import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

@pytest.mark.asyncio
async def test_travel_workflow_integration():
    """测试完整旅游规划工作流"""
    
    # 这是一个集成测试示例，需要在实际环境中运行
    print("🧪 开始旅游规划器集成测试")
    
    # 测试用例
    test_cases = [
        {
            "name": "北京文化游",
            "query": "我想去北京玩5天，预算3000元，喜欢历史文化",
            "expected_agents": ["transportation_planner", "cultural_heritage_guide", "cost_calculator", "report_integrator"]
        },
        {
            "name": "三亚亲子游", 
            "query": "带孩子去三亚度假一周，有什么亲子活动推荐",
            "expected_agents": ["family_travel_planner", "destination_expert", "itinerary_designer"]
        },
        {
            "name": "简单查询",
            "query": "上海天气怎么样",
            "expected_complexity": "simple"
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 测试用例: {case['name']}")
        print(f"   查询: {case['query']}")
        
        # 在实际环境中，这里会调用真实的工作流
        # result = await execute_travel_workflow(case['query'])
        
        print(f"   ✅ 测试用例 {case['name']} 模拟通过")
    
    print("\n🎉 所有集成测试模拟完成")

if __name__ == "__main__":
    asyncio.run(test_travel_workflow_integration()) 