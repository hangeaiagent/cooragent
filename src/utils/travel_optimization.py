"""
旅游优化工具类 (Travel Optimization Utils)
包含地理计算、路线优化、时间调度、资源协调等核心算法
"""

import math
import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransportMode(Enum):
    """交通方式枚举"""
    WALKING = "walking"
    DRIVING = "driving"
    PUBLIC_TRANSIT = "public_transit"
    CYCLING = "cycling"
    FLYING = "flying"


class ActivityType(Enum):
    """活动类型枚举"""
    SIGHTSEEING = "sightseeing"
    DINING = "dining"
    SHOPPING = "shopping"
    ACCOMMODATION = "accommodation"
    TRANSPORTATION = "transportation"
    ENTERTAINMENT = "entertainment"


@dataclass
class Location:
    """地理位置数据结构"""
    id: str
    name: str
    latitude: float
    longitude: float
    category: ActivityType
    priority: int = 1
    estimated_duration: int = 60  # 分钟
    opening_hours: Dict[str, Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.opening_hours is None:
            self.opening_hours = {
                "Monday": (9, 18), "Tuesday": (9, 18), "Wednesday": (9, 18),
                "Thursday": (9, 18), "Friday": (9, 18), "Saturday": (9, 18),
                "Sunday": (9, 18)
            }


@dataclass
class TravelSegment:
    """旅行片段数据结构"""
    from_location: Location
    to_location: Location
    transport_mode: TransportMode
    distance: float  # 公里
    duration: int    # 分钟
    cost: float      # 费用
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None


@dataclass
class TimeWindow:
    """时间窗口数据结构"""
    start_time: datetime
    end_time: datetime
    activity: str
    location: Location
    flexibility: int = 30  # 弹性时间（分钟）


class GeographicCalculator:
    """地理计算器"""
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """使用Haversine公式计算两点间距离（公里）"""
        R = 6371  # 地球半径（公里）
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        return round(distance, 2)
    
    @staticmethod
    def calculate_travel_time(distance: float, transport_mode: TransportMode) -> int:
        """计算旅行时间（分钟）"""
        speed_mapping = {
            TransportMode.WALKING: 5,        # 5km/h
            TransportMode.CYCLING: 15,       # 15km/h
            TransportMode.DRIVING: 40,       # 40km/h (城市)
            TransportMode.PUBLIC_TRANSIT: 25, # 25km/h (地铁/公交)
            TransportMode.FLYING: 500        # 500km/h
        }
        
        speed = speed_mapping.get(transport_mode, 25)
        travel_time = (distance / speed) * 60  # 转换为分钟
        
        # 添加等待时间
        waiting_time = {
            TransportMode.WALKING: 0,
            TransportMode.CYCLING: 0,
            TransportMode.DRIVING: 5,
            TransportMode.PUBLIC_TRANSIT: 10,
            TransportMode.FLYING: 120
        }
        
        total_time = travel_time + waiting_time.get(transport_mode, 0)
        return max(1, int(total_time))
    
    @staticmethod
    def estimate_travel_cost(distance: float, transport_mode: TransportMode) -> float:
        """估算旅行费用（人民币）"""
        cost_mapping = {
            TransportMode.WALKING: 0,
            TransportMode.CYCLING: 0.5,      # 共享单车
            TransportMode.DRIVING: 2.0,      # 每公里油费+停车
            TransportMode.PUBLIC_TRANSIT: 0.3, # 每公里地铁/公交
            TransportMode.FLYING: 0.8        # 每公里机票成本
        }
        
        cost_per_km = cost_mapping.get(transport_mode, 1.0)
        return round(distance * cost_per_km, 2)


class LocationClustering:
    """地点聚类算法"""
    
    @staticmethod
    def k_means_clustering(locations: List[Location], k: int = 3) -> Dict[int, List[Location]]:
        """使用K-means算法对地点进行聚类"""
        if len(locations) <= k:
            return {i: [locations[i]] for i in range(len(locations))}
        
        # 初始化聚类中心
        centroids = LocationClustering._initialize_centroids(locations, k)
        
        max_iterations = 10
        for _ in range(max_iterations):
            # 分配点到最近的聚类中心
            clusters = {i: [] for i in range(k)}
            
            for location in locations:
                closest_centroid = LocationClustering._find_closest_centroid(
                    location, centroids
                )
                clusters[closest_centroid].append(location)
            
            # 更新聚类中心
            new_centroids = LocationClustering._update_centroids(clusters)
            
            # 检查收敛
            if LocationClustering._centroids_converged(centroids, new_centroids):
                break
            
            centroids = new_centroids
        
        return {k: v for k, v in clusters.items() if v}
    
    @staticmethod
    def _initialize_centroids(locations: List[Location], k: int) -> List[Tuple[float, float]]:
        """初始化聚类中心"""
        # 简化实现：选择分散的点作为初始中心
        if k == 1:
            return [(locations[0].latitude, locations[0].longitude)]
        
        centroids = []
        step = len(locations) // k
        
        for i in range(k):
            idx = min(i * step, len(locations) - 1)
            centroids.append((locations[idx].latitude, locations[idx].longitude))
        
        return centroids
    
    @staticmethod
    def _find_closest_centroid(location: Location, centroids: List[Tuple[float, float]]) -> int:
        """找到最近的聚类中心"""
        min_distance = float('inf')
        closest_centroid = 0
        
        for i, (lat, lon) in enumerate(centroids):
            distance = GeographicCalculator.haversine_distance(
                location.latitude, location.longitude, lat, lon
            )
            if distance < min_distance:
                min_distance = distance
                closest_centroid = i
        
        return closest_centroid
    
    @staticmethod
    def _update_centroids(clusters: Dict[int, List[Location]]) -> List[Tuple[float, float]]:
        """更新聚类中心"""
        new_centroids = []
        
        for cluster_locations in clusters.values():
            if cluster_locations:
                avg_lat = sum(loc.latitude for loc in cluster_locations) / len(cluster_locations)
                avg_lon = sum(loc.longitude for loc in cluster_locations) / len(cluster_locations)
                new_centroids.append((avg_lat, avg_lon))
            else:
                new_centroids.append((0, 0))  # 空集群的默认中心
        
        return new_centroids
    
    @staticmethod
    def _centroids_converged(old_centroids: List[Tuple[float, float]], 
                           new_centroids: List[Tuple[float, float]], 
                           threshold: float = 0.001) -> bool:
        """检查聚类中心是否收敛"""
        for (old_lat, old_lon), (new_lat, new_lon) in zip(old_centroids, new_centroids):
            distance = GeographicCalculator.haversine_distance(
                old_lat, old_lon, new_lat, new_lon
            )
            if distance > threshold:
                return False
        return True


class RouteOptimizer:
    """路线优化器（旅行商问题求解）"""
    
    @staticmethod
    def optimize_route(start_location: Location, 
                      destinations: List[Location],
                      transport_mode: TransportMode = TransportMode.PUBLIC_TRANSIT) -> List[Location]:
        """优化旅行路线（使用近似算法）"""
        
        if not destinations:
            return [start_location]
        
        if len(destinations) == 1:
            return [start_location] + destinations
        
        # 对于较小的问题，使用动态规划
        if len(destinations) <= 8:
            return RouteOptimizer._dp_tsp(start_location, destinations, transport_mode)
        else:
            # 对于较大的问题，使用贪心+2-opt算法
            return RouteOptimizer._greedy_2opt_tsp(start_location, destinations, transport_mode)
    
    @staticmethod
    def _dp_tsp(start: Location, destinations: List[Location], 
               transport_mode: TransportMode) -> List[Location]:
        """动态规划求解TSP（适用于小规模问题）"""
        
        all_locations = [start] + destinations
        n = len(all_locations)
        
        # 计算距离矩阵
        distance_matrix = RouteOptimizer._build_distance_matrix(all_locations)
        
        # DP状态：dp[mask][i] = 从起点出发，访问mask中的点，最后在点i的最小距离
        dp = {}
        parent = {}
        
        # 初始化
        dp[(1, 0)] = 0  # 从起点开始
        
        # 动态规划
        for mask in range(1, 1 << n):
            for u in range(n):
                if not (mask & (1 << u)):
                    continue
                
                if (mask, u) not in dp:
                    dp[(mask, u)] = float('inf')
                
                for v in range(n):
                    if u == v or not (mask & (1 << v)):
                        continue
                    
                    prev_mask = mask ^ (1 << u)
                    if (prev_mask, v) in dp:
                        new_dist = dp[(prev_mask, v)] + distance_matrix[v][u]
                        if new_dist < dp[(mask, u)]:
                            dp[(mask, u)] = new_dist
                            parent[(mask, u)] = v
        
        # 找到最优解
        full_mask = (1 << n) - 1
        min_cost = float('inf')
        last_node = -1
        
        for i in range(1, n):  # 不回到起点
            if (full_mask, i) in dp and dp[(full_mask, i)] < min_cost:
                min_cost = dp[(full_mask, i)]
                last_node = i
        
        # 重构路径
        if last_node == -1:
            return [start] + destinations  # 降级到原始顺序
        
        path = []
        mask = full_mask
        current = last_node
        
        while mask:
            path.append(current)
            if (mask, current) in parent:
                next_node = parent[(mask, current)]
                mask ^= (1 << current)
                current = next_node
            else:
                break
        
        path.reverse()
        return [all_locations[i] for i in path]
    
    @staticmethod
    def _greedy_2opt_tsp(start: Location, destinations: List[Location], 
                        transport_mode: TransportMode) -> List[Location]:
        """贪心+2-opt算法求解TSP"""
        
        all_locations = [start] + destinations
        
        # 贪心构造初始解
        route = RouteOptimizer._nearest_neighbor(all_locations)
        
        # 2-opt优化
        route = RouteOptimizer._two_opt_improvement(route)
        
        return route
    
    @staticmethod
    def _nearest_neighbor(locations: List[Location]) -> List[Location]:
        """最近邻算法构造初始路线"""
        if not locations:
            return []
        
        route = [locations[0]]
        unvisited = set(locations[1:])
        
        current = locations[0]
        
        while unvisited:
            nearest = min(unvisited, 
                         key=lambda loc: GeographicCalculator.haversine_distance(
                             current.latitude, current.longitude,
                             loc.latitude, loc.longitude
                         ))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route
    
    @staticmethod
    def _two_opt_improvement(route: List[Location]) -> List[Location]:
        """2-opt算法改进路线"""
        if len(route) < 4:
            return route
        
        improved = True
        max_iterations = 100
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    if j - i == 1:
                        continue
                    
                    # 计算当前距离
                    current_dist = (
                        GeographicCalculator.haversine_distance(
                            route[i-1].latitude, route[i-1].longitude,
                            route[i].latitude, route[i].longitude
                        ) +
                        GeographicCalculator.haversine_distance(
                            route[j-1].latitude, route[j-1].longitude,
                            route[j % len(route)].latitude, route[j % len(route)].longitude
                        )
                    )
                    
                    # 计算交换后的距离
                    new_dist = (
                        GeographicCalculator.haversine_distance(
                            route[i-1].latitude, route[i-1].longitude,
                            route[j-1].latitude, route[j-1].longitude
                        ) +
                        GeographicCalculator.haversine_distance(
                            route[i].latitude, route[i].longitude,
                            route[j % len(route)].latitude, route[j % len(route)].longitude
                        )
                    )
                    
                    if new_dist < current_dist:
                        # 执行2-opt交换
                        route[i:j] = route[i:j][::-1]
                        improved = True
        
        return route
    
    @staticmethod
    def _build_distance_matrix(locations: List[Location]) -> List[List[float]]:
        """构建距离矩阵"""
        n = len(locations)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = GeographicCalculator.haversine_distance(
                        locations[i].latitude, locations[i].longitude,
                        locations[j].latitude, locations[j].longitude
                    )
        
        return matrix


class TimeScheduler:
    """时间调度器"""
    
    @staticmethod
    def schedule_activities(activities: List[TimeWindow], 
                          constraints: Dict[str, any] = None) -> List[TimeWindow]:
        """调度活动时间（考虑约束）"""
        
        if not activities:
            return []
        
        # 按开始时间排序
        sorted_activities = sorted(activities, key=lambda x: x.start_time)
        
        # 检测并解决冲突
        scheduled = TimeScheduler._resolve_conflicts(sorted_activities, constraints or {})
        
        # 优化时间间隔
        optimized = TimeScheduler._optimize_intervals(scheduled)
        
        return optimized
    
    @staticmethod
    def _resolve_conflicts(activities: List[TimeWindow], constraints: Dict) -> List[TimeWindow]:
        """解决时间冲突"""
        
        resolved = []
        
        for activity in activities:
            # 检查与已调度活动的冲突
            conflict_found = False
            
            for scheduled in resolved:
                if TimeScheduler._has_time_conflict(activity, scheduled):
                    # 调整活动时间
                    activity = TimeScheduler._adjust_activity_time(activity, scheduled, constraints)
                    conflict_found = True
                    break
            
            resolved.append(activity)
        
        return resolved
    
    @staticmethod
    def _has_time_conflict(activity1: TimeWindow, activity2: TimeWindow) -> bool:
        """检查两个活动是否有时间冲突"""
        return not (activity1.end_time <= activity2.start_time or 
                   activity2.end_time <= activity1.start_time)
    
    @staticmethod
    def _adjust_activity_time(activity: TimeWindow, conflicting: TimeWindow, 
                             constraints: Dict) -> TimeWindow:
        """调整活动时间以避免冲突"""
        
        # 计算活动持续时间
        duration = activity.end_time - activity.start_time
        
        # 尝试在冲突活动之后安排
        new_start = conflicting.end_time + timedelta(minutes=activity.flexibility)
        new_end = new_start + duration
        
        # 检查营业时间约束
        if activity.location.opening_hours:
            day_name = new_start.strftime("%A")
            if day_name in activity.location.opening_hours:
                open_hour, close_hour = activity.location.opening_hours[day_name]
                
                # 确保在营业时间内
                day_start = new_start.replace(hour=open_hour, minute=0, second=0, microsecond=0)
                day_end = new_start.replace(hour=close_hour, minute=0, second=0, microsecond=0)
                
                if new_start < day_start:
                    new_start = day_start
                    new_end = new_start + duration
                
                if new_end > day_end:
                    # 安排到下一天
                    new_start = (new_start + timedelta(days=1)).replace(
                        hour=open_hour, minute=0, second=0, microsecond=0
                    )
                    new_end = new_start + duration
        
        return TimeWindow(
            start_time=new_start,
            end_time=new_end,
            activity=activity.activity,
            location=activity.location,
            flexibility=activity.flexibility
        )
    
    @staticmethod
    def _optimize_intervals(activities: List[TimeWindow]) -> List[TimeWindow]:
        """优化活动间隔"""
        
        if len(activities) <= 1:
            return activities
        
        optimized = [activities[0]]
        
        for i in range(1, len(activities)):
            prev_activity = optimized[-1]
            current_activity = activities[i]
            
            # 计算地点间的旅行时间
            travel_time = GeographicCalculator.calculate_travel_time(
                GeographicCalculator.haversine_distance(
                    prev_activity.location.latitude, prev_activity.location.longitude,
                    current_activity.location.latitude, current_activity.location.longitude
                ),
                TransportMode.PUBLIC_TRANSIT
            )
            
            # 确保有足够的旅行时间
            min_start = prev_activity.end_time + timedelta(minutes=travel_time + 15)  # 15分钟缓冲
            
            if current_activity.start_time < min_start:
                duration = current_activity.end_time - current_activity.start_time
                current_activity = TimeWindow(
                    start_time=min_start,
                    end_time=min_start + duration,
                    activity=current_activity.activity,
                    location=current_activity.location,
                    flexibility=current_activity.flexibility
                )
            
            optimized.append(current_activity)
        
        return optimized


class ResourceCoordinator:
    """资源协调器"""
    
    def __init__(self):
        self.resource_cache = {}
        self.booking_queue = []
    
    def coordinate_resources(self, resource_requests: List[Dict], 
                           priorities: Dict[str, int] = None) -> Dict[str, any]:
        """协调资源分配"""
        
        priorities = priorities or {}
        
        # 按优先级排序资源请求
        sorted_requests = sorted(
            resource_requests,
            key=lambda x: priorities.get(x.get('id', ''), 0),
            reverse=True
        )
        
        allocation_result = {
            'allocated': [],
            'conflicts': [],
            'alternatives': [],
            'waiting_list': []
        }
        
        for request in sorted_requests:
            result = self._process_resource_request(request)
            
            if result['status'] == 'allocated':
                allocation_result['allocated'].append(result)
            elif result['status'] == 'conflict':
                allocation_result['conflicts'].append(result)
            elif result['status'] == 'alternative':
                allocation_result['alternatives'].append(result)
            else:
                allocation_result['waiting_list'].append(result)
        
        return allocation_result
    
    def _process_resource_request(self, request: Dict) -> Dict:
        """处理单个资源请求"""
        
        resource_type = request.get('type', 'unknown')
        resource_id = request.get('id', 'unknown')
        time_slot = request.get('time_slot')
        
        # 检查资源可用性
        if self._is_resource_available(resource_id, time_slot):
            # 分配资源
            self._allocate_resource(resource_id, time_slot)
            return {
                'status': 'allocated',
                'resource_id': resource_id,
                'time_slot': time_slot,
                'confirmation': f"资源 {resource_id} 已成功分配"
            }
        else:
            # 寻找替代方案
            alternatives = self._find_alternative_resources(resource_type, time_slot)
            
            if alternatives:
                return {
                    'status': 'alternative',
                    'resource_id': resource_id,
                    'alternatives': alternatives,
                    'message': f"原资源不可用，找到 {len(alternatives)} 个替代方案"
                }
            else:
                return {
                    'status': 'waiting',
                    'resource_id': resource_id,
                    'message': "资源暂时不可用，已加入等待队列"
                }
    
    def _is_resource_available(self, resource_id: str, time_slot: any) -> bool:
        """检查资源是否可用"""
        
        if resource_id not in self.resource_cache:
            self.resource_cache[resource_id] = {'allocated_slots': set()}
        
        return time_slot not in self.resource_cache[resource_id]['allocated_slots']
    
    def _allocate_resource(self, resource_id: str, time_slot: any):
        """分配资源"""
        
        if resource_id not in self.resource_cache:
            self.resource_cache[resource_id] = {'allocated_slots': set()}
        
        self.resource_cache[resource_id]['allocated_slots'].add(time_slot)
    
    def _find_alternative_resources(self, resource_type: str, time_slot: any) -> List[Dict]:
        """寻找替代资源"""
        
        # 模拟替代资源查找
        alternatives = []
        
        if resource_type == 'hotel':
            alternatives = [
                {'id': 'hotel_alt_1', 'name': '替代酒店A', 'distance': '500m', 'price_diff': '+50'},
                {'id': 'hotel_alt_2', 'name': '替代酒店B', 'distance': '1km', 'price_diff': '-30'}
            ]
        elif resource_type == 'restaurant':
            alternatives = [
                {'id': 'restaurant_alt_1', 'name': '替代餐厅A', 'cuisine': '相同', 'rating': '4.5'},
                {'id': 'restaurant_alt_2', 'name': '替代餐厅B', 'cuisine': '相似', 'rating': '4.3'}
            ]
        elif resource_type == 'attraction':
            alternatives = [
                {'id': 'attraction_alt_1', 'name': '相似景点A', 'type': '同类', 'distance': '2km'},
                {'id': 'attraction_alt_2', 'name': '相似景点B', 'type': '同类', 'distance': '3km'}
            ]
        
        # 过滤可用的替代资源
        available_alternatives = [
            alt for alt in alternatives 
            if self._is_resource_available(alt['id'], time_slot)
        ]
        
        return available_alternatives


# 导出的优化函数接口
def optimize_travel_route(start_location: Dict, destinations: List[Dict], 
                         transport_mode: str = "public_transit") -> List[Dict]:
    """优化旅行路线的公共接口"""
    
    try:
        # 转换为内部数据结构
        start_loc = Location(
            id=start_location.get('id', 'start'),
            name=start_location.get('name', '起点'),
            latitude=start_location.get('latitude', 0.0),
            longitude=start_location.get('longitude', 0.0),
            category=ActivityType.TRANSPORTATION
        )
        
        dest_locs = []
        for i, dest in enumerate(destinations):
            dest_loc = Location(
                id=dest.get('id', f'dest_{i}'),
                name=dest.get('name', f'目的地{i+1}'),
                latitude=dest.get('latitude', 0.0),
                longitude=dest.get('longitude', 0.0),
                category=ActivityType.SIGHTSEEING,
                priority=dest.get('priority', 1)
            )
            dest_locs.append(dest_loc)
        
        # 转换交通方式
        mode_mapping = {
            "walking": TransportMode.WALKING,
            "driving": TransportMode.DRIVING,
            "public_transit": TransportMode.PUBLIC_TRANSIT,
            "cycling": TransportMode.CYCLING,
            "flying": TransportMode.FLYING
        }
        
        transport = mode_mapping.get(transport_mode, TransportMode.PUBLIC_TRANSIT)
        
        # 执行路线优化
        optimized_route = RouteOptimizer.optimize_route(start_loc, dest_locs, transport)
        
        # 转换回字典格式
        result = []
        for loc in optimized_route:
            result.append({
                'id': loc.id,
                'name': loc.name,
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'category': loc.category.value,
                'priority': loc.priority
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 路线优化错误: {e}")
        return [start_location] + destinations  # 返回原始顺序


def cluster_locations_by_proximity(locations: List[Dict], num_clusters: int = 3) -> Dict[int, List[Dict]]:
    """按地理接近度聚类地点的公共接口"""
    
    try:
        # 转换为内部数据结构
        location_objects = []
        for i, loc in enumerate(locations):
            loc_obj = Location(
                id=loc.get('id', f'loc_{i}'),
                name=loc.get('name', f'地点{i+1}'),
                latitude=loc.get('latitude', 0.0),
                longitude=loc.get('longitude', 0.0),
                category=ActivityType.SIGHTSEEING
            )
            location_objects.append(loc_obj)
        
        # 执行聚类
        clusters = LocationClustering.k_means_clustering(location_objects, num_clusters)
        
        # 转换回字典格式
        result = {}
        for cluster_id, cluster_locations in clusters.items():
            result[cluster_id] = []
            for loc in cluster_locations:
                result[cluster_id].append({
                    'id': loc.id,
                    'name': loc.name,
                    'latitude': loc.latitude,
                    'longitude': loc.longitude,
                    'category': loc.category.value
                })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 地点聚类错误: {e}")
        return {0: locations}  # 返回单一聚类


def schedule_time_windows(activities: List[Dict], constraints: Dict = None) -> List[Dict]:
    """调度时间窗口的公共接口"""
    
    try:
        # 转换为内部数据结构
        time_windows = []
        
        for activity in activities:
            start_time = activity.get('start_time')
            end_time = activity.get('end_time')
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            location = Location(
                id=activity.get('location_id', 'unknown'),
                name=activity.get('location_name', '未知地点'),
                latitude=activity.get('latitude', 0.0),
                longitude=activity.get('longitude', 0.0),
                category=ActivityType.SIGHTSEEING
            )
            
            time_window = TimeWindow(
                start_time=start_time,
                end_time=end_time,
                activity=activity.get('name', '活动'),
                location=location,
                flexibility=activity.get('flexibility', 30)
            )
            
            time_windows.append(time_window)
        
        # 执行调度
        scheduled = TimeScheduler.schedule_activities(time_windows, constraints or {})
        
        # 转换回字典格式
        result = []
        for tw in scheduled:
            result.append({
                'name': tw.activity,
                'start_time': tw.start_time.isoformat(),
                'end_time': tw.end_time.isoformat(),
                'location_id': tw.location.id,
                'location_name': tw.location.name,
                'latitude': tw.location.latitude,
                'longitude': tw.location.longitude,
                'flexibility': tw.flexibility
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 时间调度错误: {e}")
        return activities  # 返回原始活动列表 