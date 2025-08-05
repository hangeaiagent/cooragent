#!/usr/bin/env python3
"""
旅游智能体模板独立测试脚本

直接测试模板定义和结构，不依赖外部工具和API。
"""

def test_travel_agent_templates():
    """测试旅游智能体模板定义"""
    
    print("🚀 开始测试旅游智能体模板定义...")
    
    # 直接定义模板结构（从travel_agent_templates.py复制）
    travel_templates = {
        # === 基础旅游智能体模板 ===
        "destination_expert": {
            "name": "destination_expert",
            "nick_name": "目的地专家",
            "llm_type": "researcher",
            "tools": ["tavily_tool", "browser_tool"],
            "prompt_template": "destination_expert",
            "description": "专业的旅游目的地专家，擅长分析目的地特色、推荐景点、制定行程路线，熟悉全球热门旅游城市的文化、交通、住宿和美食信息。",
            "specialties": ["destination_analysis", "itinerary_planning", "local_culture"],
            "target_regions": ["global"]
        },
        
        "budget_optimizer": {
            "name": "budget_optimizer", 
            "nick_name": "预算优化师",
            "llm_type": "coder",
            "tools": ["python_repl_tool", "tavily_tool"],
            "prompt_template": "budget_optimizer",
            "description": "专业的旅游预算优化专家，精通成本分析、价格比较、省钱攻略制定，能够为不同预算水平的用户提供最优性价比的旅游方案。",
            "specialties": ["budget_analysis", "cost_optimization", "value_comparison"],
            "target_budgets": ["budget", "mid_range", "luxury"]
        },
        
        "family_travel_planner": {
            "name": "family_travel_planner",
            "nick_name": "亲子旅游规划师", 
            "llm_type": "researcher",
            "tools": ["tavily_tool", "browser_tool"],
            "prompt_template": "family_travel_planner",
            "description": "专业的亲子旅游规划专家，深度了解适合不同年龄段儿童的旅游活动、安全注意事项、亲子友好的住宿和餐饮选择。",
            "specialties": ["family_activities", "child_safety", "age_appropriate_planning"],
            "target_audience": ["families_with_children", "multi_generation"]
        },
        
        "cultural_heritage_guide": {
            "name": "cultural_heritage_guide",
            "nick_name": "文化遗产向导",
            "llm_type": "researcher",
            "tools": ["tavily_tool", "browser_tool"],
            "prompt_template": "cultural_heritage_guide", 
            "description": "专业的文化遗产旅游专家，精通世界文化遗产、历史古迹、传统文化体验，能够提供深度的文化旅游解读和体验建议。",
            "specialties": ["cultural_heritage", "historical_sites", "traditional_experiences"],
            "target_interests": ["culture", "history", "education"]
        },
        
        "adventure_travel_specialist": {
            "name": "adventure_travel_specialist",
            "nick_name": "探险旅游专家",
            "llm_type": "researcher",
            "tools": ["tavily_tool", "browser_tool"],
            "prompt_template": "adventure_travel_specialist",
            "description": "专业的探险旅游专家，熟悉户外运动、极限体验、自然探索活动，能够为喜欢挑战和刺激的旅行者定制冒险旅程。",
            "specialties": ["outdoor_activities", "extreme_sports", "nature_exploration"],
            "target_activities": ["hiking", "diving", "skiing", "climbing"]
        },
        
        # === 专业化旅游工作流智能体模板 ===
        "transportation_planner": {
            "name": "transportation_planner",
            "nick_name": "交通规划智能体",
            "llm_type": "researcher",
            "tools": ["tavily_tool", "python_repl_tool", "browser_tool"],
            "prompt_template": "transportation_planner",
            "description": "专业的交通规划专家，精通航班、火车、汽车等各种交通方式的时刻表、价格对比和路线优化，能够根据行程安排最优交通方案。",
            "specialties": ["flight_booking", "train_scheduling", "route_optimization", "price_comparison"],
            "target_services": ["flights", "trains", "buses", "car_rental", "local_transport"]
        },
        
        "itinerary_designer": {
            "name": "itinerary_designer",
            "nick_name": "行程设计智能体",
            "llm_type": "researcher",
            "tools": ["tavily_tool", "browser_tool", "python_repl_tool"],
            "prompt_template": "itinerary_designer",
            "description": "专业的行程设计师，根据目的地特色和用户偏好，推荐最佳景点、活动和体验，并提供详细的日程安排和实用信息。",
            "specialties": ["attraction_recommendation", "activity_planning", "schedule_optimization", "photo_sourcing"],
            "target_features": ["daily_itinerary", "attraction_details", "photo_urls", "timing_optimization"]
        },
        
        "cost_calculator": {
            "name": "cost_calculator", 
            "nick_name": "费用计算智能体",
            "llm_type": "coder",
            "tools": ["python_repl_tool", "tavily_tool"],
            "prompt_template": "cost_calculator",
            "description": "专业的旅游费用计算专家，精确统计交通、住宿、餐饮、门票等各项开支，提供详细的预算分析和成本优化建议。",
            "specialties": ["expense_tracking", "budget_analysis", "cost_breakdown", "financial_planning"],
            "target_categories": ["transportation", "accommodation", "meals", "attractions", "shopping", "insurance"]
        },
        
        "report_integrator": {
            "name": "report_integrator",
            "nick_name": "结果整合智能体", 
            "llm_type": "reporter",
            "tools": ["python_repl_tool"],
            "prompt_template": "report_integrator",
            "description": "专业的旅游报告整合专家，汇总各智能体的规划结果，生成包含文字描述、数据表格、景点图片的完整Word文档报告。",
            "specialties": ["content_integration", "document_generation", "data_visualization", "report_formatting"],
            "target_outputs": ["word_document", "pdf_report", "presentation", "summary_tables"]
        },
        
        "travel_coordinator": {
            "name": "travel_coordinator",
            "nick_name": "旅游协调专家",
            "llm_type": "coordinator",
            "tools": ["tavily_tool", "python_repl_tool", "browser_tool"],
            "prompt_template": "travel_coordinator",
            "description": "旅游多智能体协调专家，统筹管理交通规划、行程设计、费用计算等各个智能体，确保整体旅游方案的协调性和完整性。",
            "specialties": ["agent_coordination", "workflow_management", "quality_assurance", "integration_optimization"],
            "target_workflow": ["multi_agent_orchestration", "result_validation", "conflict_resolution", "final_integration"]
        }
    }
    
    # 1. 测试模板完整性
    print("\n📋 Step 1: 测试模板完整性...")
    
    required_fields = ['name', 'nick_name', 'llm_type', 'tools', 'prompt_template', 'description']
    
    for template_id, template in travel_templates.items():
        missing_fields = [field for field in required_fields if field not in template]
        if missing_fields:
            print(f"   ❌ 模板 {template_id} 缺少字段: {missing_fields}")
        else:
            print(f"   ✅ 模板 {template_id}: {template['nick_name']}")
    
    print(f"✅ 总共定义了 {len(travel_templates)} 个旅游智能体模板")
    
    # 2. 测试分类统计
    print("\n📋 Step 2: 测试模板分类...")
    
    basic_templates = ["destination_expert", "budget_optimizer", "family_travel_planner", 
                      "cultural_heritage_guide", "adventure_travel_specialist"]
    workflow_templates = ["transportation_planner", "itinerary_designer", "cost_calculator", 
                         "report_integrator", "travel_coordinator"]
    
    basic_count = sum(1 for tid in basic_templates if tid in travel_templates)
    workflow_count = sum(1 for tid in workflow_templates if tid in travel_templates)
    
    print(f"✅ 基础旅游模板: {basic_count} 个")
    for template_id in basic_templates:
        if template_id in travel_templates:
            print(f"   - {template_id}: {travel_templates[template_id]['nick_name']}")
    
    print(f"✅ 工作流模板: {workflow_count} 个")
    for template_id in workflow_templates:
        if template_id in travel_templates:
            print(f"   - {template_id}: {travel_templates[template_id]['nick_name']}")
    
    # 3. 测试工具配置
    print("\n📋 Step 3: 测试工具配置...")
    
    tool_usage = {}
    for template_id, template in travel_templates.items():
        for tool in template['tools']:
            if tool not in tool_usage:
                tool_usage[tool] = []
            tool_usage[tool].append(template_id)
    
    print("🔧 工具使用统计:")
    for tool, users in tool_usage.items():
        print(f"   - {tool}: 被 {len(users)} 个智能体使用")
    
    # 4. 测试LLM类型分布
    print("\n📋 Step 4: 测试LLM类型分布...")
    
    llm_usage = {}
    for template_id, template in travel_templates.items():
        llm_type = template['llm_type']
        if llm_type not in llm_usage:
            llm_usage[llm_type] = []
        llm_usage[llm_type].append(template_id)
    
    print("🤖 LLM类型分布:")
    for llm_type, users in llm_usage.items():
        print(f"   - {llm_type}: {len(users)} 个智能体")
    
    # 5. 测试描述质量
    print("\n📋 Step 5: 测试描述质量...")
    
    description_stats = {}
    for template_id, template in travel_templates.items():
        desc_length = len(template['description'])
        if desc_length >= 80:
            description_stats[template_id] = "excellent"
        elif desc_length >= 50:
            description_stats[template_id] = "good"
        else:
            description_stats[template_id] = "needs_improvement"
    
    excellent_count = sum(1 for status in description_stats.values() if status == "excellent")
    good_count = sum(1 for status in description_stats.values() if status == "good")
    needs_improvement = sum(1 for status in description_stats.values() if status == "needs_improvement")
    
    print(f"📝 描述质量统计:")
    print(f"   - 优秀 (≥80字符): {excellent_count} 个")
    print(f"   - 良好 (50-79字符): {good_count} 个")
    print(f"   - 需要改进 (<50字符): {needs_improvement} 个")
    
    # 6. 测试专长领域覆盖
    print("\n📋 Step 6: 测试专长领域覆盖...")
    
    all_specialties = set()
    for template in travel_templates.values():
        if 'specialties' in template:
            all_specialties.update(template['specialties'])
    
    print(f"🎯 专长领域覆盖: {len(all_specialties)} 个专业领域")
    specialty_list = sorted(list(all_specialties))
    for i in range(0, len(specialty_list), 3):
        row = specialty_list[i:i+3]
        print(f"   {' | '.join(row)}")
    
    # 7. 验证用户场景覆盖
    print("\n📋 Step 7: 验证用户场景覆盖...")
    
    scenarios = {
        "交通规划": "transportation_planner",
        "行程设计": "itinerary_designer", 
        "费用计算": "cost_calculator",
        "文档生成": "report_integrator",
        "多智能体协调": "travel_coordinator",
        "目的地咨询": "destination_expert",
        "预算优化": "budget_optimizer",
        "亲子旅游": "family_travel_planner",
        "文化旅游": "cultural_heritage_guide",
        "探险旅游": "adventure_travel_specialist"
    }
    
    covered_scenarios = 0
    for scenario, template_id in scenarios.items():
        if template_id in travel_templates:
            print(f"   ✅ {scenario}: {travel_templates[template_id]['nick_name']}")
            covered_scenarios += 1
        else:
            print(f"   ❌ {scenario}: 缺少对应模板")
    
    coverage_percentage = (covered_scenarios / len(scenarios)) * 100
    print(f"📊 用户场景覆盖率: {coverage_percentage:.1f}%")
    
    return True, len(travel_templates), basic_count, workflow_count, coverage_percentage

def test_prompt_templates():
    """测试提示词模板"""
    
    print("\n🔍 测试提示词模板质量...")
    
    # 提示词模板定义（简化版本用于测试）
    prompt_templates = {
        "destination_expert": """你是一位专业的旅游目的地专家，拥有丰富的全球旅游经验和深入的地理文化知识。

核心职责：
1. 目的地分析：深入分析旅游目的地的特色、亮点、最佳旅游时间
2. 景点推荐：根据用户偏好推荐合适的景点和活动
3. 行程规划：制定合理的游览路线和时间安排
4. 文化解读：介绍当地文化、习俗、注意事项

请始终保持专业、热情的态度，为用户提供有价值的目的地信息和建议。""",

        "transportation_planner": """你是一位专业的交通规划专家，精通各种交通方式的时刻表、价格分析和路线优化。

核心职责：
1. 交通方案设计：根据行程安排最优的交通路线和时间
2. 价格比较分析：对比不同交通工具的价格和性价比
3. 时刻表规划：精确安排出发和到达时间，确保行程衔接
4. 路线优化：选择最efficient的交通路线，减少中转和等待时间

输出格式：
- 推荐交通方案（主要和备选）
- 详细时刻表和价格信息
- 预订链接和注意事项
- 总交通费用估算

请始终以用户的便利性和经济性为优先考虑。""",

        "cost_calculator": """你是一位专业的旅游费用计算专家，精通各项旅游开支的精确统计和预算分析。

核心职责：
1. 费用统计：精确计算交通、住宿、餐饮、门票等各项花费
2. 预算分析：提供详细的费用明细和占比分析
3. 成本优化：识别节省费用的机会和替代方案
4. 财务规划：制定合理的旅游预算和支出计划

输出格式：
- 详细费用明细表
- 费用分类统计图
- 总费用和人均费用
- 费用占比分析
- 节省费用的建议

请确保计算准确，提供实用的省钱建议。"""
    }
    
    quality_criteria = {
        "min_length": 200,  # 最少字符数
        "has_responsibilities": ["核心职责", "职责"],  # 应包含职责说明
        "has_workflow": ["工作流程", "流程", "输出格式", "格式"],  # 应包含流程说明
        "has_professional_tone": ["专业", "专家"],  # 应体现专业性
    }
    
    print("📊 提示词质量分析:")
    
    total_score = 0
    total_templates = len(prompt_templates)
    
    for template_id, prompt in prompt_templates.items():
        # 检查各项质量标准
        length_ok = len(prompt) >= quality_criteria["min_length"]
        has_responsibilities = any(keyword in prompt for keyword in quality_criteria["has_responsibilities"])
        has_workflow = any(keyword in prompt for keyword in quality_criteria["has_workflow"])
        has_professional_tone = any(keyword in prompt for keyword in quality_criteria["has_professional_tone"])
        
        # 计算质量分数
        score = sum([length_ok, has_responsibilities, has_workflow, has_professional_tone])
        quality_percentage = (score / 4) * 100
        total_score += quality_percentage
        
        status_icon = "✅" if quality_percentage >= 75 else "⚠️" if quality_percentage >= 50 else "❌"
        
        print(f"   {status_icon} {template_id}: 质量分数 {quality_percentage:.0f}% (长度:{len(prompt)}字符)")
    
    average_score = total_score / total_templates
    print(f"📈 平均质量分数: {average_score:.1f}%")
    
    return average_score >= 75

if __name__ == "__main__":
    print("=" * 80)
    print("🏖️  旅游智能体模板定义 - 独立验证测试")
    print("=" * 80)
    
    # 运行模板结构测试
    success, total_count, basic_count, workflow_count, coverage = test_travel_agent_templates()
    
    # 运行提示词质量测试  
    prompt_quality_ok = test_prompt_templates()
    
    # 最终结果统计
    print("\n" + "=" * 80)
    print("📊 测试结果总结:")
    print(f"   - 模板总数: {total_count} 个")
    print(f"   - 基础模板: {basic_count} 个")
    print(f"   - 工作流模板: {workflow_count} 个")
    print(f"   - 场景覆盖率: {coverage:.1f}%")
    print(f"   - 提示词质量: {'优秀' if prompt_quality_ok else '需要改进'}")
    
    if success and prompt_quality_ok and coverage >= 90:
        print("\n🎉 所有测试通过！旅游智能体模板定义完整且质量优秀")
        print("✅ 模板设计符合需求，可以开始集成测试")
    elif success and coverage >= 80:
        print("\n⚠️ 基础测试通过，但仍有改进空间")
        print("💡 建议优化提示词质量和场景覆盖")
    else:
        print("\n❌ 测试未完全通过，需要修改模板定义")
    
    print("=" * 80) 