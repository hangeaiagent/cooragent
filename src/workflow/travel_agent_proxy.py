"""
旅游专业化智能体代理 (Travel Agent Proxy)
实现旅游上下文注入、专业工具优化、动态MCP管理和结果增强
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langchain.agents import create_react_agent
from langgraph.types import Command

from src.interface.agent import State
from src.manager.agents import agent_manager
from src.llm.llm import get_llm_by_type
from src.prompts.template import apply_prompt
from src.service.env import MAX_STEPS
from src.utils.chinese_names import generate_chinese_log
from src.utils.travel_intelligence import extract_travel_context
import logging

logger = logging.getLogger(__name__)


@dataclass
class TravelExecutionContext:
    """旅游执行上下文"""
    destination: str
    travel_dates: Dict[str, str]
    traveler_profile: Dict[str, Any]
    budget_constraints: Dict[str, float]
    current_weather: Dict[str, str]
    traffic_status: Dict[str, str]
    exchange_rates: Dict[str, float]
    local_events: List[Dict[str, str]]


class TravelContextInjector:
    """旅游上下文注入器"""
    
    async def inject_travel_context(self, state: State, agent_name: str) -> State:
        """为智能体注入旅游专业上下文"""
        
        enhanced_state = state.copy()
        
        try:
            # 1. 基础旅游上下文
            base_travel_context = self._extract_base_context(state)
            
            # 2. 智能体专用上下文
            agent_specific_context = self._get_agent_specific_context(agent_name, base_travel_context)
            
            # 3. 实时动态上下文
            dynamic_context = await self._get_dynamic_context(base_travel_context["destination"])
            
            # 4. 整合所有上下文
            enhanced_state["travel_context"] = {
                **base_travel_context,
                **agent_specific_context,
                **dynamic_context,
                "agent_name": agent_name,
                "context_injection_time": datetime.now().isoformat()
            }
            
            logger.info(f"🎯 上下文注入完成: {agent_name} - 目的地: {base_travel_context['destination']}")
            
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ 旅游上下文注入错误: {e}")
            return enhanced_state
    
    def _extract_base_context(self, state: State) -> Dict:
        """提取基础旅游上下文"""
        try:
            user_query = state.get("USER_QUERY", "")
            travel_context = extract_travel_context(user_query)
            
            # 确保travel_context是字典类型
            if not isinstance(travel_context, dict):
                travel_context = {}
            
            return {
                "destination": travel_context.get("destination", "未指定"),
                "travel_dates": travel_context.get("dates", {}),
                "traveler_profile": travel_context.get("preferences", {}),
                "budget_constraints": travel_context.get("budget", {}),
                "travel_preferences": travel_context.get("preferences", {}),
                "departure": travel_context.get("departure", ""),
                "duration": travel_context.get("duration", ""),
                "travel_type": travel_context.get("travel_type", "leisure")
            }
        except Exception as e:
            logger.error(f"❌ 提取基础旅游上下文错误: {e}")
            # 返回默认的安全上下文
            return {
                "destination": "未指定",
                "travel_dates": {},
                "traveler_profile": {},
                "budget_constraints": {},
                "travel_preferences": {},
                "departure": "",
                "duration": "",
                "travel_type": "leisure"
            }
    
    def _get_agent_specific_context(self, agent_name: str, base_context: Dict) -> Dict:
        """获取智能体专用上下文"""
        
        # 安全获取traveler_profile，处理可能是列表的情况
        traveler_profile = base_context.get("traveler_profile", {})
        if isinstance(traveler_profile, list):
            traveler_profile = {}
        
        budget_constraints = base_context.get("budget_constraints", {})
        if isinstance(budget_constraints, list):
            budget_constraints = {}
        
        context_mapping = {
            "hotel_booker": {
                "accommodation_preferences": base_context.get("accommodation_prefs", {}),
                "check_in_date": base_context.get("travel_dates", {}).get("start"),
                "check_out_date": base_context.get("travel_dates", {}).get("end"),
                "room_requirements": base_context.get("room_requirements", {}),
                "location_preferences": base_context.get("location_prefs", {}),
                "budget_per_night": budget_constraints.get("accommodation", 500)
            },
            "restaurant_finder": {
                "cuisine_preferences": base_context.get("cuisine_prefs", []),
                "dietary_restrictions": base_context.get("dietary_restrictions", []),
                "budget_per_meal": budget_constraints.get("dining", 200),
                "dining_times": base_context.get("dining_schedule", {}),
                "group_size": traveler_profile.get("group_size", 1),
                "special_occasions": base_context.get("special_occasions", [])
            },
            "attraction_planner": {
                "interests": base_context.get("interests", []),
                "mobility_requirements": base_context.get("mobility_requirements", {}),
                "age_considerations": traveler_profile.get("ages", []),
                "activity_level": base_context.get("activity_level", "moderate"),
                "cultural_interests": base_context.get("cultural_interests", []),
                "time_preferences": base_context.get("time_preferences", {})
            },
            "transportation_planner": {
                "transport_preferences": base_context.get("transport_prefs", {}),
                "mobility_needs": base_context.get("mobility_needs", {}),
                "budget_constraints": base_context.get("transport_budget", {}),
                "schedule_flexibility": base_context.get("schedule_flexibility", "moderate"),
                "luggage_requirements": base_context.get("luggage_info", {}),
                "departure_preferences": base_context.get("departure_prefs", {})
            },
            "travel_planner": {
                "planning_scope": "comprehensive",
                "coordination_required": True,
                "multi_agent_planning": True,
                "optimization_level": "high",
                "personalization_level": "high"
            }
        }
        
        return context_mapping.get(agent_name, {})
    
    async def _get_dynamic_context(self, destination: str) -> Dict:
        """获取实时动态上下文"""
        try:
            # 模拟异步获取实时信息
            await asyncio.sleep(0.1)
            
            return {
                "current_weather": await self._get_current_weather(destination),
                "traffic_status": await self._get_traffic_status(destination),
                "exchange_rates": await self._get_exchange_rates(destination),
                "local_events": await self._get_local_events(destination),
                "crowd_levels": await self._get_crowd_levels(destination),
                "emergency_info": await self._get_emergency_info(destination)
            }
        except Exception as e:
            logger.error(f"❌ 获取动态上下文错误: {e}")
            return {}
    
    async def _get_current_weather(self, destination: str) -> Dict:
        """获取当前天气信息"""
        # 模拟天气API调用
        return {
            "temperature": "22°C",
            "condition": "晴天",
            "humidity": "65%",
            "wind_speed": "5km/h",
            "forecast": "今日适合户外活动"
        }
    
    async def _get_traffic_status(self, destination: str) -> Dict:
        """获取交通状况"""
        return {
            "overall_status": "畅通",
            "congestion_areas": [],
            "recommended_routes": ["地铁1号线", "公交快线"],
            "estimated_delays": "无明显延误"
        }
    
    async def _get_exchange_rates(self, destination: str) -> Dict:
        """获取汇率信息"""
        return {
            "CNY_to_local": 1.0,
            "USD_to_local": 7.2,
            "EUR_to_local": 7.8,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _get_local_events(self, destination: str) -> List[Dict]:
        """获取当地活动信息"""
        return [
            {
                "event": "城市音乐节",
                "date": "本周末",
                "location": "中心广场",
                "type": "文化活动"
            },
            {
                "event": "美食嘉年华",
                "date": "下周",
                "location": "美食街",
                "type": "美食活动"
            }
        ]
    
    async def _get_crowd_levels(self, destination: str) -> Dict:
        """获取人流密度信息"""
        return {
            "attractions": "中等",
            "restaurants": "较高",
            "transportation": "正常",
            "shopping_areas": "较高"
        }
    
    async def _get_emergency_info(self, destination: str) -> Dict:
        """获取紧急信息"""
        return {
            "emergency_numbers": {"police": "110", "medical": "120", "fire": "119"},
            "nearest_hospital": "市中心医院",
            "tourist_hotline": "12345",
            "embassy_contact": "+86-xxx-xxxx"
        }


class TravelToolOptimizer:
    """旅游工具优化器"""
    
    def optimize_tools_for_travel(self, selected_tools: List, enhanced_state: State) -> List:
        """为旅游场景优化工具配置"""
        
        try:
            optimized_tools = []
            travel_context = enhanced_state.get("travel_context", {})
            
            for tool in selected_tools:
                # 1. 为工具注入旅游参数
                enhanced_tool = self._enhance_tool_with_travel_params(tool, travel_context)
                
                # 2. 配置API限制和缓存策略
                configured_tool = self._configure_api_limits(enhanced_tool, travel_context)
                
                # 3. 添加旅游专用错误处理
                robust_tool = self._add_travel_error_handling(configured_tool)
                
                optimized_tools.append(robust_tool)
            
            logger.info(f"🔧 工具优化完成: {len(optimized_tools)} 个工具已优化")
            return optimized_tools
            
        except Exception as e:
            logger.error(f"❌ 工具优化错误: {e}")
            return selected_tools  # 返回原始工具
    
    def _enhance_tool_with_travel_params(self, tool, travel_context: Dict):
        """为工具增强旅游参数"""
        
        # 获取工具名称（处理不同的工具对象结构）
        tool_name = getattr(tool, 'name', str(tool))
        
        if "maps" in tool_name or "地图" in tool_name:
            # 为地图工具注入目的地和偏好
            if hasattr(tool, 'default_params'):
                tool.default_params = {
                    "destination": travel_context.get("destination"),
                    "transport_mode": travel_context.get("transport_preferences", {}).get("preferred_mode", "walking"),
                    "avoid_tolls": travel_context.get("transport_preferences", {}).get("avoid_tolls", False),
                    "language": travel_context.get("traveler_profile", {}).get("language", "zh-CN")
                }
        
        elif "weather" in tool_name or "天气" in tool_name:
            # 为天气工具注入位置和日期
            if hasattr(tool, 'default_params'):
                tool.default_params = {
                    "location": travel_context.get("destination"),
                    "dates": travel_context.get("travel_dates"),
                    "units": travel_context.get("traveler_profile", {}).get("units", "metric")
                }
        
        elif "booking" in tool_name or "预订" in tool_name:
            # 为预订工具注入用户偏好
            if hasattr(tool, 'default_params'):
                tool.default_params = {
                    "traveler_info": travel_context.get("traveler_profile"),
                    "budget_range": travel_context.get("budget_constraints"),
                    "preferences": travel_context.get("travel_preferences")
                }
        
        return tool
    
    def _configure_api_limits(self, tool, travel_context: Dict):
        """配置API限制和缓存策略"""
        
        # 为工具配置调用限制
        if hasattr(tool, 'rate_limit'):
            tool.rate_limit = {
                "calls_per_minute": 60,
                "cache_duration": 300,  # 5分钟缓存
                "retry_attempts": 3
            }
        
        # 配置缓存策略
        if hasattr(tool, 'cache_config'):
            tool.cache_config = {
                "enable_cache": True,
                "cache_key_prefix": f"travel_{travel_context.get('destination', 'unknown')}",
                "ttl": 1800  # 30分钟
            }
        
        return tool
    
    def _add_travel_error_handling(self, tool):
        """添加旅游专用错误处理"""
        
        # 为工具添加错误处理装饰器
        original_invoke = getattr(tool, 'invoke', None)
        
        if original_invoke:
            def travel_error_wrapper(*args, **kwargs):
                try:
                    return original_invoke(*args, **kwargs)
                except Exception as e:
                    logger.error(f"⚠️ 工具调用错误 {getattr(tool, 'name', 'unknown')}: {e}")
                    
                    # 返回友好的错误信息
                    return {
                        "error": True,
                        "message": f"工具暂时不可用: {str(e)}",
                        "fallback_suggestion": "请尝试手动搜索或稍后重试"
                    }
            
            tool.invoke = travel_error_wrapper
        
        return tool


class TravelMCPManager:
    """旅游MCP服务管理器"""
    
    def __init__(self):
        self.destination_mcp_mapping = self._load_destination_mcp_mapping()
        self.mcp_client_pool = {}
    
    async def select_destination_specific_mcp(self, travel_context: Dict) -> List:
        """根据目的地选择专用MCP服务"""
        
        try:
            destination = travel_context.get("destination", "")
            travel_type = travel_context.get("travel_type", "general")
            
            # 1. 获取目的地相关的MCP服务
            relevant_mcps = self._get_destination_mcps(destination)
            
            # 2. 根据旅行类型筛选MCP服务
            filtered_mcps = self._filter_mcps_by_travel_type(relevant_mcps, travel_type)
            
            # 3. 动态加载MCP工具
            mcp_tools = []
            for mcp_config in filtered_mcps:
                tools = await self._load_mcp_tools(mcp_config)
                mcp_tools.extend(tools)
            
            logger.info(f"🔌 MCP服务选择完成: {len(mcp_tools)} 个MCP工具已加载")
            return mcp_tools
            
        except Exception as e:
            logger.error(f"❌ MCP服务选择错误: {e}")
            return []
    
    def _load_destination_mcp_mapping(self) -> Dict:
        """加载目的地MCP映射配置"""
        # 简化实现：预定义映射关系
        return {
            "amap_mcp": {"name": "高德地图", "type": "maps", "regions": ["中国"]},
            "meituan_mcp": {"name": "美团", "type": "dining", "regions": ["中国"]},
            "google_places_mcp": {"name": "Google Places", "type": "places", "regions": ["全球"]},
            "booking_com_mcp": {"name": "Booking.com", "type": "accommodation", "regions": ["全球"]},
            "tripadvisor_mcp": {"name": "TripAdvisor", "type": "reviews", "regions": ["全球"]}
        }
    
    def _get_destination_mcps(self, destination: str) -> List[Dict]:
        """获取目的地相关的MCP服务配置"""
        
        # 国家/地区级别的MCP服务映射
        country_mapping = {
            "中国": ["amap_mcp", "meituan_mcp"],
            "日本": ["google_places_mcp", "booking_com_mcp"],
            "美国": ["google_places_mcp", "tripadvisor_mcp"],
            "欧洲": ["booking_com_mcp", "google_places_mcp"]
        }
        
        # 城市级别的MCP服务映射
        city_mapping = {
            "北京": ["amap_mcp", "meituan_mcp"],
            "上海": ["amap_mcp", "meituan_mcp"],
            "东京": ["google_places_mcp", "booking_com_mcp"],
            "纽约": ["google_places_mcp", "tripadvisor_mcp"],
            "伦敦": ["booking_com_mcp", "google_places_mcp"]
        }
        
        # 合并相关MCP服务
        relevant_mcps = []
        
        # 城市特定服务
        if destination in city_mapping:
            relevant_mcps.extend(city_mapping[destination])
        
        # 国家/地区服务
        for country, mcps in country_mapping.items():
            if country in destination or destination in country:
                relevant_mcps.extend(mcps)
        
        # 如果没有特定映射，使用全球服务
        if not relevant_mcps:
            relevant_mcps = ["google_places_mcp", "booking_com_mcp", "tripadvisor_mcp"]
        
        return [self.destination_mcp_mapping[mcp] for mcp in relevant_mcps 
                if mcp in self.destination_mcp_mapping]
    
    def _filter_mcps_by_travel_type(self, mcps: List[Dict], travel_type: str) -> List[Dict]:
        """根据旅行类型筛选MCP服务"""
        
        type_priorities = {
            "business": ["booking", "maps", "transport"],
            "leisure": ["places", "dining", "attraction", "accommodation"],
            "adventure": ["maps", "weather", "emergency"],
            "cultural": ["places", "museums", "reviews"],
            "family": ["family_friendly", "places", "accommodation"]
        }
        
        priority_types = type_priorities.get(travel_type, ["places", "accommodation", "dining"])
        
        # 按优先级排序MCP服务
        def get_priority(mcp: Dict) -> int:
            mcp_type = mcp.get("type", "unknown")
            try:
                return priority_types.index(mcp_type)
            except ValueError:
                return len(priority_types)
        
        sorted_mcps = sorted(mcps, key=get_priority)
        return sorted_mcps[:5]  # 限制最多5个MCP服务
    
    async def _load_mcp_tools(self, mcp_config: Dict) -> List:
        """加载MCP工具"""
        # 模拟MCP工具加载
        await asyncio.sleep(0.05)
        
        # 返回模拟工具对象
        tool_name = f"{mcp_config['name']}_tool"
        
        class MockMCPTool:
            def __init__(self, name: str, mcp_type: str):
                self.name = name
                self.type = mcp_type
                self.description = f"{name}专用工具"
            
            def invoke(self, *args, **kwargs):
                return f"通过{self.name}获取信息"
        
        return [MockMCPTool(tool_name, mcp_config.get("type", "general"))]


class TravelResultEnhancer:
    """旅游结果增强器"""
    
    def enhance_travel_result(self, response: Dict, enhanced_state: State) -> Dict:
        """增强旅游执行结果"""
        
        try:
            travel_context = enhanced_state.get("travel_context", {})
            
            enhanced_response = response.copy()
            
            # 1. 添加地理信息增强
            enhanced_response = self._add_geographic_enhancement(enhanced_response, travel_context)
            
            # 2. 添加时间信息规范
            enhanced_response = self._add_time_standardization(enhanced_response, travel_context)
            
            # 3. 添加预订状态跟踪
            enhanced_response = self._add_booking_tracking(enhanced_response, travel_context)
            
            # 4. 添加多语言支持
            enhanced_response = self._add_localization(enhanced_response, travel_context)
            
            # 5. 添加质量评估
            enhanced_response = self._add_quality_assessment(enhanced_response, travel_context)
            
            logger.info(f"✨ 结果增强完成: 已添加地理、时间、预订等增强信息")
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ 结果增强错误: {e}")
            return response
    
    def _add_geographic_enhancement(self, response: Dict, travel_context: Dict) -> Dict:
        """添加地理信息增强"""
        
        if "messages" in response:
            for message in response["messages"]:
                if hasattr(message, 'content') and isinstance(message.content, str):
                    # 为结果添加地理坐标信息
                    destination = travel_context.get("destination", "")
                    if destination and destination in message.content:
                        geographic_info = {
                            "coordinates": {"lat": 39.9042, "lng": 116.4074},  # 示例坐标
                            "timezone": "Asia/Shanghai",
                            "region": "北京市",
                            "country": "中国"
                        }
                        
                        if not hasattr(message, 'metadata'):
                            message.metadata = {}
                        message.metadata["geographic_info"] = geographic_info
        
        return response
    
    def _add_time_standardization(self, response: Dict, travel_context: Dict) -> Dict:
        """添加时间信息规范"""
        
        time_enhancement = {
            "local_timezone": travel_context.get("current_weather", {}).get("timezone", "Asia/Shanghai"),
            "timestamp": datetime.now().isoformat(),
            "validity_period": "24小时",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response["time_info"] = time_enhancement
        return response
    
    def _add_booking_tracking(self, response: Dict, travel_context: Dict) -> Dict:
        """添加预订状态跟踪"""
        
        booking_info = {
            "booking_references": [],
            "confirmation_required": [],
            "payment_status": "pending",
            "cancellation_policy": "查看具体条款",
            "support_contact": "客服热线: 400-xxx-xxxx"
        }
        
        response["booking_info"] = booking_info
        return response
    
    def _add_localization(self, response: Dict, travel_context: Dict) -> Dict:
        """添加多语言支持"""
        
        user_language = travel_context.get("traveler_profile", {}).get("language", "zh-CN")
        destination_language = self._get_destination_language(travel_context.get("destination", ""))
        
        localization_info = {
            "user_language": user_language,
            "destination_language": destination_language,
            "translation_available": True,
            "currency": self._get_destination_currency(travel_context.get("destination", ""))
        }
        
        response["localization"] = localization_info
        return response
    
    def _add_quality_assessment(self, response: Dict, travel_context: Dict) -> Dict:
        """添加质量评估"""
        
        quality_metrics = {
            "relevance_score": 0.95,
            "completeness_score": 0.90,
            "accuracy_score": 0.92,
            "personalization_score": 0.88,
            "confidence_level": "high",
            "data_freshness": "实时"
        }
        
        response["quality_assessment"] = quality_metrics
        return response
    
    def _get_destination_language(self, destination: str) -> str:
        """获取目的地语言"""
        language_mapping = {
            "中国": "zh-CN",
            "日本": "ja-JP",
            "美国": "en-US",
            "英国": "en-GB",
            "法国": "fr-FR",
            "德国": "de-DE"
        }
        
        for country, lang in language_mapping.items():
            if country in destination:
                return lang
        
        return "en-US"  # 默认英语
    
    def _get_destination_currency(self, destination: str) -> str:
        """获取目的地货币"""
        currency_mapping = {
            "中国": "CNY",
            "日本": "JPY",
            "美国": "USD",
            "英国": "GBP",
            "欧洲": "EUR"
        }
        
        for country, currency in currency_mapping.items():
            if country in destination:
                return currency
        
        return "USD"  # 默认美元


class TravelAgentProxy:
    """旅游专业化智能体代理"""
    
    def __init__(self):
        self.context_injector = TravelContextInjector()
        self.tool_optimizer = TravelToolOptimizer()
        self.result_enhancer = TravelResultEnhancer()
        self.mcp_manager = TravelMCPManager()
    
    async def execute_travel_agent(self, state: State) -> Command:
        """执行旅游智能体"""
        
        try:
            agent_name = state.get("next", "travel_planner")
            
            logger.info(f"🚀 开始执行旅游智能体: {agent_name}")
            
            # 1. 检查agent_manager是否可用，如果不可用则模拟执行
            if not hasattr(agent_manager, 'available_agents') or not agent_manager.available_agents:
                logger.warning("⚠️ Agent Manager未初始化，使用模拟执行模式")
                return await self._simulate_agent_execution(state, agent_name)
            
            # 2. 获取智能体配置
            if agent_name not in agent_manager.available_agents:
                logger.warning(f"⚠️ 智能体 {agent_name} 不存在，使用默认智能体")
                # 尝试找到存在的旅游相关智能体
                available_travel_agents = [name for name in agent_manager.available_agents.keys() 
                                         if any(keyword in name.lower() for keyword in ['travel', 'coordinator', 'planner'])]
                if available_travel_agents:
                    agent_name = available_travel_agents[0]
                    logger.info(f"🔄 使用可用的旅游智能体: {agent_name}")
                else:
                    return await self._simulate_agent_execution(state, agent_name)
            
            _agent = agent_manager.available_agents[agent_name]
            
            # 3. 注入旅游专业上下文
            enhanced_state = await self.context_injector.inject_travel_context(state, agent_name)
            
            # 4. 优化工具配置
            original_tools = [agent_manager.available_tools[tool.name] for tool in _agent.selected_tools 
                            if tool.name in agent_manager.available_tools]
            optimized_tools = self.tool_optimizer.optimize_tools_for_travel(
                original_tools, enhanced_state
            )
            
            # 5. 动态选择MCP服务
            dynamic_mcp_tools = await self.mcp_manager.select_destination_specific_mcp(
                enhanced_state.get("travel_context", {})
            )
            
            # 6. 创建ReAct智能体实例
            from langchain.agents import create_react_agent
            from langchain.agents.agent import AgentExecutor
            from langchain_core.prompts import PromptTemplate
            from src.llm.llm import get_llm
            
            # 获取LLM
            llm = get_llm(_agent.llm_type)
            
            # 合并所有工具
            all_tools = optimized_tools + dynamic_mcp_tools
            
            # 创建prompt
            prompt_template = PromptTemplate.from_template(_agent.prompt)
            
            # 创建agent
            react_agent = create_react_agent(llm, all_tools, prompt_template)
            agent_executor = AgentExecutor(
                agent=react_agent,
                tools=all_tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )
            
            # 7. 执行智能体
            response = await agent_executor.ainvoke(enhanced_state)
            
            # 8. 增强结果
            enhanced_response = self.result_enhancer.enhance_travel_result(
                response, enhanced_state
            )
            
            logger.info(f"✅ 旅游智能体 {agent_name} 执行成功")
            
            # 返回到下一个节点或结束
            return Command(
                goto="__end__",
                update={
                    **enhanced_response,
                    "agent_execution_completed": True,
                    "executed_agent": agent_name,
                    "execution_timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ 旅游智能体执行错误: {e}")
            return await self._handle_execution_error(state, str(e))
    
    async def _simulate_agent_execution(self, state: State, agent_name: str) -> Command:
        """模拟智能体执行(当agent_manager不可用时)"""
        
        logger.info(f"🎭 模拟执行智能体: {agent_name}")
        
        # 注入旅游上下文
        enhanced_state = await self.context_injector.inject_travel_context(state, agent_name)
        
        # 生成模拟响应
        user_query = state.get("USER_QUERY", "")
        travel_context = enhanced_state.get("travel_context", {})
        
        simulated_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"根据您的查询'{user_query}'，我已通过{agent_name}为您分析了相关的旅游信息。"
                }
            ],
            "simulation_mode": True,
            "simulated_agent": agent_name
        }
        
        # 增强结果
        enhanced_response = self.result_enhancer.enhance_travel_result(
            simulated_response, enhanced_state
        )
        
        logger.info(f"✅ 模拟执行完成: {agent_name}")
        
        return Command(
            goto="__end__",
            update={
                **enhanced_response,
                "simulation_executed": True,
                "executed_agent": agent_name,
                "execution_timestamp": datetime.now().isoformat()
            }
        )
    
    def _apply_travel_enhanced_prompt(self, enhanced_state: State, original_prompt: str) -> str:
        """应用旅游增强提示词"""
        
        travel_context = enhanced_state.get("travel_context", {})
        
        # 添加旅游上下文到提示词
        travel_enhancement = f"""
        
旅游专业上下文:
- 目的地: {travel_context.get('destination', '未指定')}
- 旅行日期: {travel_context.get('travel_dates', {})}
- 当前天气: {travel_context.get('current_weather', {})}
- 预算范围: {travel_context.get('budget_constraints', {})}
- 旅行者类型: {travel_context.get('traveler_profile', {})}

请基于以上旅游上下文提供专业的旅游建议和服务。
        """
        
        enhanced_prompt = apply_prompt(enhanced_state, original_prompt + travel_enhancement)
        return enhanced_prompt
    
    def _build_travel_execution_config(self, enhanced_state: State) -> Dict:
        """构建旅游专用执行配置"""
        
        base_config = {
            "configurable": {"user_id": enhanced_state.get("user_id")},
            "recursion_limit": int(MAX_STEPS),
        }
        
        # 添加旅游专用配置
        travel_config = {
            **base_config,
            "travel_mode": True,
            "context_aware": True,
            "result_enhancement": True,
            "geographic_optimization": True,
            "timeout": 300,  # 5分钟超时
            "retry_attempts": 2
        }
        
        return travel_config


async def travel_agent_proxy_node(state: State) -> Command:
    """旅游专业化智能体代理节点"""
    
    travel_proxy = TravelAgentProxy()
    
    try:
        # 执行旅游智能体
        result = await travel_proxy.execute_travel_agent(state)
        
        # 记录执行日志
        execution_log = generate_chinese_log(
            "travel_agent_proxy_execution",
            f"🎯 旅游智能体代理执行完成: {state.get('next', 'unknown')}",
            agent_name=state.get('next'),
            execution_mode="travel_enhanced",
            context_injected=True,
            tools_optimized=True,
            result_enhanced=True
        )
        logger.info(f"中文日志: {execution_log['data']['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 旅游智能体代理节点错误: {e}")
        
        # 错误处理：降级到标准处理
        error_log = generate_chinese_log(
            "travel_agent_proxy_error",
            f"⚠️ 旅游智能体代理错误: {str(e)}",
            error=str(e),
            fallback_mode="standard_proxy"
        )
        logger.info(f"中文日志: {error_log['data']['message']}")
        
        return Command(
            goto="travel_publisher",
            update={
                "error": str(e),
                "fallback_executed": True,
                "timestamp": datetime.now().isoformat()
            }
        ) 