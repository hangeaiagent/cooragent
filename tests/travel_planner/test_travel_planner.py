"""
旅游规划器综合测试套件

测试TravelPlannerAgent的核心功能，包括旅游上下文提取、智能体选择、计划生成等。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

# 导入被测试的模块
from src.workflow.travel_planner import (
    TravelContextExtractor, 
    TravelAgentSelector, 
    travel_planner_node
)
from src.utils.travel_intelligence import (
    extract_travel_context,
    optimize_geographic_flow,
    analyze_travel_budget,
    validate_travel_plan
)

class TestTravelContextExtractor:
    """测试旅游上下文提取器"""
    
    def test_extract_basic_travel_info(self):
        """测试基础旅游信息提取"""
        query = "我计划5月22日到26日从上海去北京玩5天，预算3000元"
        
        context = TravelContextExtractor.extract_travel_context(query)
        
        assert context["departure"] == "上海"
        assert context["destination"] == "北京"
        assert context["duration"] == 5
        assert context["budget_range"] == 3000
        assert context["complexity"] == "complex"
    
    def test_extract_cultural_travel(self):
        """测试文化旅游类型识别"""
        query = "想去西安看历史文化古迹，有什么博物馆推荐"
        
        context = TravelContextExtractor.extract_travel_context(query)
        
        assert context["destination"] == "西安"
        assert context["travel_type"] == "cultural"
        assert "cultural" in context["preferences"]
    
    def test_extract_family_travel(self):
        """测试亲子旅游识别"""
        query = "带孩子一家4口去三亚度假7天，有什么亲子活动推荐"
        
        context = TravelContextExtractor.extract_travel_context(query)
        
        assert context["destination"] == "三亚"
        assert context["travel_type"] == "family"
        assert context["duration"] == 7
        assert context["complexity"] == "complex"
    
    def test_simple_query(self):
        """测试简单查询"""
        query = "北京天气怎么样"
        
        context = TravelContextExtractor.extract_travel_context(query)
        
        assert context["complexity"] == "simple"
        assert context["travel_type"] == "general"

class TestTravelAgentSelector:
    """测试旅游智能体选择器"""
    
    def setUp(self):
        self.selector = TravelAgentSelector()
    
    def test_complex_travel_agent_selection(self):
        """测试复杂旅游的智能体选择"""
        travel_context = {
            "travel_type": "cultural",
            "complexity": "complex",
            "budget_range": 5000,
            "duration": 7
        }
        
        agents = self.selector.select_optimal_agents(travel_context)
        
        # 应该包含核心旅游智能体
        assert "transportation_planner" in agents
        assert "itinerary_designer" in agents
        assert "cost_calculator" in agents
        assert "cultural_heritage_guide" in agents  # 文化旅游专家
        assert "budget_optimizer" in agents  # 有预算要求
        assert "destination_expert" in agents
        assert "report_integrator" in agents  # 必需的结果整合
    
    def test_family_travel_agent_selection(self):
        """测试亲子旅游的智能体选择"""
        travel_context = {
            "travel_type": "family",
            "complexity": "complex",
            "duration": 5
        }
        
        agents = self.selector.select_optimal_agents(travel_context)
        
        assert "family_travel_planner" in agents
        assert "report_integrator" in agents
    
    def test_simple_travel_agent_selection(self):
        """测试简单旅游查询的智能体选择"""
        travel_context = {
            "travel_type": "general",
            "complexity": "simple"
        }
        
        agents = self.selector.select_optimal_agents(travel_context)
        
        # 简单查询应该只有基础智能体
        assert "report_integrator" in agents
        assert len(agents) <= 3

class TestTravelIntelligence:
    """测试旅游智能分析功能"""
    
    def test_extract_travel_context_comprehensive(self):
        """测试综合旅游上下文提取"""
        query = "计划2025年5月带家人去日本东京文化之旅，预算2万元，7天6夜"
        
        context = extract_travel_context(query)
        
        assert context["destination"] == "东京"
        assert context["duration"] == 7
        assert context["budget_range"] == 20000
        assert context["travel_type"] == "cultural"
        assert "family" in context["preferences"] or "cultural" in context["preferences"]
    
    def test_optimize_geographic_flow(self):
        """测试地理流程优化"""
        steps = [
            {"agent_name": "report_integrator", "title": "生成报告"},
            {"agent_name": "cost_calculator", "title": "计算费用"},
            {"agent_name": "transportation_planner", "title": "规划交通"},
            {"agent_name": "itinerary_designer", "title": "设计行程"}
        ]
        
        travel_context = {"destination": "北京", "duration": 5}
        
        optimized_steps = optimize_geographic_flow(steps, travel_context)
        
        # 验证优化后的顺序：交通规划 -> 行程设计 -> 费用计算 -> 报告整合
        agent_order = [step["agent_name"] for step in optimized_steps]
        
        assert agent_order.index("transportation_planner") < agent_order.index("itinerary_designer")
        assert agent_order.index("itinerary_designer") < agent_order.index("cost_calculator")
        assert agent_order.index("cost_calculator") < agent_order.index("report_integrator")
        assert agent_order[-1] == "report_integrator"  # 报告整合必须最后
    
    def test_analyze_travel_budget(self):
        """测试旅游预算分析"""
        steps = [
            {"agent_name": "transportation_planner"},
            {"agent_name": "itinerary_designer"},
            {"agent_name": "cost_calculator"}
        ]
        
        budget_analysis = analyze_travel_budget(steps, 5000)
        
        assert budget_analysis["total_budget"] == 5000
        assert "transportation" in budget_analysis["categories"]
        assert "accommodation" in budget_analysis["categories"]
        assert budget_analysis["budget_level"] == "中等"
        
        # 测试无预算情况
        no_budget_analysis = analyze_travel_budget(steps, None)
        assert no_budget_analysis["total_budget"] == "未指定"
    
    def test_validate_travel_plan(self):
        """测试旅游计划验证"""
        valid_plan = {
            "thought": "这是一个详细的旅游计划",
            "title": "北京5日游",
            "steps": [
                {"agent_name": "transportation_planner", "title": "交通规划"},
                {"agent_name": "itinerary_designer", "title": "行程设计"},
                {"agent_name": "reporter", "title": "生成报告"}
            ]
        }
        
        travel_context = {"destination": "北京", "duration": 5, "complexity": "complex"}
        
        validation = validate_travel_plan(valid_plan, travel_context)
        
        assert validation["valid"] == True
        assert len(validation["errors"]) == 0
        
        # 测试无效计划
        invalid_plan = {
            "title": "不完整的计划"
            # 缺少必需字段
        }
        
        invalid_validation = validate_travel_plan(invalid_plan, travel_context)
        assert invalid_validation["valid"] == False
        assert len(invalid_validation["errors"]) > 0

class TestTravelPlannerNode:
    """测试旅游规划器节点"""
    
    @pytest.mark.asyncio
    async def test_travel_planner_node_execution(self):
        """测试旅游规划器节点执行"""
        
        # 模拟状态
        mock_state = {
            "USER_QUERY": "我想去北京玩5天，预算3000元，喜欢历史文化",
            "workflow_id": "test_workflow",
            "workflow_mode": "launch",
            "search_before_planning": True
        }
        
        # 模拟依赖
        with patch('src.workflow.travel_planner.tavily_tool') as mock_tavily, \
             patch('src.workflow.travel_planner.get_llm_by_type') as mock_llm, \
             patch('src.workflow.travel_planner.apply_prompt_template') as mock_template, \
             patch('src.workflow.travel_planner.cache') as mock_cache:
            
            # 模拟搜索结果
            mock_tavily.ainvoke.return_value = [
                {"title": "北京旅游攻略", "content": "北京是历史文化名城..."},
                {"title": "故宫博物院", "content": "明清两代皇宫..."}
            ]
            
            # 模拟LLM响应
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.return_value = Mock(content=json.dumps({
                "thought": "根据用户需求，这是一个文化类型的北京5日游规划",
                "title": "北京历史文化5日游",
                "new_agents_needed": [],
                "steps": [
                    {
                        "agent_name": "transportation_planner",
                        "title": "规划交通路线",
                        "description": "安排往返北京的交通和市内交通"
                    },
                    {
                        "agent_name": "cultural_heritage_guide",
                        "title": "文化景点推荐",
                        "description": "推荐故宫、天坛等历史文化景点"
                    },
                    {
                        "agent_name": "cost_calculator", 
                        "title": "费用计算",
                        "description": "计算总体旅游费用，确保在3000元预算内"
                    },
                    {
                        "agent_name": "report_integrator",
                        "title": "生成旅游报告",
                        "description": "整合所有信息生成详细的旅游计划文档"
                    }
                ]
            }))
            mock_llm.return_value = mock_llm_instance
            
            # 模拟提示词模板
            mock_template.return_value = [{"content": "旅游规划提示词", "role": "user"}]
            
            # 执行测试
            result = await travel_planner_node(mock_state)
            
            # 验证结果
            assert result.goto == "publisher"
            assert "travel_context" in result.update
            assert "full_plan" in result.update
            assert result.update["agent_name"] == "travel_planner"
            
            # 验证旅游上下文
            travel_context = result.update["travel_context"]
            assert travel_context["destination"] == "北京"
            assert travel_context["duration"] == 5
            assert travel_context["budget_range"] == 3000
            assert travel_context["travel_type"] == "cultural"
    
    @pytest.mark.asyncio
    async def test_travel_planner_error_handling(self):
        """测试旅游规划器错误处理"""
        
        mock_state = {
            "USER_QUERY": "无效查询",
            "workflow_id": "test_workflow",
            "workflow_mode": "launch"
        }
        
        with patch('src.workflow.travel_planner.get_llm_by_type') as mock_llm:
            # 模拟LLM错误
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.side_effect = Exception("LLM调用失败")
            mock_llm.return_value = mock_llm_instance
            
            result = await travel_planner_node(mock_state)
            
            # 应该优雅处理错误
            assert result.goto == "__end__"

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 