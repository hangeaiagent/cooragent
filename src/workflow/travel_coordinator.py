"""
旅游专用协调器

提供地理感知和旅游任务智能分类功能，实现旅游请求的智能路由决策。
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from src.interface.agent import State
from langgraph.types import Command

logger = logging.getLogger(__name__)


class GeographyDetector:
    """地理位置检测器"""
    
    def __init__(self):
        # 中国主要城市和地区（包括省份、自治区）
        self.china_cities = {
            # 直辖市
            "北京", "上海", "天津", "重庆",
            # 省会城市
            "广州", "深圳", "成都", "杭州", "西安", "南京", "武汉", "郑州", 
            "沈阳", "长沙", "哈尔滨", "昆明", "南宁", "银川", "西宁", "兰州",
            "石家庄", "太原", "呼和浩特", "长春", "济南", "合肥", "南昌", 
            "福州", "海口", "贵阳", "拉萨", "乌鲁木齐",
            # 重要旅游城市
            "青岛", "大连", "厦门", "珠海", "三亚", "桂林", "丽江", "大理",
            "张家界", "九寨沟", "黄山", "泰山", "峨眉山", "庐山", "五台山",
            # 省份和自治区（作为旅游目的地）
            "广东", "浙江", "江苏", "四川", "陕西", "湖北", "湖南", "河南",
            "山东", "安徽", "江西", "福建", "海南", "云南", "贵州", "甘肃",
            "河北", "山西", "辽宁", "吉林", "黑龙江", "内蒙古", "广西", 
            "西藏", "新疆", "宁夏", "青海",
            # 特别行政区
            "香港", "澳门"
        }
        
        # 国际热门目的地
        self.international_destinations = {
            "东京", "大阪", "京都", "首尔", "釜山", "曼谷", "清迈", "新加坡",
            "吉隆坡", "雅加达", "马尼拉", "胡志明市", "河内", "金边", "仰光",
            "巴黎", "伦敦", "罗马", "马德里", "阿姆斯特丹", "柏林", "维也纳",
            "布拉格", "莫斯科", "纽约", "洛杉矶", "旧金山", "拉斯维加斯",
            "迈阿密", "多伦多", "温哥华", "悉尼", "墨尔本", "奥克兰"
        }
    
    def extract_locations(self, messages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        """提取出发地和目的地"""
        content = " ".join([msg.get("content", "") for msg in messages])
        
        # 优化的正则表达式模式
        patterns = [
            # "从A到B" 模式
            r"从([^到]{1,10}?)到([^的旅游计划预算人数天]{1,15}?)的",
            r"从([^到]{1,10}?)到([^，。！？\s]{1,15}?)[，。！？\s]",
            r"从([^去]{1,10}?)去([^，。！？\s]{1,15}?)[，。！？\s]",
            # "A到B" 模式
            r"([^，。！？\s]{1,10}?)到([^的旅游计划预算人数天]{1,15}?)的",
            r"([^，。！？\s]{1,10}?)→([^，。！？\s]{1,15}?)[，。！？\s]",
            # 更精确的表单格式
            r"出发地[：:]\s*([^目的地\s]{1,15}?)\s*目的地[：:]\s*([^，。！？\s]{1,15}?)[，。！？\s]",
            r"起点[：:]\s*([^终点\s]{1,15}?)\s*终点[：:]\s*([^，。！？\s]{1,15}?)[，。！？\s]",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                departure = self._clean_location_name(match.group(1).strip())
                destination = self._clean_location_name(match.group(2).strip())
                
                # 验证城市名称
                if self._is_valid_city_name(departure) and self._is_valid_city_name(destination):
                    logger.info(f"提取到出发地: {departure}, 目的地: {destination}")
                    return departure, destination
        
        # 如果没有找到完整的出发地-目的地对，尝试提取单一目的地
        destination = self._extract_single_destination(content)
        if destination:
            logger.info(f"提取到目的地: {destination}")
            return None, destination
        
        logger.warning(f"未能从内容中提取地理位置: {content[:100]}")
        return None, None
    
    def _clean_location_name(self, location: str) -> str:
        """清理地名，去除多余词汇"""
        # 去除前缀词汇
        prefix_words = ["请帮我制定", "我想去", "计划去", "打算去"]
        for prefix in prefix_words:
            if location.startswith(prefix):
                location = location[len(prefix):].strip()
        
        # 去除常见的修饰词（只在长度大于2时才清理，避免过度清理）
        clean_words = ["市", "省", "自治区", "特别行政区", "都", "府", "县"]
        for word in clean_words:
            if location.endswith(word) and len(location) > 2:
                location = location[:-len(word)]
                break
        
        return location.strip()
    
    def _extract_single_destination(self, content: str) -> Optional[str]:
        """提取单个目的地"""
        # 检查是否包含已知城市名
        all_cities = self.china_cities | self.international_destinations
        
        for city in all_cities:
            if city in content:
                return city
        
        return None
    
    def classify_region(self, destination: str) -> str:
        """分类目的地区域"""
        if not destination:
            return "unknown"
            
        if destination in self.china_cities:
            return "china"
        elif destination in self.international_destinations:
            return "international"
        else:
            # 启发式判断
            if any(char in destination for char in "市县区镇村"):
                return "china"
            else:
                return "international"

    def _is_valid_city_name(self, name: str) -> bool:
        """验证是否为有效的城市名"""
        if not name or len(name) > 10:
            return False
        
        # 检查是否包含明显的非城市词汇
        invalid_words = ["计划", "预算", "人数", "天", "日", "旅游", "旅行", "请", "帮我", "制定"]
        for word in invalid_words:
            if word in name:
                return False
        
        # 如果在已知城市列表中，直接返回True
        all_cities = self.china_cities | self.international_destinations
        if name in all_cities:
            return True
        
        # 简单启发式：如果包含城市相关字符，认为是有效的
        city_chars = "京沪穗深圳杭州成都西安南京重庆天津苏州武汉长沙青岛大连厦门昆明哈尔滨沈阳长春石家庄太原呼和浩特济南郑州合肥南昌福州海口南宁贵阳兰州西宁银川乌鲁木齐拉萨台北香港澳门"
        if any(char in city_chars for char in name):
            return True
        
        # 如果是英文且长度合理，也认为可能是城市名
        if name.encode('utf-8').isalpha() and 2 <= len(name) <= 15:
            return True
        
        return False


class TravelTaskClassifier:
    """旅游任务分类器"""
    
    def __init__(self):
        # 简单查询关键词
        self.simple_keywords = {
            "有什么好玩的", "推荐景点", "怎么样", "如何", "什么时候去",
            "需要签证吗", "天气怎么样", "有什么特色", "好玩吗"
        }
        
        # 复杂规划关键词
        self.complex_keywords = {
            "制定计划", "行程规划", "详细安排", "几天游", "预算", "住宿",
            "交通", "路线", "攻略", "安排", "规划"
        }
    
    def analyze_complexity(self, messages: List[Dict[str, Any]]) -> str:
        """分析任务复杂度"""
        
        # 合并所有消息内容
        content = " ".join([msg.get("content", "") for msg in messages])
        
        # 检查是否包含复杂规划关键词
        complex_count = sum(1 for keyword in self.complex_keywords if keyword in content)
        simple_count = sum(1 for keyword in self.simple_keywords if keyword in content)
        
        # 检查是否包含时间、预算、人数等规划要素
        has_dates = bool(re.search(r'\d{4}-\d{2}-\d{2}|[1-9]\d*天|[1-9]\d*日', content))
        has_budget = bool(re.search(r'预算|费用|花费|多少钱|\d+元', content))
        has_travelers = bool(re.search(r'[1-9]\d*人|一家|夫妻|情侣|朋友', content))
        
        planning_elements = sum([has_dates, has_budget, has_travelers])
        
        # 决策逻辑
        if complex_count >= 2 or planning_elements >= 2:
            return "complex"
        elif simple_count >= 1 and complex_count == 0:
            return "simple"
        elif len(content) > 50 and ("计划" in content or "规划" in content):
            return "complex"
        else:
            return "simple"


class TravelCoordinator:
    """旅游专用协调器，增强地理感知和任务分类能力"""
    
    def __init__(self):
        self.geo_detector = GeographyDetector()
        self.travel_classifier = TravelTaskClassifier()
        logger.info("TravelCoordinator 初始化完成")
    
    async def coordinate_travel_request(self, state: State) -> Command:
        """旅游请求协调逻辑"""
        
        logger.info("开始协调旅游请求")
        
        try:
            messages = state.get("messages", [])
            if not messages:
                logger.warning("没有找到消息内容")
                return Command(goto="__end__")
            
            # 1. 地理位置识别
            departure, destination = self.geo_detector.extract_locations(messages)
            logger.info(f"地理位置识别结果: 出发地={departure}, 目的地={destination}")
            
            if destination:
                travel_region = self.geo_detector.classify_region(destination)
                logger.info(f"目的地区域分类: {destination} -> {travel_region}")
            else:
                travel_region = "unknown"
                logger.warning("未能识别目的地")
            
            # 2. 任务复杂度分析
            complexity = self.travel_classifier.analyze_complexity(messages)
            logger.info(f"任务复杂度分析: {complexity}")
            
            # 3. 智能路由决策
            if complexity == "simple":
                logger.info("识别为简单查询，直接响应")
                return Command(
                    update={
                        "travel_analysis": {
                            "departure": departure,
                            "destination": destination,
                            "region": travel_region,
                            "complexity": complexity,
                            "routing_decision": "direct_response"
                        }
                    },
                    goto="__end__"
                )
            else:
                logger.info("识别为复杂规划任务，转发给旅游规划器")
                
                # 选择MCP工具配置
                mcp_config = self._select_mcp_tools(travel_region)
                
                return Command(
                    update={
                        "travel_context": {
                            "departure": departure,
                            "destination": destination,
                            "region": travel_region,
                            "complexity": complexity,
                            "mcp_config": mcp_config,
                            "routing_decision": "travel_planning"
                        }
                    },
                    goto="planner"  # 暂时使用标准planner，后续会改为travel_planner
                )
                
        except Exception as e:
            logger.error(f"旅游请求协调出错: {e}", exc_info=True)
            return Command(
                update={
                    "error": f"旅游请求协调失败: {str(e)}"
                },
                goto="__end__"
            )
    
    def _select_mcp_tools(self, travel_region: str) -> Dict[str, Any]:
        """根据旅游区域选择MCP工具配置"""
        
        if travel_region == "china":
            logger.info("🇨🇳 选择中国旅游MCP工具配置")
            return {
                "amap": {"url": "https://mcp.amap.com/sse"},
                "ctrip": {"command": "python", "args": ["tools/ctrip_server.py"]},
                "dianping": {"command": "node", "args": ["tools/dianping_server.js"]}
            }
        elif travel_region == "international":
            logger.info("🌍 选择国际旅游MCP工具配置")
            return {
                "google_maps": {"url": "https://mcp.google.com/maps"},
                "booking": {"url": "https://mcp.booking.com/sse"},
                "yelp": {"command": "python", "args": ["tools/yelp_server.py"]}
            }
        else:
            logger.info("❓ 未知区域，使用默认工具配置")
            return {
                "tavily": {"command": "python", "args": ["tools/search.py"]}
            } 