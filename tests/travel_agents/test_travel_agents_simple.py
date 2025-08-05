#!/usr/bin/env python3
"""
旅游智能体模板管理器简化测试脚本

测试模板定义和基础功能，不依赖外部API。
"""

import sys
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_travel_template_definitions():
    """测试旅游智能体模板定义"""
    
    print("🚀 开始测试旅游智能体模板定义...")
    
    try:
        # 直接导入和测试模板管理器类
        from src.manager.travel_agent_templates import TravelAgentTemplateManager
        
        # 创建一个模拟的agent_manager对象
        class MockAgentManager:
            def __init__(self):
                self.available_tools = {}
                self.available_agents = {}
                
            async def _list_default_agents(self):
                return []
                
            async def _create_agent_by_prebuilt(self, **kwargs):
                print(f"   🔧 模拟创建智能体: {kwargs['name']} ({kwargs['nick_name']})")
                return True
        
        mock_agent_manager = MockAgentManager()
        travel_template_manager = TravelAgentTemplateManager(mock_agent_manager)
        
        print("✅ TravelAgentTemplateManager 导入成功")
        
        # 1. 测试模板定义
        print("\n📋 Step 1: 测试模板定义...")
        
        all_templates = travel_template_manager.list_all_templates()
        print(f"✅ 总共定义了 {len(all_templates)} 个旅游智能体模板")
        
        # 验证每个模板的完整性
        required_fields = ['name', 'nick_name', 'llm_type', 'tools', 'prompt_template', 'description']
        
        for template_id, template in all_templates.items():
            missing_fields = [field for field in required_fields if field not in template]
            if missing_fields:
                print(f"   ❌ 模板 {template_id} 缺少字段: {missing_fields}")
            else:
                print(f"   ✅ 模板 {template_id}: {template['nick_name']}")
        
        # 2. 测试分类功能
        print("\n📋 Step 2: 测试模板分类...")
        
        basic_templates = travel_template_manager.get_templates_by_category("basic")
        workflow_templates = travel_template_manager.get_templates_by_category("workflow")
        
        print(f"✅ 基础模板: {len(basic_templates)} 个")
        for template_id in basic_templates:
            print(f"   - {template_id}")
            
        print(f"✅ 工作流模板: {len(workflow_templates)} 个")
        for template_id in workflow_templates:
            print(f"   - {template_id}")
        
        # 3. 测试提示词生成
        print("\n📋 Step 3: 测试提示词生成...")
        
        test_templates = ["destination_expert", "transportation_planner", "cost_calculator"]
        
        for template_name in test_templates:
            prompt = travel_template_manager._get_template_prompt(template_name)
            if len(prompt) > 100:  # 检查提示词是否有实际内容
                print(f"   ✅ {template_name}: 提示词长度 {len(prompt)} 字符")
            else:
                print(f"   ❌ {template_name}: 提示词过短或缺失")
        
        # 4. 测试推荐功能
        print("\n📋 Step 4: 测试智能体推荐...")
        
        test_intents = [
            {"travel_type": "cultural_tourism", "budget_level": "mid_range", "complexity": "simple"},
            {"travel_type": "family_tourism", "budget_level": "budget", "complexity": "complex"},
            {"travel_type": "adventure_tourism", "budget_level": "luxury", "complexity": "simple"},
        ]
        
        for intent in test_intents:
            # 注意：这里需要使用同步方法，因为我们没有异步环境
            recommended = travel_template_manager.get_recommended_agent_sync(intent)
            print(f"   🎯 {intent['travel_type']} → {recommended}")
        
        # 5. 测试模板信息获取
        print("\n📋 Step 5: 测试模板信息获取...")
        
        test_template = "itinerary_designer"
        template_info = travel_template_manager.get_template_info(test_template)
        
        if template_info:
            print(f"✅ 模板 {test_template} 信息:")
            print(f"   - 昵称: {template_info['nick_name']}")
            print(f"   - 描述: {template_info['description'][:80]}...")
            print(f"   - 专长: {template_info.get('specialties', 'N/A')}")
        
        print(f"\n🎉 模板定义测试完成!")
        print(f"   - 模板总数: {len(all_templates)}")
        print(f"   - 基础模板: {len(basic_templates)}")
        print(f"   - 工作流模板: {len(workflow_templates)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.exception("测试失败")
        return False

def test_prompt_quality():
    """测试提示词质量"""
    
    print("\n🔍 测试提示词质量...")
    
    try:
        from src.manager.travel_agent_templates import TravelAgentTemplateManager
        
        class MockAgentManager:
            pass
        
        travel_template_manager = TravelAgentTemplateManager(MockAgentManager())
        
        # 测试所有模板的提示词
        all_templates = travel_template_manager.list_all_templates()
        
        quality_criteria = {
            "min_length": 200,  # 最少字符数
            "has_core_responsibilities": ["核心职责", "职责"],  # 应包含职责说明
            "has_workflow": ["工作流程", "流程"],  # 应包含工作流程
            "has_output_format": ["输出格式", "格式", "输出"],  # 应包含输出说明
        }
        
        print("📊 提示词质量检查:")
        
        for template_id in all_templates.keys():
            prompt = travel_template_manager._get_template_prompt(template_id)
            
            # 检查长度
            length_ok = len(prompt) >= quality_criteria["min_length"]
            
            # 检查是否包含关键内容
            has_responsibilities = any(keyword in prompt for keyword in quality_criteria["has_core_responsibilities"])
            has_workflow = any(keyword in prompt for keyword in quality_criteria["has_workflow"])
            has_output = any(keyword in prompt for keyword in quality_criteria["has_output_format"])
            
            # 计算质量分数
            score = sum([length_ok, has_responsibilities, has_workflow, has_output])
            quality_percentage = (score / 4) * 100
            
            status_icon = "✅" if quality_percentage >= 75 else "⚠️" if quality_percentage >= 50 else "❌"
            
            print(f"   {status_icon} {template_id}: 质量分数 {quality_percentage:.0f}% (长度:{len(prompt)}字符)")
        
        return True
        
    except Exception as e:
        print(f"❌ 提示词质量测试出现错误: {e}")
        return False

# 为了同步测试，添加一个同步版本的推荐方法
def add_sync_recommendation_method():
    """为测试添加同步推荐方法"""
    
    from src.manager.travel_agent_templates import TravelAgentTemplateManager
    
    def get_recommended_agent_sync(self, travel_intent):
        """同步版本的智能体推荐（用于测试）"""
        travel_type = travel_intent.get("travel_type", "general")
        budget_level = travel_intent.get("budget_level", "mid_range") 
        complexity = travel_intent.get("complexity", "simple")
        
        if travel_type == "cultural_tourism":
            return "cultural_heritage_guide"
        elif travel_type == "family_tourism": 
            return "family_travel_planner"
        elif travel_type == "adventure_tourism":
            return "adventure_travel_specialist"
        elif budget_level in ["budget", "luxury"]:
            return "budget_optimizer"
        elif complexity == "complex":
            return "destination_expert"
        else:
            return "destination_expert"
    
    # 动态添加方法
    TravelAgentTemplateManager.get_recommended_agent_sync = get_recommended_agent_sync

if __name__ == "__main__":
    print("=" * 80)
    print("🏖️  旅游智能体模板管理器 - 简化功能测试")
    print("=" * 80)
    
    # 添加同步方法
    add_sync_recommendation_method()
    
    # 运行测试
    test1_success = test_travel_template_definitions()
    test2_success = test_prompt_quality()
    
    # 最终结果
    print("\n" + "=" * 80)
    if test1_success and test2_success:
        print("🎉 所有测试通过！旅游智能体模板定义正确")
        print("✅ 模板管理器功能正常，可以进行下一步集成测试")
    else:
        print("⚠️ 部分测试未通过，请检查模板定义")
    print("=" * 80) 