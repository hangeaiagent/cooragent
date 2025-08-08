"""
旅游Publisher和Agent Proxy集成测试
测试完整的旅游专业化工作流
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.workflow.travel_publisher import (
    travel_publisher_node,
    TravelPublisher,
    GeographicOptimizer,
    TravelTimeManager,
    ResourceCoordinator,
    WeatherAdapter
)
from src.workflow.travel_agent_proxy import (
    travel_agent_proxy_node,
    TravelAgentProxy,
    TravelContextInjector,
    TravelToolOptimizer,
    TravelMCPManager,
    TravelResultEnhancer
)
from src.interface.workflow import State


class TestTravelPublisher:
    """测试Travel Publisher核心功能"""
    
    @pytest.fixture
    def sample_state(self):
        return {
            "user_id": "test_user",
            "workflow_id": "test_workflow",
            "workflow_mode": "launch",
            "USER_QUERY": "我想去北京旅游3天，参观故宫、天安门、颐和园",
            "messages": [
                {"role": "user", "content": "我想去北京旅游3天，参观故宫、天安门、颐和园"}
            ]
        }
    
    @pytest.fixture
    def travel_publisher(self):
        return TravelPublisher()
    
    def test_geographic_optimizer(self):
        """测试地理优化器"""
        optimizer = GeographicOptimizer()
        
        current_loc = "北京站"
        planned_locs = ["故宫", "天安门", "颐和园", "北海公园"]
        
        result = optimizer.analyze_location_sequence(current_loc, planned_locs)
        
        assert "clustered_locations" in result
        assert "optimal_route" in result
        assert "travel_time_matrix" in result
        assert "transportation_modes" in result
        
        # 检查聚类结果
        clusters = result["clustered_locations"]
        assert isinstance(clusters, dict)
        
        # 检查路线优化
        route = result["optimal_route"]
        assert isinstance(route, list)
        assert current_loc in route
        
        # 检查时间矩阵
        time_matrix = result["travel_time_matrix"]
        assert isinstance(time_matrix, dict)
        
    def test_travel_time_manager(self):
        """测试旅游时间管理器"""
        time_manager = TravelTimeManager()
        
        current_time = datetime.now()
        business_hours = {
            "hotel_booker": {"open": 0, "close": 24},
            "restaurant_finder": {"open": 8, "close": 22},
            "attraction_planner": {"open": 9, "close": 18}
        }
        booking_deadlines = {
            "flight": current_time,
            "hotel": current_time
        }
        
        result = time_manager.validate_time_windows(
            current_time, business_hours, booking_deadlines
        )
        
        assert "valid_agents" in result
        assert "urgent_bookings" in result
        assert "optimal_timing" in result
        assert "timezone_adjustments" in result
        
        # 检查有效智能体
        valid_agents = result["valid_agents"]
        assert isinstance(valid_agents, list)
        
        # 检查紧急预订
        urgent_bookings = result["urgent_bookings"]
        assert isinstance(urgent_bookings, list)
    
    @pytest.mark.asyncio
    async def test_resource_coordinator(self):
        """测试资源协调器"""
        coordinator = ResourceCoordinator()
        
        resources = [
            {"type": "hotel", "id": "hotel_1", "priority": "high"},
            {"type": "restaurant", "id": "restaurant_1", "priority": "medium"},
            {"type": "attraction", "id": "attraction_1", "priority": "high"}
        ]
        
        result = await coordinator.check_availability(resources, {})
        
        assert "available_resources" in result
        assert "booking_conflicts" in result
        assert "alternative_options" in result
        assert "priority_bookings" in result
        
        # 检查可用性结果
        availability = result["available_resources"]
        assert isinstance(availability, dict)
        assert len(availability) == len(resources)
    
    def test_weather_adapter(self):
        """测试天气适应器"""
        adapter = WeatherAdapter()
        
        weather_forecast = {
            "上午": "晴天",
            "下午": "多云",
            "晚上": "下雨"
        }
        weather_dependent_tasks = ["户外观光", "公园游览"]
        
        result = adapter.adapt_to_weather(weather_forecast, weather_dependent_tasks)
        
        assert "weather_adaptations" in result
        assert "recommended_changes" in result
        assert "backup_plans" in result
        
        # 检查天气适应建议
        adaptations = result["weather_adaptations"]
        assert isinstance(adaptations, dict)
        assert len(adaptations) == len(weather_dependent_tasks)
    
    @pytest.mark.asyncio
    async def test_intelligent_travel_routing(self, travel_publisher, sample_state):
        """测试智能旅游路由"""
        
        selected_agent = await travel_publisher.intelligent_travel_routing(sample_state)
        
        # 应该选择合适的智能体
        assert selected_agent in [
            "travel_planner", "attraction_planner", "transportation_planner",
            "hotel_booker", "restaurant_finder"
        ]
    
    @pytest.mark.asyncio
    async def test_travel_publisher_node(self, sample_state):
        """测试旅游发布器节点"""
        
        command = await travel_publisher_node(sample_state)
        
        assert hasattr(command, 'goto')
        assert hasattr(command, 'update')
        
        # 检查路由目标
        assert command.goto in ["travel_agent_proxy", "agent_factory", "__end__"]
        
        # 检查状态更新
        update = command.update
        assert "next" in update
        assert "travel_routing_decision" in update


class TestTravelAgentProxy:
    """测试Travel Agent Proxy核心功能"""
    
    @pytest.fixture
    def sample_state(self):
        return {
            "user_id": "test_user",
            "workflow_id": "test_workflow",
            "USER_QUERY": "我想预订北京的酒店",
            "next": "hotel_booker",
            "messages": [
                {"role": "user", "content": "我想预订北京的酒店"}
            ]
        }
    
    @pytest.fixture
    def travel_agent_proxy(self):
        return TravelAgentProxy()
    
    @pytest.mark.asyncio
    async def test_travel_context_injector(self, sample_state):
        """测试旅游上下文注入器"""
        injector = TravelContextInjector()
        
        enhanced_state = await injector.inject_travel_context(sample_state, "hotel_booker")
        
        assert "travel_context" in enhanced_state
        
        travel_context = enhanced_state["travel_context"]
        assert "destination" in travel_context
        assert "agent_name" in travel_context
        assert "context_injection_time" in travel_context
        
        # 检查智能体专用上下文
        assert "accommodation_preferences" in travel_context
        assert "budget_per_night" in travel_context
    
    def test_travel_tool_optimizer(self, sample_state):
        """测试旅游工具优化器"""
        optimizer = TravelToolOptimizer()
        
        # 模拟工具
        mock_tools = [
            MagicMock(name="maps_tool"),
            MagicMock(name="weather_tool"),
            MagicMock(name="booking_tool")
        ]
        
        enhanced_state = {
            **sample_state,
            "travel_context": {
                "destination": "北京",
                "transport_preferences": {"preferred_mode": "walking"},
                "traveler_profile": {"language": "zh-CN"}
            }
        }
        
        optimized_tools = optimizer.optimize_tools_for_travel(mock_tools, enhanced_state)
        
        assert len(optimized_tools) == len(mock_tools)
        
        # 检查工具是否被增强
        for tool in optimized_tools:
            assert hasattr(tool, 'name')
    
    @pytest.mark.asyncio
    async def test_travel_mcp_manager(self):
        """测试旅游MCP管理器"""
        manager = TravelMCPManager()
        
        travel_context = {
            "destination": "北京",
            "travel_type": "leisure"
        }
        
        mcp_tools = await manager.select_destination_specific_mcp(travel_context)
        
        assert isinstance(mcp_tools, list)
        # MCP工具应该根据目的地选择
        
    def test_travel_result_enhancer(self, sample_state):
        """测试旅游结果增强器"""
        enhancer = TravelResultEnhancer()
        
        # 模拟响应
        mock_response = {
            "messages": [
                MagicMock(content="在北京找到了几个不错的酒店选择", metadata={})
            ]
        }
        
        enhanced_state = {
            **sample_state,
            "travel_context": {
                "destination": "北京",
                "traveler_profile": {"language": "zh-CN"}
            }
        }
        
        enhanced_response = enhancer.enhance_travel_result(mock_response, enhanced_state)
        
        assert "time_info" in enhanced_response
        assert "booking_info" in enhanced_response
        assert "localization" in enhanced_response
        assert "quality_assessment" in enhanced_response
    
    @pytest.mark.asyncio
    @patch('src.manager.agents.agent_manager')
    @patch('src.workflow.travel_agent_proxy.create_react_agent')
    async def test_execute_travel_agent(self, mock_create_agent, mock_agent_manager, 
                                      travel_agent_proxy, sample_state):
        """测试执行旅游智能体"""
        
        # 模拟智能体管理器
        mock_agent = MagicMock()
        mock_agent.llm_type = "basic"
        mock_agent.selected_tools = []
        mock_agent.prompt = "Test prompt"
        
        mock_agent_manager.available_agents = {"hotel_booker": mock_agent}
        mock_agent_manager.available_tools = {}
        
        # 模拟ReAct智能体
        mock_react_agent = AsyncMock()
        mock_react_agent.ainvoke.return_value = {"result": "测试结果"}
        mock_create_agent.return_value = mock_react_agent
        
        command = await travel_agent_proxy.execute_travel_agent(sample_state)
        
        assert hasattr(command, 'goto')
        assert hasattr(command, 'update')
        
        # 检查是否返回到旅游发布器
        assert command.goto == "travel_publisher"
    
    @pytest.mark.asyncio
    @patch('src.manager.agents.agent_manager')
    async def test_travel_agent_proxy_node(self, mock_agent_manager, sample_state):
        """测试旅游智能体代理节点"""
        
        # 模拟智能体管理器
        mock_agent = MagicMock()
        mock_agent.llm_type = "basic"
        mock_agent.selected_tools = []
        mock_agent.prompt = "Test prompt"
        
        mock_agent_manager.available_agents = {"hotel_booker": mock_agent}
        mock_agent_manager.available_tools = {}
        
        # 由于create_react_agent需要复杂的模拟，这里测试异常处理
        command = await travel_agent_proxy_node(sample_state)
        
        assert hasattr(command, 'goto')
        assert hasattr(command, 'update')


class TestTravelWorkflowIntegration:
    """测试完整的旅游工作流集成"""
    
    @pytest.fixture
    def travel_query_state(self):
        return {
            "user_id": "test_user",
            "workflow_id": "test_workflow",
            "workflow_mode": "launch",
            "USER_QUERY": "我计划下个月去北京旅游5天，需要预订酒店、安排景点游览和餐厅推荐",
            "messages": [
                {
                    "role": "user", 
                    "content": "我计划下个月去北京旅游5天，需要预订酒店、安排景点游览和餐厅推荐"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_travel_publisher_to_proxy_flow(self, travel_query_state):
        """测试从Travel Publisher到Travel Agent Proxy的完整流程"""
        
        # 第一步：测试Travel Publisher
        publisher_command = await travel_publisher_node(travel_query_state)
        
        assert publisher_command.goto == "travel_agent_proxy"
        assert "next" in publisher_command.update
        
        # 更新状态
        updated_state = {**travel_query_state, **publisher_command.update}
        
        # 第二步：测试Travel Agent Proxy
        with patch('src.manager.agents.agent_manager') as mock_agent_manager:
            # 模拟智能体
            mock_agent = MagicMock()
            mock_agent.llm_type = "basic"
            mock_agent.selected_tools = []
            mock_agent.prompt = "Travel agent prompt"
            
            mock_agent_manager.available_agents = {
                updated_state["next"]: mock_agent
            }
            mock_agent_manager.available_tools = {}
            
            proxy_command = await travel_agent_proxy_node(updated_state)
            
            assert hasattr(proxy_command, 'goto')
            assert hasattr(proxy_command, 'update')
    
    @pytest.mark.asyncio 
    async def test_multiple_agent_coordination(self, travel_query_state):
        """测试多智能体协调"""
        
        # 模拟需要多个智能体的复杂旅游查询
        complex_query_state = {
            **travel_query_state,
            "USER_QUERY": "我要去北京旅游，需要预订航班、酒店、安排3天的行程包括故宫天安门颐和园，还要推荐当地美食"
        }
        
        publisher = TravelPublisher()
        
        # 测试智能路由决策
        selected_agent = await publisher.intelligent_travel_routing(complex_query_state)
        
        # 应该选择综合规划智能体
        assert selected_agent in [
            "travel_planner",      # 综合规划
            "transportation_planner", # 交通规划
            "hotel_booker",        # 酒店预订
            "attraction_planner"   # 景点规划
        ]
    
    def test_travel_context_flow(self, travel_query_state):
        """测试旅游上下文在工作流中的传递"""
        
        publisher = TravelPublisher()
        
        # 提取并增强旅游上下文
        travel_context = publisher.context_enhancer.extract_context(travel_query_state)
        
        assert travel_context.destination
        assert travel_context.planned_locations
        assert travel_context.required_resources
        
        # 验证上下文完整性
        assert isinstance(travel_context.weather_forecast, dict)
        assert isinstance(travel_context.business_hours, dict)
        assert isinstance(travel_context.booking_deadlines, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self):
        """测试错误处理和降级机制"""
        
        # 测试空状态
        empty_state = {}
        
        try:
            command = await travel_publisher_node(empty_state)
            # 应该能够处理空状态并提供降级方案
            assert hasattr(command, 'goto')
        except Exception as e:
            # 如果抛出异常，应该是可预期的
            assert isinstance(e, (KeyError, ValueError, TypeError))
        
        # 测试无效智能体名称
        invalid_state = {
            "user_id": "test_user",
            "next": "invalid_agent_name",
            "USER_QUERY": "测试查询"
        }
        
        try:
            command = await travel_agent_proxy_node(invalid_state)
            # 应该能够处理无效智能体并提供降级方案
            assert hasattr(command, 'goto')
        except Exception as e:
            # 错误应该被妥善处理
            assert isinstance(e, (KeyError, ValueError, AttributeError))


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 