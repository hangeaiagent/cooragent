"""
测试TravelCoordinator功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.workflow.travel_coordinator import (
    TravelCoordinator, 
    GeographyDetector, 
    TravelTaskClassifier
)
from src.interface.agent import State
from langgraph.types import Command


class TestGeographyDetector:
    """测试地理位置检测器"""
    
    def setup_method(self):
        self.detector = GeographyDetector()
    
    def test_extract_locations_with_clear_pattern(self):
        """测试明确的起止点模式"""
        messages = [{"content": "请帮我制定从北京到成都的旅游计划"}]
        departure, destination = self.detector.extract_locations(messages)
        
        assert departure == "北京"
        assert destination == "成都"
    
    def test_extract_locations_with_arrow(self):
        """测试箭头模式"""
        messages = [{"content": "上海→巴黎的行程"}]
        departure, destination = self.detector.extract_locations(messages)
        
        assert departure == "上海"
        assert destination == "巴黎"
    
    def test_extract_locations_with_formal_format(self):
        """测试正式格式"""
        messages = [{"content": "出发地：广州 目的地：深圳"}]
        departure, destination = self.detector.extract_locations(messages)
        
        assert departure == "广州"
        assert destination == "深圳"
    
    def test_extract_single_destination(self):
        """测试单一目的地提取"""
        messages = [{"content": "北京有什么好玩的景点？"}]
        departure, destination = self.detector.extract_locations(messages)
        
        assert departure is None
        assert destination == "北京"
    
    def test_clean_location_name(self):
        """测试地名清理"""
        assert self.detector._clean_location_name("北京市") == "北京"
        assert self.detector._clean_location_name("四川省") == "四川"
        assert self.detector._clean_location_name("请帮我制定成都") == "成都"
    
    def test_classify_region_china(self):
        """测试中国地区分类"""
        assert self.detector.classify_region("北京") == "china"
        assert self.detector.classify_region("成都") == "china"
        assert self.detector.classify_region("上海") == "china"
    
    def test_classify_region_international(self):
        """测试国际地区分类"""
        assert self.detector.classify_region("巴黎") == "international"
        assert self.detector.classify_region("东京") == "international"
        assert self.detector.classify_region("纽约") == "international"
    
    def test_classify_region_unknown(self):
        """测试未知地区分类"""
        assert self.detector.classify_region("") == "unknown"
        assert self.detector.classify_region(None) == "unknown"
    
    def test_classify_region_heuristic_china(self):
        """测试启发式中国地区判断"""
        assert self.detector.classify_region("某某市") == "china"
        assert self.detector.classify_region("某某县") == "china"
    
    def test_classify_region_heuristic_international(self):
        """测试启发式国际地区判断"""
        assert self.detector.classify_region("SomeCity") == "international"


class TestTravelTaskClassifier:
    """测试旅游任务分类器"""
    
    def setup_method(self):
        self.classifier = TravelTaskClassifier()
    
    def test_simple_query_keywords(self):
        """测试简单查询关键词"""
        messages = [{"content": "北京有什么好玩的景点？"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "simple"
    
    def test_simple_query_how_question(self):
        """测试简单How问题"""
        messages = [{"content": "成都的天气怎么样？"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "simple"
    
    def test_complex_planning_keywords(self):
        """测试复杂规划关键词"""
        messages = [{"content": "请帮我制定3天的北京详细行程规划"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "complex"
    
    def test_complex_with_budget(self):
        """测试包含预算的复杂任务"""
        messages = [{"content": "北京旅游，预算5000元，需要住宿推荐"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "complex"
    
    def test_complex_with_dates(self):
        """测试包含日期的复杂任务"""
        messages = [{"content": "2024-08-15到2024-08-18，成都4天游安排"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "complex"
    
    def test_complex_with_travelers(self):
        """测试包含人数的复杂任务"""
        messages = [{"content": "一家三口去上海旅游，需要规划路线"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "complex"
    
    def test_complex_multiple_planning_keywords(self):
        """测试多个规划关键词"""
        messages = [{"content": "请制定详细的行程安排和住宿攻略"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "complex"
    
    def test_complex_long_content_with_planning(self):
        """测试长内容包含规划关键词"""
        messages = [{"content": "我想去成都旅游，希望你能帮我制定一个详细的计划，包括吃喝玩乐各方面"}]
        complexity = self.classifier.analyze_complexity(messages)
        assert complexity == "complex"


class TestTravelCoordinator:
    """测试旅游协调器"""
    
    def setup_method(self):
        self.coordinator = TravelCoordinator()
    
    @pytest.mark.asyncio
    async def test_coordinate_simple_query(self):
        """测试简单查询协调"""
        state = State({
            "messages": [{"content": "北京有什么好玩的？"}]
        })
        
        command = await self.coordinator.coordinate_travel_request(state)
        
        assert command.goto == "__end__"
        assert "travel_analysis" in command.update
        analysis = command.update["travel_analysis"]
        assert analysis["destination"] == "北京"
        assert analysis["region"] == "china"
        assert analysis["complexity"] == "simple"
        assert analysis["routing_decision"] == "direct_response"
    
    @pytest.mark.asyncio
    async def test_coordinate_complex_planning_china(self):
        """测试中国复杂规划协调"""
        state = State({
            "messages": [{"content": "请帮我制定从上海到成都的3天旅游计划，预算5000元"}]
        })
        
        command = await self.coordinator.coordinate_travel_request(state)
        
        assert command.goto == "planner"
        assert "travel_context" in command.update
        context = command.update["travel_context"]
        assert context["departure"] == "上海"
        assert context["destination"] == "成都"
        assert context["region"] == "china"
        assert context["complexity"] == "complex"
        assert context["routing_decision"] == "travel_planning"
        
        # 验证选择了中国MCP工具
        mcp_config = context["mcp_config"]
        assert "amap" in mcp_config
        assert "ctrip" in mcp_config
        assert "dianping" in mcp_config
    
    @pytest.mark.asyncio
    async def test_coordinate_complex_planning_international(self):
        """测试国际复杂规划协调"""
        state = State({
            "messages": [{"content": "计划从北京到巴黎的7天行程，需要详细安排"}]
        })
        
        command = await self.coordinator.coordinate_travel_request(state)
        
        assert command.goto == "planner"
        assert "travel_context" in command.update
        context = command.update["travel_context"]
        assert context["departure"] == "北京"
        assert context["destination"] == "巴黎"
        assert context["region"] == "international"
        assert context["complexity"] == "complex"
        
        # 验证选择了国际MCP工具
        mcp_config = context["mcp_config"]
        assert "google_maps" in mcp_config
        assert "booking" in mcp_config
        assert "yelp" in mcp_config
    
    @pytest.mark.asyncio
    async def test_coordinate_unknown_destination(self):
        """测试未知目的地协调"""
        state = State({
            "messages": [{"content": "请帮我制定一个SomeUnknownCity的旅游计划"}]
        })
        
        command = await self.coordinator.coordinate_travel_request(state)
        
        assert command.goto == "planner"
        context = command.update["travel_context"]
        assert context["region"] == "international"  # 未知城市默认为国际
        
        # 验证使用了默认工具配置
        mcp_config = context["mcp_config"]
        assert "google_maps" in mcp_config
    
    @pytest.mark.asyncio
    async def test_coordinate_no_messages(self):
        """测试无消息情况"""
        state = State({})
        
        command = await self.coordinator.coordinate_travel_request(state)
        
        assert command.goto == "__end__"
    
    @pytest.mark.asyncio
    async def test_coordinate_error_handling(self):
        """测试错误处理"""
        # 创建一个会抛出异常的mock state
        state = State({"messages": None})  # 这会导致异常
        
        command = await self.coordinator.coordinate_travel_request(state)
        
        assert command.goto == "__end__"
        assert "error" in command.update
    
    def test_select_mcp_tools_china(self):
        """测试中国MCP工具选择"""
        config = self.coordinator._select_mcp_tools("china")
        
        assert "amap" in config
        assert "ctrip" in config
        assert "dianping" in config
    
    def test_select_mcp_tools_international(self):
        """测试国际MCP工具选择"""
        config = self.coordinator._select_mcp_tools("international")
        
        assert "google_maps" in config
        assert "booking" in config
        assert "yelp" in config
    
    def test_select_mcp_tools_unknown(self):
        """测试未知区域MCP工具选择"""
        config = self.coordinator._select_mcp_tools("unknown")
        
        assert "tavily" in config


# 集成测试
class TestTravelCoordinatorIntegration:
    """测试TravelCoordinator集成功能"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_domestic_complex(self):
        """测试国内复杂旅游完整工作流"""
        coordinator = TravelCoordinator()
        
        # 模拟用户输入：国内复杂旅游规划
        state = State({
            "messages": [{"content": "请帮我制定从北京到成都的4天旅游计划，预算8000元，2人出行，偏爱美食体验"}]
        })
        
        command = await coordinator.coordinate_travel_request(state)
        
        # 验证协调结果
        assert command.goto == "planner"
        
        context = command.update["travel_context"]
        assert context["departure"] == "北京"
        assert context["destination"] == "成都"
        assert context["region"] == "china"
        assert context["complexity"] == "complex"
        assert context["routing_decision"] == "travel_planning"
        
        # 验证MCP工具配置
        mcp_config = context["mcp_config"]
        assert "amap" in mcp_config  # 高德地图
        assert "ctrip" in mcp_config  # 携程
        assert "dianping" in mcp_config  # 大众点评
    
    @pytest.mark.asyncio
    async def test_full_workflow_international_complex(self):
        """测试国际复杂旅游完整工作流"""
        coordinator = TravelCoordinator()
        
        # 模拟用户输入：国际复杂旅游规划
        state = State({
            "messages": [{"content": "计划从上海到东京的5天行程，需要详细的住宿和交通安排"}]
        })
        
        command = await coordinator.coordinate_travel_request(state)
        
        # 验证协调结果
        assert command.goto == "planner"
        
        context = command.update["travel_context"]
        assert context["departure"] == "上海"
        assert context["destination"] == "东京"
        assert context["region"] == "international"
        assert context["complexity"] == "complex"
        
        # 验证国际MCP工具配置
        mcp_config = context["mcp_config"]
        assert "google_maps" in mcp_config
        assert "booking" in mcp_config
        assert "yelp" in mcp_config
    
    @pytest.mark.asyncio 
    async def test_full_workflow_simple_query(self):
        """测试简单查询完整工作流"""
        coordinator = TravelCoordinator()
        
        # 模拟用户输入：简单查询
        state = State({
            "messages": [{"content": "成都有什么特色美食推荐？"}]
        })
        
        command = await coordinator.coordinate_travel_request(state)
        
        # 验证简单查询直接结束
        assert command.goto == "__end__"
        
        analysis = command.update["travel_analysis"]
        assert analysis["destination"] == "成都"
        assert analysis["region"] == "china"
        assert analysis["complexity"] == "simple"
        assert analysis["routing_decision"] == "direct_response" 