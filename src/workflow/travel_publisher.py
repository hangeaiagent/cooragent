"""
旅游专业化发布器 (Travel Publisher)
实现地理感知、时间敏感、资源协调的专业化旅游智能体工作流协调器
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from langgraph.types import Command
from src.interface.agent import State
from src.manager.agents import agent_manager
from src.llm.llm import get_llm_by_type
from src.workflow.cache import workflow_cache as cache
from src.utils.chinese_names import generate_chinese_log
from src.utils.travel_intelligence import extract_travel_context
import logging

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    SUNNY = "sunny"
    RAINY = "rainy"
    CLOUDY = "cloudy"
    SNOWY = "snowy"
    STORMY = "stormy"


@dataclass
class TravelContext:
    """旅游上下文数据结构"""
    destination: str
    current_location: Optional[str]
    planned_locations: List[str]
    travel_dates: Dict[str, str]
    weather_forecast: Dict[str, str]
    business_hours: Dict[str, Dict[str, int]]
    booking_deadlines: Dict[str, datetime]
    required_resources: List[Dict]
    budget_constraints: Dict[str, float]
    traveler_profile: Dict[str, Any]


class GeographicOptimizer:
    """地理位置优化器"""
    
    def __init__(self):
        self.distance_cache = {}
    
    def analyze_location_sequence(self, current_loc: str, planned_locs: List[str]) -> Dict:
        """分析位置序列的优化方案"""
        return {
            "clustered_locations": self._cluster_by_proximity(planned_locs),
            "optimal_route": self._calculate_optimal_route(current_loc, planned_locs),
            "travel_time_matrix": self._build_travel_time_matrix(planned_locs),
            "transportation_modes": self._recommend_transport_modes(planned_locs)
        }
    
    def _cluster_by_proximity(self, locations: List[str]) -> Dict[str, List[str]]:
        """按地理接近度聚类位置"""
        # 简化实现：按关键词聚类
        clusters = {"city_center": [], "suburbs": [], "attractions": [], "transport_hubs": []}
        
        for location in locations:
            location_lower = location.lower()
            if any(keyword in location_lower for keyword in ["市中心", "中心", "downtown", "center"]):
                clusters["city_center"].append(location)
            elif any(keyword in location_lower for keyword in ["郊区", "suburb", "outskirt"]):
                clusters["suburbs"].append(location)
            elif any(keyword in location_lower for keyword in ["景点", "景区", "attraction", "park", "museum"]):
                clusters["attractions"].append(location)
            elif any(keyword in location_lower for keyword in ["机场", "火车站", "station", "airport"]):
                clusters["transport_hubs"].append(location)
            else:
                clusters["city_center"].append(location)  # 默认分类
        
        return {k: v for k, v in clusters.items() if v}
    
    def _calculate_optimal_route(self, start: str, destinations: List[str]) -> List[str]:
        """计算最优旅行路线（简化TSP实现）"""
        if not destinations:
            return []
        
        # 简化实现：按距离和重要性排序
        route = [start]
        remaining = destinations.copy()
        
        # 优先级排序：交通枢纽 > 市中心 > 景点 > 郊区
        priority_order = ["airport", "station", "center", "downtown", "attraction", "park", "suburb"]
        
        def get_priority(location: str) -> int:
            location_lower = location.lower()
            for i, keyword in enumerate(priority_order):
                if keyword in location_lower:
                    return i
            return len(priority_order)
        
        remaining.sort(key=get_priority)
        route.extend(remaining)
        
        return route
    
    def _build_travel_time_matrix(self, locations: List[str]) -> Dict[str, Dict[str, int]]:
        """构建位置间旅行时间矩阵"""
        matrix = {}
        for loc1 in locations:
            matrix[loc1] = {}
            for loc2 in locations:
                if loc1 == loc2:
                    matrix[loc1][loc2] = 0
                else:
                    # 简化实现：基于关键词估算时间
                    estimated_time = self._estimate_travel_time(loc1, loc2)
                    matrix[loc1][loc2] = estimated_time
        return matrix
    
    def _estimate_travel_time(self, loc1: str, loc2: str) -> int:
        """估算两地间旅行时间（分钟）"""
        # 简化实现：基于地点类型估算
        base_time = 30  # 基础时间30分钟
        
        # 如果有一个是交通枢纽，减少时间
        if any(keyword in loc1.lower() or keyword in loc2.lower() 
               for keyword in ["airport", "station", "机场", "火车站"]):
            base_time -= 10
        
        # 如果都在市中心，减少时间
        if all("center" in loc.lower() or "中心" in loc 
               for loc in [loc1, loc2]):
            base_time -= 15
        
        return max(15, base_time)  # 最小15分钟
    
    def _recommend_transport_modes(self, locations: List[str]) -> Dict[str, str]:
        """推荐交通方式"""
        recommendations = {}
        
        for location in locations:
            location_lower = location.lower()
            if any(keyword in location_lower for keyword in ["airport", "机场"]):
                recommendations[location] = "地铁/机场快线"
            elif any(keyword in location_lower for keyword in ["station", "火车站"]):
                recommendations[location] = "地铁/公交"
            elif any(keyword in location_lower for keyword in ["center", "中心"]):
                recommendations[location] = "步行/地铁"
            elif any(keyword in location_lower for keyword in ["suburb", "郊区"]):
                recommendations[location] = "公交/出租车"
            else:
                recommendations[location] = "地铁/公交"
        
        return recommendations


class TravelTimeManager:
    """旅游时间管理器"""
    
    def validate_time_windows(self, current_time: datetime, 
                            business_hours: Dict, booking_deadlines: Dict) -> Dict:
        """验证时间窗口约束"""
        return {
            "valid_agents": self._get_time_valid_agents(current_time, business_hours),
            "urgent_bookings": self._identify_urgent_bookings(booking_deadlines),
            "optimal_timing": self._calculate_optimal_timing(current_time, business_hours),
            "timezone_adjustments": self._handle_timezone_differences()
        }
    
    def _get_time_valid_agents(self, current_time: datetime, 
                              business_hours: Dict) -> List[str]:
        """获取当前时间有效的智能体"""
        valid_agents = []
        current_hour = current_time.hour
        
        for agent_name, hours in business_hours.items():
            start_hour = hours.get("open", 0)
            end_hour = hours.get("close", 24)
            if start_hour <= current_hour <= end_hour:
                valid_agents.append(agent_name)
        
        return valid_agents
    
    def _identify_urgent_bookings(self, booking_deadlines: Dict) -> List[str]:
        """识别紧急预订"""
        urgent_bookings = []
        current_time = datetime.now()
        
        for booking_type, deadline in booking_deadlines.items():
            if isinstance(deadline, datetime):
                time_diff = deadline - current_time
                if time_diff <= timedelta(hours=24):  # 24小时内的截止时间
                    urgent_bookings.append(booking_type)
        
        return urgent_bookings
    
    def _calculate_optimal_timing(self, current_time: datetime, 
                                business_hours: Dict) -> Dict[str, str]:
        """计算最优执行时间"""
        optimal_timing = {}
        
        for agent_name, hours in business_hours.items():
            start_hour = hours.get("open", 9)
            end_hour = hours.get("close", 18)
            
            if current_time.hour < start_hour:
                optimal_time = f"建议{start_hour}:00后执行"
            elif current_time.hour > end_hour:
                next_day = current_time + timedelta(days=1)
                optimal_time = f"建议明天{start_hour}:00后执行"
            else:
                optimal_time = "可立即执行"
            
            optimal_timing[agent_name] = optimal_time
        
        return optimal_timing
    
    def _handle_timezone_differences(self) -> Dict[str, str]:
        """处理时区差异"""
        # 简化实现：返回时区建议
        return {
            "local_timezone": "建议使用当地时区",
            "booking_timezone": "预订请使用目的地时区",
            "coordination_timezone": "协调请使用用户时区"
        }


class ResourceCoordinator:
    """旅游资源协调器"""
    
    def __init__(self):
        self.availability_cache = {}
        self.booking_conflicts = []
    
    async def check_availability(self, required_resources: List[Dict], 
                                booking_preferences: Dict) -> Dict:
        """检查资源可用性"""
        return {
            "available_resources": await self._check_real_time_availability(required_resources),
            "booking_conflicts": self._detect_booking_conflicts(required_resources),
            "alternative_options": self._find_alternatives(required_resources),
            "priority_bookings": self._prioritize_bookings(required_resources, booking_preferences)
        }
    
    async def _check_real_time_availability(self, resources: List[Dict]) -> Dict:
        """实时检查资源可用性"""
        availability_results = {}
        
        for resource in resources:
            resource_id = resource.get("id", f"unknown_{len(availability_results)}")
            resource_type = resource.get("type", "unknown")
            
            # 模拟异步可用性检查
            await asyncio.sleep(0.1)  # 模拟API调用延迟
            
            if resource_type == "hotel":
                availability_results[resource_id] = await self._check_hotel_availability(resource)
            elif resource_type == "restaurant":
                availability_results[resource_id] = await self._check_restaurant_availability(resource)
            elif resource_type == "attraction":
                availability_results[resource_id] = await self._check_attraction_availability(resource)
            elif resource_type == "flight":
                availability_results[resource_id] = await self._check_flight_availability(resource)
            else:
                availability_results[resource_id] = {"available": True, "message": "资源类型未知，假设可用"}
        
        return availability_results
    
    async def _check_hotel_availability(self, resource: Dict) -> Dict:
        """检查酒店可用性"""
        return {
            "available": True,
            "rooms_available": 5,
            "price_range": "¥300-800/晚",
            "message": "有空房间可预订"
        }
    
    async def _check_restaurant_availability(self, resource: Dict) -> Dict:
        """检查餐厅可用性"""
        return {
            "available": True,
            "tables_available": 3,
            "waiting_time": "15分钟",
            "message": "可接受预订"
        }
    
    async def _check_attraction_availability(self, resource: Dict) -> Dict:
        """检查景点可用性"""
        return {
            "available": True,
            "tickets_available": True,
            "crowd_level": "中等",
            "message": "景点开放，建议预订门票"
        }
    
    async def _check_flight_availability(self, resource: Dict) -> Dict:
        """检查航班可用性"""
        return {
            "available": True,
            "seats_available": 12,
            "price_trend": "稳定",
            "message": "有座位可预订"
        }
    
    def _detect_booking_conflicts(self, resources: List[Dict]) -> List[str]:
        """检测预订冲突"""
        conflicts = []
        
        # 简化实现：检查时间冲突
        time_slots = {}
        for resource in resources:
            time_slot = resource.get("time_slot")
            location = resource.get("location")
            
            if time_slot and location:
                key = f"{time_slot}_{location}"
                if key in time_slots:
                    conflicts.append(f"时间冲突：{time_slot} 在 {location}")
                else:
                    time_slots[key] = resource
        
        return conflicts
    
    def _find_alternatives(self, resources: List[Dict]) -> Dict[str, List[Dict]]:
        """寻找替代方案"""
        alternatives = {}
        
        for resource in resources:
            resource_type = resource.get("type")
            resource_id = resource.get("id", "unknown")
            
            if resource_type == "hotel":
                alternatives[resource_id] = [
                    {"name": "附近酒店A", "distance": "500米", "price": "相似价位"},
                    {"name": "附近酒店B", "distance": "1公里", "price": "略低价位"}
                ]
            elif resource_type == "restaurant":
                alternatives[resource_id] = [
                    {"name": "同类餐厅A", "distance": "200米", "cuisine": "相同菜系"},
                    {"name": "同类餐厅B", "distance": "400米", "cuisine": "相同菜系"}
                ]
            else:
                alternatives[resource_id] = []
        
        return alternatives
    
    def _prioritize_bookings(self, resources: List[Dict], 
                            preferences: Dict) -> List[Dict]:
        """优先级排序预订"""
        priority_weights = {
            "flight": 10,      # 航班最高优先级
            "hotel": 8,        # 住宿次高优先级
            "attraction": 6,   # 景点中等优先级
            "restaurant": 4    # 餐厅较低优先级
        }
        
        def get_priority(resource: Dict) -> int:
            resource_type = resource.get("type", "unknown")
            base_priority = priority_weights.get(resource_type, 1)
            
            # 根据用户偏好调整优先级
            if resource.get("name") in preferences.get("favorites", []):
                base_priority += 5
            
            if resource.get("urgent", False):
                base_priority += 3
            
            return base_priority
        
        sorted_resources = sorted(resources, key=get_priority, reverse=True)
        return sorted_resources


class WeatherAdapter:
    """天气适应器"""
    
    def adapt_to_weather(self, weather_forecast: Dict, 
                        weather_dependent_tasks: List[str]) -> Dict:
        """根据天气条件适应任务安排"""
        adaptations = {}
        
        for task in weather_dependent_tasks:
            task_weather = weather_forecast.get(task, "unknown")
            adaptations[task] = self._get_weather_adaptation(task, task_weather)
        
        return {
            "weather_adaptations": adaptations,
            "recommended_changes": self._recommend_weather_changes(weather_forecast),
            "backup_plans": self._generate_backup_plans(weather_forecast)
        }
    
    def _get_weather_adaptation(self, task: str, weather: str) -> Dict:
        """获取特定任务的天气适应建议"""
        if "户外" in task or "outdoor" in task.lower():
            if weather in ["rainy", "stormy", "下雨", "暴雨"]:
                return {
                    "recommendation": "建议改为室内活动",
                    "alternative": "参观博物馆或购物中心",
                    "timing": "等待天气好转"
                }
            elif weather in ["sunny", "晴天"]:
                return {
                    "recommendation": "适合户外活动",
                    "preparation": "准备防晒用品",
                    "timing": "早上或傍晚最佳"
                }
        
        return {
            "recommendation": "按原计划进行",
            "preparation": "无特殊准备",
            "timing": "不受天气影响"
        }
    
    def _recommend_weather_changes(self, weather_forecast: Dict) -> List[str]:
        """推荐基于天气的行程变更"""
        recommendations = []
        
        for time_period, weather in weather_forecast.items():
            if weather in ["rainy", "stormy", "下雨", "暴雨"]:
                recommendations.append(f"{time_period}: 建议安排室内活动")
            elif weather in ["sunny", "晴天"]:
                recommendations.append(f"{time_period}: 适合户外观光")
            elif weather in ["cloudy", "多云"]:
                recommendations.append(f"{time_period}: 适合各类活动")
        
        return recommendations
    
    def _generate_backup_plans(self, weather_forecast: Dict) -> Dict:
        """生成天气备用计划"""
        backup_plans = {}
        
        for time_period, weather in weather_forecast.items():
            if weather in ["rainy", "stormy", "下雨", "暴雨"]:
                backup_plans[time_period] = [
                    "室内博物馆参观",
                    "购物中心游览",
                    "室内娱乐设施",
                    "酒店休息调整"
                ]
            elif weather in ["snowy", "下雪"]:
                backup_plans[time_period] = [
                    "雪景观赏",
                    "室内温泉",
                    "热饮品尝",
                    "冬季活动体验"
                ]
            else:
                backup_plans[time_period] = ["按原计划进行"]
        
        return backup_plans


class TravelContextEnhancer:
    """旅游上下文增强器"""
    
    def extract_context(self, state: State) -> TravelContext:
        """提取并增强旅游上下文"""
        user_query = state.get("USER_QUERY", "")
        
        # 使用现有的旅游智能分析
        basic_context = extract_travel_context(user_query)
        
        # 增强上下文信息
        enhanced_context = TravelContext(
            destination=basic_context.get("destination") or "未指定",
            current_location=basic_context.get("departure"),
            planned_locations=self._extract_planned_locations(user_query),
            travel_dates=basic_context.get("dates") or {},
            weather_forecast=self._get_weather_forecast(basic_context.get("destination")),
            business_hours=self._get_business_hours(),
            booking_deadlines=self._get_booking_deadlines(),
            required_resources=self._extract_required_resources(user_query),
            budget_constraints=basic_context.get("budget") or {},
            traveler_profile=basic_context.get("preferences") or {}
        )
        
        return enhanced_context
    
    def _extract_planned_locations(self, user_query: str) -> List[str]:
        """提取计划访问的地点"""
        locations = []
        
        # 简化实现：基于关键词提取
        location_keywords = ["景点", "博物馆", "公园", "商场", "机场", "火车站", "酒店", "餐厅"]
        
        for keyword in location_keywords:
            if keyword in user_query:
                locations.append(f"{keyword}区域")
        
        return locations if locations else ["市中心", "主要景点"]
    
    def _get_weather_forecast(self, destination: str) -> Dict[str, str]:
        """获取天气预报（模拟）"""
        # 模拟天气预报
        return {
            "上午": "晴天",
            "下午": "多云",
            "晚上": "晴天"
        }
    
    def _get_business_hours(self) -> Dict[str, Dict[str, int]]:
        """获取营业时间"""
        return {
            "hotel_booker": {"open": 0, "close": 24},      # 酒店24小时
            "restaurant_finder": {"open": 8, "close": 22},  # 餐厅8-22点
            "attraction_planner": {"open": 9, "close": 18}, # 景点9-18点
            "transportation_planner": {"open": 6, "close": 23} # 交通6-23点
        }
    
    def _get_booking_deadlines(self) -> Dict[str, datetime]:
        """获取预订截止时间"""
        now = datetime.now()
        return {
            "flight": now + timedelta(hours=2),      # 航班2小时前
            "hotel": now + timedelta(hours=24),      # 酒店24小时前
            "restaurant": now + timedelta(hours=4),  # 餐厅4小时前
            "attraction": now + timedelta(hours=1)   # 景点1小时前
        }
    
    def _extract_required_resources(self, user_query: str) -> List[Dict]:
        """提取所需资源"""
        resources = []
        
        if any(keyword in user_query for keyword in ["住宿", "酒店", "hotel"]):
            resources.append({"type": "hotel", "id": "hotel_1", "priority": "high"})
        
        if any(keyword in user_query for keyword in ["餐厅", "用餐", "restaurant"]):
            resources.append({"type": "restaurant", "id": "restaurant_1", "priority": "medium"})
        
        if any(keyword in user_query for keyword in ["景点", "游览", "attraction"]):
            resources.append({"type": "attraction", "id": "attraction_1", "priority": "high"})
        
        if any(keyword in user_query for keyword in ["航班", "机票", "flight"]):
            resources.append({"type": "flight", "id": "flight_1", "priority": "high"})
        
        return resources


class TravelPublisher:
    """旅游专业化发布器"""
    
    def __init__(self):
        self.geo_optimizer = GeographicOptimizer()
        self.time_manager = TravelTimeManager()
        self.resource_coordinator = ResourceCoordinator()
        self.weather_adapter = WeatherAdapter()
        self.context_enhancer = TravelContextEnhancer()
    
    async def intelligent_travel_routing(self, state: State) -> str:
        """智能旅游路由决策"""
        try:
            # 1. 提取旅游上下文
            travel_context = self.context_enhancer.extract_context(state)
            
            logger.info(f"🌍 提取旅游上下文: 目的地={travel_context.destination}")
            
            # 2. 地理优化分析
            geo_analysis = self.geo_optimizer.analyze_location_sequence(
                travel_context.current_location or "出发地",
                travel_context.planned_locations
            )
            
            # 3. 时间窗口验证
            current_time = datetime.now()
            time_analysis = self.time_manager.validate_time_windows(
                current_time,
                travel_context.business_hours,
                travel_context.booking_deadlines
            )
            
            # 4. 天气条件适应
            weather_dependent_tasks = ["户外观光", "徒步旅行", "海滩活动"]
            weather_analysis = self.weather_adapter.adapt_to_weather(
                travel_context.weather_forecast,
                weather_dependent_tasks
            )
            
            # 5. 资源可用性检查
            resource_analysis = await self.resource_coordinator.check_availability(
                travel_context.required_resources,
                {"favorites": [], "urgent": False}
            )
            
            # 6. 综合决策
            optimal_agent = self._make_routing_decision(
                geo_analysis, time_analysis, weather_analysis, resource_analysis, state
            )
            
            logger.info(f"🎯 智能路由决策: 选择智能体={optimal_agent}")
            
            return optimal_agent
            
        except Exception as e:
            logger.error(f"❌ 智能旅游路由出错: {e}")
            # 降级到标准路由
            return "agent_proxy"
    
    def _make_routing_decision(self, geo_analysis: Dict, time_analysis: Dict, 
                             weather_analysis: Dict, resource_analysis: Dict, 
                             state: State) -> str:
        """基于多维度分析做出路由决策"""
        
        # 根据查询内容选择合适的智能体
        user_query = state.get("USER_QUERY", "") or ""
        if not isinstance(user_query, str):
            user_query = ""
        user_query = user_query.lower()
        
        # 使用实际存在的智能体名称进行路由
        if any(keyword in user_query for keyword in ["航班", "机票", "交通", "flight", "transport"]):
            return "transportation_planner"  # ✅ 实际存在
        elif any(keyword in user_query for keyword in ["酒店", "住宿", "hotel", "accommodation"]):
            return "destination_expert"  # 🔄 映射到存在的智能体
        elif any(keyword in user_query for keyword in ["餐厅", "用餐", "restaurant", "dining", "美食"]):
            return "destination_expert"  # 🔄 映射到存在的智能体
        elif any(keyword in user_query for keyword in ["景点", "游览", "attraction", "sightseeing"]):
            return "itinerary_designer"  # 🔄 映射到存在的智能体
        elif any(keyword in user_query for keyword in ["预算", "费用", "cost", "budget"]):
            return "cost_calculator"  # ✅ 实际存在
        elif any(keyword in user_query for keyword in ["行程", "规划", "plan", "itinerary"]):
            return "itinerary_designer"  # ✅ 实际存在
        else:
            # 默认使用旅游协调器进行综合规划
            return "travel_coordinator"  # ✅ 实际存在


async def travel_publisher_node(state: State) -> Command[Literal["travel_agent_proxy", "agent_proxy", "agent_factory", "__end__"]]:
    """旅游专业化发布器节点"""
    
    travel_publisher = TravelPublisher()
    
    try:
        # 检查工作流模式
        workflow_mode = state.get("workflow_mode", "launch")
        
        if workflow_mode == "launch":
            # 使用智能旅游路由
            optimal_agent = await travel_publisher.intelligent_travel_routing(state)
            
            # 记录路由决策
            routing_log = generate_chinese_log(
                "travel_publisher_routing",
                f"🧭 旅游发布器智能路由: 选择智能体={optimal_agent}",
                selected_agent=optimal_agent,
                routing_mode="intelligent_travel_routing",
                context_extracted=True
            )
            logger.info(f"中文日志: {routing_log['data']['message']}")
            
        elif workflow_mode in ["production", "polish"]:
            # 使用缓存的路由决策
            optimal_agent = cache.get_next_node(state.get("workflow_id", ""))
            if not optimal_agent:
                optimal_agent = "travel_planner"  # 默认旅游规划器
                
            cache_log = generate_chinese_log(
                "travel_publisher_cache",
                f"📋 旅游发布器缓存路由: 使用缓存智能体={optimal_agent}",
                cached_agent=optimal_agent,
                workflow_mode=workflow_mode
            )
            logger.info(f"中文日志: {cache_log['data']['message']}")
        else:
            optimal_agent = "travel_planner"
        
        # 更新状态
        updated_state = {
            "next": optimal_agent,
            "travel_routing_decision": {
                "selected_agent": optimal_agent,
                "routing_mode": workflow_mode,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # 路由决策
        if optimal_agent == "FINISH":
            goto = "__end__"
        elif optimal_agent == "agent_factory":
            goto = "agent_factory"
        elif optimal_agent in ["agent_proxy", "travel_agent_proxy"]:
            # 支持两种代理路由方式兼容性
            goto = optimal_agent
        else:
            goto = "travel_agent_proxy"  # 默认使用旅游专用代理
        
        return Command(goto=goto, update=updated_state)
        
    except Exception as e:
        logger.error(f"❌ 旅游发布器节点错误: {e}")
        
        # 错误处理：降级到标准代理
        error_log = generate_chinese_log(
            "travel_publisher_error",
            f"⚠️ 旅游发布器错误降级: {str(e)}",
            error=str(e),
            fallback_agent="agent_proxy"
        )
        logger.info(f"中文日志: {error_log['data']['message']}")
        
        return Command(
            goto="agent_proxy",  # 降级到标准代理确保兼容性
            update={"next": "planner", "error": str(e)}
        ) 