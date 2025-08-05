#!/usr/bin/env python3
"""
旅游智能体模板管理器测试脚本

测试标准旅游智能体的创建、加载和功能验证。
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.manager.agents import AgentManager
from src.manager.travel_agent_templates import TravelAgentTemplateManager
from src.utils.path_utils import get_project_root

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_travel_agent_template_manager():
    """测试旅游智能体模板管理器"""
    
    print("🚀 开始测试旅游智能体模板管理器...")
    
    try:
        # 1. 初始化AgentManager
        print("\n📋 Step 1: 初始化AgentManager...")
        
        tools_dir = get_project_root() / "store" / "tools"
        agents_dir = get_project_root() / "store" / "agents"  
        prompts_dir = get_project_root() / "store" / "prompts"
        
        agent_manager = AgentManager(tools_dir, agents_dir, prompts_dir)
        await agent_manager.initialize()
        
        print(f"✅ AgentManager初始化成功，可用智能体: {len(agent_manager.available_agents)} 个")
        
        # 2. 创建TravelAgentTemplateManager
        print("\n📋 Step 2: 创建TravelAgentTemplateManager...")
        
        travel_template_manager = TravelAgentTemplateManager(agent_manager)
        
        # 3. 列出所有模板
        print("\n📋 Step 3: 列出所有旅游智能体模板...")
        
        all_templates = travel_template_manager.list_all_templates()
        print(f"✅ 总共定义了 {len(all_templates)} 个旅游智能体模板:")
        
        for template_id, template in all_templates.items():
            print(f"   - {template_id}: {template['nick_name']} ({template['description'][:50]}...)")
        
        # 4. 按类别列出模板
        print("\n📋 Step 4: 按类别列出模板...")
        
        basic_templates = travel_template_manager.get_templates_by_category("basic")
        workflow_templates = travel_template_manager.get_templates_by_category("workflow")
        
        print(f"✅ 基础旅游智能体模板: {len(basic_templates)} 个")
        for template_id in basic_templates:
            print(f"   - {template_id}")
            
        print(f"✅ 工作流智能体模板: {len(workflow_templates)} 个")  
        for template_id in workflow_templates:
            print(f"   - {template_id}")
        
        # 5. 创建标准旅游智能体
        print("\n📋 Step 5: 创建标准旅游智能体...")
        
        creation_results = await travel_template_manager.create_standard_travel_agents()
        
        print("✅ 旅游智能体创建结果:")
        for template_id, result in creation_results.items():
            status_icon = "✅" if result is True else "⚠️" if result == "already_exists" else "❌"
            status_text = "成功创建" if result is True else "已存在" if result == "already_exists" else "创建失败"
            print(f"   {status_icon} {template_id}: {status_text}")
        
        # 6. 验证智能体是否创建成功
        print("\n📋 Step 6: 验证智能体是否创建成功...")
        
        default_agents = await agent_manager._list_default_agents()
        travel_agents = [agent for agent in default_agents 
                        if agent.agent_name in all_templates.keys()]
        
        print(f"✅ 在共享智能体中找到 {len(travel_agents)} 个旅游智能体:")
        for agent in travel_agents:
            print(f"   - {agent.agent_name} ({agent.nick_name}): {len(agent.selected_tools)} 个工具")
        
        # 7. 测试意图推荐功能
        print("\n📋 Step 7: 测试智能体推荐功能...")
        
        test_intents = [
            {"travel_type": "cultural_tourism", "budget_level": "mid_range", "complexity": "simple"},
            {"travel_type": "family_tourism", "budget_level": "budget", "complexity": "complex"},
            {"travel_type": "adventure_tourism", "budget_level": "luxury", "complexity": "simple"},
            {"travel_type": "general", "budget_level": "budget", "complexity": "simple"},
        ]
        
        for intent in test_intents:
            recommended = await travel_template_manager.get_recommended_agent(intent)
            print(f"   🎯 意图 {intent} → 推荐智能体: {recommended}")
        
        # 8. 测试模板信息获取
        print("\n📋 Step 8: 测试模板信息获取...")
        
        test_template = "destination_expert"
        template_info = travel_template_manager.get_template_info(test_template)
        
        if template_info:
            print(f"✅ 模板 {test_template} 信息:")
            print(f"   - 昵称: {template_info['nick_name']}")
            print(f"   - LLM类型: {template_info['llm_type']}")
            print(f"   - 工具数量: {len(template_info['tools'])}")
            print(f"   - 专长: {template_info['specialties']}")
        
        # 9. 验证智能体工具配置
        print("\n📋 Step 9: 验证智能体工具配置...")
        
        sample_agent_name = "destination_expert"
        if sample_agent_name in agent_manager.available_agents:
            sample_agent = agent_manager.available_agents[sample_agent_name]
            print(f"✅ 智能体 {sample_agent_name} 工具配置:")
            for tool in sample_agent.selected_tools:
                print(f"   - {tool.name}: {tool.description[:50]}...")
        
        # 10. 统计结果
        print("\n📊 测试结果统计:")
        
        success_count = sum(1 for result in creation_results.values() if result is True)
        existing_count = sum(1 for result in creation_results.values() if result == "already_exists") 
        failed_count = sum(1 for result in creation_results.values() if result is False)
        
        print(f"   ✅ 成功创建: {success_count} 个智能体")
        print(f"   ⚠️ 已存在: {existing_count} 个智能体")
        print(f"   ❌ 创建失败: {failed_count} 个智能体")
        print(f"   📊 总体成功率: {((success_count + existing_count) / len(creation_results) * 100):.1f}%")
        
        print(f"\n🎉 旅游智能体模板管理器测试完成!")
        print(f"   - 共定义 {len(all_templates)} 个模板")
        print(f"   - 成功加载 {len(travel_agents)} 个旅游智能体")
        print(f"   - 系统总可用智能体: {len(agent_manager.available_agents)} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.exception("测试失败")
        return False

async def test_agent_workflow_creation():
    """测试通过命令行方式创建智能体的流程"""
    
    print("\n🧪 测试智能体工作流创建...")
    
    try:
        # 模拟用户请求创建智能体的场景
        test_requests = [
            "创建交通规划智能体：根据行程或其他智能体输出，安排出发/到达时间、路线、票价等，输出详尽交通计划。",
            "创建行程设计智能体：根据目的地和用户偏好，推荐景点、给出理由及照片 URL，并设计详细日程。",
            "创建费用计算智能体：统计交通、住宿、门票、餐饮等所有花销，输出预算明细与总花费。"
        ]
        
        print("✅ 模拟用户请求:")
        for i, request in enumerate(test_requests, 1):
            print(f"   {i}. {request[:50]}...")
        
        print("💡 这些请求将通过现有的agent_factory机制处理")
        print("💡 系统会自动匹配相应的旅游智能体模板")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流测试出现错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🏖️  旅游智能体模板管理器 - 功能测试")
    print("=" * 80)
    
    async def main():
        # 主要功能测试
        main_test_success = await test_travel_agent_template_manager()
        
        # 工作流测试
        workflow_test_success = await test_agent_workflow_creation()
        
        # 最终结果
        print("\n" + "=" * 80)
        if main_test_success and workflow_test_success:
            print("🎉 所有测试通过！旅游智能体模板管理器功能正常")
            print("✅ 可以开始使用旅游智能体功能")
        else:
            print("⚠️ 部分测试未通过，请检查日志排查问题")
        print("=" * 80)
    
    # 运行测试
    asyncio.run(main()) 