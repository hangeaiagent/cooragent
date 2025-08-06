"""
旅游智能分析工具

提供地理流程优化、预算分析、计划验证等专业旅游规划功能。
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def extract_travel_context(user_query: str) -> Dict[str, Any]:
    """从用户查询中提取完整的旅游上下文信息"""
    
    # 输入验证和异常处理
    if not user_query or not isinstance(user_query, str):
        user_query = ""
    
    context = {
        "departure": None,
        "destination": None,
        "duration": None,
        "budget_range": None,
        "travel_type": "general",
        "complexity": "simple",
        "preferences": [],
        "group_size": 1,
        "travel_dates": None
    }
    
    # 地理信息提取
    location_patterns = [
        r'从(.{2,10})(?:出发|去|到|前往)',
        r'(?:去|到|前往)(.{2,10})(?:旅游|游玩|旅行|玩)',
        r'(.{2,10})(?:\d+)日?游',
        r'(.{2,10})自由行'
    ]
    
    destinations = []
    departures = []
    
    for pattern in location_patterns:
        matches = re.findall(pattern, user_query)
        for match in matches:
            location = match.strip()
            if len(location) >= 2:
                if "从" in pattern:
                    departures.append(location)
                else:
                    destinations.append(location)
    
    if departures:
        context["departure"] = departures[0]
    if destinations:
        context["destination"] = destinations[0]
    
    # 时间信息提取
    duration_patterns = [
        r'(\d+)天(?:\d+)?夜?',
        r'(\d+)日游',
        r'(\d+)个?天',
        r'(\d+)夜'
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, user_query)
        if match:
            context["duration"] = int(match.group(1))
            break
    
    # 日期信息提取
    date_patterns = [
        r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})',
        r'(\d{1,2})[月\-](\d{1,2})[日号]',
        r'(\d{1,2})[月\-](\d{1,2})[日号]?[至到\-](\d{1,2})[月\-]?(\d{1,2})[日号]?'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, user_query)
        if match:
            # 简化处理，只提取找到的第一个日期模式
            context["travel_dates"] = match.group(0)
            break
    
    # 预算信息提取
    budget_patterns = [
        r'预算(\d+)(?:元|块|万)',
        r'(\d+)(?:元|块|万)预算',
        r'大概(\d+)(?:元|块|万)',
        r'(\d+)k以?内'
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, user_query)
        if match:
            budget_str = match.group(1)
            if 'k' in match.group(0).lower():
                context["budget_range"] = int(budget_str) * 1000
            elif '万' in match.group(0):
                context["budget_range"] = int(budget_str) * 10000
            else:
                context["budget_range"] = int(budget_str)
            break
    
    # 人数信息提取
    group_patterns = [
        r'(\d+)人',
        r'(\d+)个人',
        r'一家(\d+)口'
    ]
    
    for pattern in group_patterns:
        match = re.search(pattern, user_query)
        if match:
            context["group_size"] = int(match.group(1))
            break
    
    # 旅游类型分析
    travel_types = {
        "cultural": ["文化", "历史", "博物馆", "古迹", "遗产", "传统", "人文"],
        "leisure": ["休闲", "度假", "海滩", "温泉", "放松", "悠闲", "慢游"],
        "adventure": ["探险", "户外", "徒步", "登山", "极限", "冒险", "刺激"],
        "business": ["商务", "会议", "出差", "工作", "公务"],
        "family": ["亲子", "家庭", "儿童", "老人", "孩子", "带娃"],
        "food": ["美食", "餐厅", "小吃", "特色菜", "吃货", "品尝"],
        "shopping": ["购物", "商场", "特产", "免税", "买买买", "扫货"],
        "photography": ["摄影", "拍照", "打卡", "网红", "风景"],
        "romantic": ["蜜月", "情侣", "浪漫", "约会", "二人世界"]
    }
    
    detected_types = []
    for travel_type, keywords in travel_types.items():
        if any(keyword in user_query for keyword in keywords):
            detected_types.append(travel_type)
    
    if detected_types:
        context["travel_type"] = detected_types[0]
        context["preferences"] = detected_types
    
    # 复杂度判断
    complexity_indicators = [
        "详细", "完整", "全面", "专业", "攻略", "规划",
        "行程", "安排", "路线", "预算分析", "推荐",
        "包含", "涵盖", "考虑", "优化"
    ]
    
    complexity_score = sum(1 for indicator in complexity_indicators if indicator in user_query)
    
    # 多维度复杂度评估
    if (complexity_score >= 2 or 
        len(detected_types) > 1 or 
        (context["duration"] and context["duration"] > 3) or
        context["budget_range"] or
        context["group_size"] > 2):
        context["complexity"] = "complex"
    
    return context

def optimize_geographic_flow(steps: List[Dict], travel_context: Dict[str, Any]) -> List[Dict]:
    """优化地理流程，减少无效往返"""
    
    if not steps:
        return steps
    
    # 简化版地理优化：按照逻辑顺序重新排列
    optimized_steps = []
    remaining_steps = steps.copy()
    
    # 首先安排交通规划
    transport_steps = [step for step in remaining_steps if "transportation" in step.get("agent_name", "").lower()]
    for step in transport_steps:
        optimized_steps.append(step)
        remaining_steps.remove(step)
    
    # 然后安排行程设计
    itinerary_steps = [step for step in remaining_steps if "itinerary" in step.get("agent_name", "").lower()]
    for step in itinerary_steps:
        optimized_steps.append(step)
        remaining_steps.remove(step)
    
    # 接着安排专业旅游服务
    specialist_steps = [step for step in remaining_steps if any(keyword in step.get("agent_name", "").lower() 
                       for keyword in ["cultural", "family", "adventure", "destination"])]
    for step in specialist_steps:
        optimized_steps.append(step)
        remaining_steps.remove(step)
    
    # 然后安排预算计算
    budget_steps = [step for step in remaining_steps if any(keyword in step.get("agent_name", "").lower() 
                   for keyword in ["cost", "budget"])]
    for step in budget_steps:
        optimized_steps.append(step)
        remaining_steps.remove(step)
    
    # 最后安排报告整合（必须是最后一步）
    report_steps = [step for step in remaining_steps if "report" in step.get("agent_name", "").lower()]
    
    # 添加剩余步骤
    for step in remaining_steps:
        if step not in report_steps:
            optimized_steps.append(step)
    
    # 报告整合必须是最后
    for step in report_steps:
        optimized_steps.append(step)
    
    logger.info(f"地理流程优化完成：{len(steps)} -> {len(optimized_steps)} 步骤")
    
    return optimized_steps

def analyze_travel_budget(steps: List[Dict], budget_range: Optional[int]) -> Dict[str, Any]:
    """分析旅游预算分配"""
    
    if not budget_range:
        return {
            "total_budget": "未指定",
            "categories": {},
            "recommendations": ["请提供预算范围以获得更准确的费用分析"]
        }
    
    # 标准预算分配比例
    budget_allocation = {
        "transportation": 0.30,  # 交通 30%
        "accommodation": 0.35,   # 住宿 35%
        "food": 0.20,           # 餐饮 20%
        "activities": 0.10,     # 活动门票 10%
        "shopping": 0.05        # 购物纪念品 5%
    }
    
    budget_breakdown = {}
    for category, ratio in budget_allocation.items():
        budget_breakdown[category] = {
            "amount": int(budget_range * ratio),
            "percentage": f"{ratio*100:.0f}%"
        }
    
    # 根据步骤调整预算建议
    agent_names = [step.get("agent_name", "") for step in steps]
    
    recommendations = []
    if any("cultural" in name for name in agent_names):
        recommendations.append("文化旅游建议增加门票和导览费用预算")
    if any("adventure" in name for name in agent_names):
        recommendations.append("探险旅游建议增加装备和保险费用")
    if any("family" in name for name in agent_names):
        recommendations.append("亲子旅游建议增加儿童票和亲子活动费用")
    
    return {
        "total_budget": budget_range,
        "categories": budget_breakdown,
        "recommendations": recommendations,
        "budget_level": "经济" if budget_range < 2000 else "中等" if budget_range < 5000 else "充裕"
    }

def validate_travel_plan(plan: Dict[str, Any], travel_context: Dict[str, Any]) -> Dict[str, Any]:
    """验证旅游计划的合理性和完整性"""
    
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # 检查必需字段
    required_fields = ["thought", "title", "steps"]
    for field in required_fields:
        if field not in plan or not plan[field]:
            validation_result["errors"].append(f"缺少必需字段: {field}")
            validation_result["valid"] = False
    
    # 检查步骤完整性
    steps = plan.get("steps", [])
    if not steps:
        validation_result["errors"].append("计划必须包含具体的执行步骤")
        validation_result["valid"] = False
        return validation_result
    
    # 检查智能体使用规则
    agent_usage = {}
    for step in steps:
        agent_name = step.get("agent_name", "")
        agent_usage[agent_name] = agent_usage.get(agent_name, 0) + 1
    
    # 除了reporter外，其他智能体只能使用一次
    for agent, count in agent_usage.items():
        if agent != "reporter" and count > 1:
            validation_result["warnings"].append(f"智能体 {agent} 被使用了 {count} 次，建议合并相关任务")
    
    # 检查是否包含reporter作为最后步骤
    if not steps or steps[-1].get("agent_name") != "reporter":
        validation_result["warnings"].append("建议使用 reporter 作为最后的汇总步骤")
    
    # 检查旅游专业性
    agent_names = [step.get("agent_name", "") for step in steps]
    travel_agents = [name for name in agent_names if any(keyword in name 
                    for keyword in ["travel", "transportation", "itinerary", "destination", "cultural", "adventure"])]
    
    if len(travel_agents) < 2 and travel_context.get("complexity") == "complex":
        validation_result["suggestions"].append("复杂旅游规划建议使用更多专业旅游智能体")
    
    # 检查地理逻辑
    if travel_context.get("destination") and travel_context.get("duration"):
        if len(steps) < travel_context["duration"]:
            validation_result["suggestions"].append(f"行程{travel_context['duration']}天但只有{len(steps)}个步骤，建议增加详细安排")
    
    return validation_result

def format_travel_search_results(search_results: List[Dict]) -> str:
    """格式化旅游搜索结果用于增强规划"""
    
    if not search_results:
        return "暂无相关旅游信息"
    
    formatted_content = ""
    for i, result in enumerate(search_results[:3], 1):  # 只取前3个结果
        title = result.get("title", f"信息 {i}")
        content = result.get("content", "")[:200]  # 限制内容长度
        
        formatted_content += f"\n### {title}\n{content}...\n"
    
    return formatted_content

def generate_travel_insights(travel_context: Dict[str, Any]) -> Dict[str, Any]:
    """生成旅游洞察和建议"""
    
    insights = {
        "seasonal_advice": "",
        "budget_tips": [],
        "cultural_notes": [],
        "practical_tips": []
    }
    
    destination = travel_context.get("destination", "")
    travel_type = travel_context.get("travel_type", "general")
    duration = travel_context.get("duration")
    
    # 季节性建议
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:
        insights["seasonal_advice"] = "冬季出行注意保暖，部分景点可能受天气影响"
    elif current_month in [6, 7, 8]:
        insights["seasonal_advice"] = "夏季出行注意防晒防暑，提前预订住宿"
    
    # 预算建议
    if travel_context.get("budget_range"):
        budget = travel_context["budget_range"]
        if duration and budget:
            daily_budget = budget / duration
            if daily_budget < 200:
                insights["budget_tips"].append("预算较紧，建议选择经济型住宿和公共交通")
            elif daily_budget > 800:
                insights["budget_tips"].append("预算充足，可以选择高品质服务和体验")
    
    # 文化注意事项
    if travel_type == "cultural":
        insights["cultural_notes"].append("参观文化景点时请注意着装和行为规范")
        insights["cultural_notes"].append("建议提前了解当地历史文化背景")
    
    # 实用建议
    if duration and duration <= 3:
        insights["practical_tips"].append("短途旅行建议轻装出行，重点体验核心景点")
    elif duration and duration >= 7:
        insights["practical_tips"].append("长途旅行建议合理安排休息时间，避免过度疲劳")
    
    return insights 