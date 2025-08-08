"""
旅游专用规划器节点实现

提供专业化的旅游规划能力，包括地理智能、智能体优选、预算分析等功能。
"""

import json
import logging
import re
from typing import Literal, Dict, Any, List, Optional
from copy import deepcopy

from src.interface.agent import State
from src.llm.llm import get_llm_by_type
from src.llm.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
from src.tools import tavily_tool
from src.utils.chinese_names import generate_chinese_log
from src.workflow.cache import workflow_cache as cache
from langgraph.types import Command

logger = logging.getLogger(__name__)

class TravelContextExtractor:
    """旅游上下文提取器"""
    
    @staticmethod
    def extract_travel_context(user_query: str) -> Dict[str, Any]:
        """从用户查询中提取旅游上下文信息"""
        
        context = {
            "departure": None,
            "destination": None,
            "duration": None,
            "budget_range": None,
            "travel_type": "general",
            "complexity": "simple",
            "preferences": []
        }
        
        # 提取出发地和目的地
        location_patterns = [
            r'从(.{2,8})(?:出发|去|到)',
            r'(?:去|到|前往)(.{2,8})(?:旅游|游玩|旅行)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, user_query)
            if matches:
                if "从" in pattern:
                    context["departure"] = matches[0]
                else:
                    context["destination"] = matches[0]
        
        # 提取时间信息
        duration_patterns = [
            r'(\d+)天',
            r'(\d+)日',
            r'(\d+)个?天'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, user_query)
            if match:
                context["duration"] = int(match.group(1))
                break
        
        # 提取预算信息
        budget_patterns = [
            r'预算(\d+)(?:元|块)',
            r'(\d+)(?:元|块)预算',
            r'大概(\d+)(?:元|块)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, user_query)
            if match:
                context["budget_range"] = int(match.group(1))
                break
        
        # 分析旅游类型
        travel_types = {
            "cultural": ["文化", "历史", "博物馆", "古迹", "遗产", "传统"],
            "leisure": ["休闲", "度假", "海滩", "温泉", "放松", "悠闲"],
            "adventure": ["探险", "户外", "徒步", "登山", "极限", "冒险"],
            "business": ["商务", "会议", "出差", "工作"],
            "family": ["亲子", "家庭", "儿童", "老人", "孩子"],
            "food": ["美食", "餐厅", "小吃", "特色菜", "吃货"],
            "shopping": ["购物", "商场", "特产", "免税", "买买买"]
        }
        
        detected_types = []
        for travel_type, keywords in travel_types.items():
            if any(keyword in user_query for keyword in keywords):
                detected_types.append(travel_type)
        
        if detected_types:
            context["travel_type"] = detected_types[0]
            context["preferences"] = detected_types
        
        # 判断复杂度
        complexity_indicators = [
            "详细", "完整", "全面", "专业", "攻略", "规划",
            "行程", "安排", "路线", "预算分析", "推荐"
        ]
        
        if any(indicator in user_query for indicator in complexity_indicators):
            context["complexity"] = "complex"
        
        # 如果有多个类型或天数较长，也认为是复杂规划
        if len(detected_types) > 1 or (context["duration"] and context["duration"] > 3):
            context["complexity"] = "complex"
        
        return context

class TravelAgentSelector:
    """旅游智能体智能选择器"""
    
    def __init__(self):
        # 旅游智能体优先级映射
        self.travel_agent_priority = {
            "transportation": ["transportation_planner"],
            "itinerary": ["itinerary_designer"], 
            "budget": ["cost_calculator", "budget_optimizer"],
            "accommodation": ["destination_expert"],
            "family_travel": ["family_travel_planner"],
            "cultural": ["cultural_heritage_guide"],
            "adventure": ["adventure_travel_specialist"],
            "reporting": ["report_integrator"]
        }
    
    def select_optimal_agents(self, travel_context: Dict[str, Any]) -> List[str]:
        """根据旅游上下文选择最优智能体组合"""
        
        selected_agents = []
        travel_type = travel_context.get("travel_type", "general")
        complexity = travel_context.get("complexity", "simple")
        
        # 复杂旅游规划的核心智能体
        if complexity == "complex":
            selected_agents.extend([
                "transportation_planner",  # 交通规划
                "itinerary_designer",      # 行程设计
                "cost_calculator"          # 费用计算
            ])
        
        # 根据旅游类型添加专业智能体
        if travel_type == "cultural":
            selected_agents.append("cultural_heritage_guide")
        elif travel_type == "family":
            selected_agents.append("family_travel_planner")
        elif travel_type == "adventure":
            selected_agents.append("adventure_travel_specialist")
        
        # 检查偏好中是否包含特殊类型
        preferences = travel_context.get("preferences", [])
        if preferences:  # 确保preferences不为None
            if "family" in preferences and "family_travel_planner" not in selected_agents:
                selected_agents.append("family_travel_planner")
            if "cultural" in preferences and "cultural_heritage_guide" not in selected_agents:
                selected_agents.append("cultural_heritage_guide")
            if "adventure" in preferences and "adventure_travel_specialist" not in selected_agents:
                selected_agents.append("adventure_travel_specialist")
        
        # 预算优化（如果有预算要求）
        if travel_context.get("budget_range"):
            selected_agents.append("budget_optimizer")
        
        # 目的地专家（提供本地信息）
        if complexity == "complex":
            selected_agents.append("destination_expert")
        
        # 结果整合（必需的最后步骤）
        selected_agents.append("report_integrator")
        
        return list(set(selected_agents))  # 去重

async def travel_planner_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """旅游专用规划器节点 - 增强地理智能和专业规划"""
    
    # 提取旅游上下文
    user_query = state.get("USER_QUERY", "")
    travel_context = TravelContextExtractor.extract_travel_context(user_query)
    
    # 旅游规划启动日志
    travel_start_log = generate_chinese_log(
        "travel_planner_start",
        f"🗺️ 旅游规划器启动 - 目的地: {travel_context.get('destination', '未指定')}，"
        f"预计{travel_context.get('duration', '未知')}天行程，类型: {travel_context.get('travel_type', '通用')}",
        destination=travel_context.get("destination"),
        duration=travel_context.get("duration"),
        budget_range=travel_context.get("budget_range"),
        travel_type=travel_context.get("travel_type"),
        complexity=travel_context.get("complexity"),
        workflow_mode=state.get("workflow_mode", "unknown")
    )
    logger.info(f"中文日志: {travel_start_log['data']['message']}")
    
    content = ""
    goto = "publisher"
    
    try:
        # 1. 智能体选择优化
        agent_selector = TravelAgentSelector()
        optimal_agents = agent_selector.select_optimal_agents(travel_context)
        
        # 注入旅游上下文到状态
        state["travel_context"] = travel_context
        state["recommended_agents"] = optimal_agents
        
        # 2. 旅游信息搜索增强（默认启用）
        if state.get("search_before_planning", True) and travel_context.get("destination"):
            search_query = f"{travel_context.get('destination', '')} 旅游攻略 景点推荐 交通住宿"
            if travel_context.get("travel_type") != "general":
                search_query += f" {travel_context.get('travel_type')}"
            
            search_log = generate_chinese_log(
                "travel_search_enhancement",
                f"🔍 搜索旅游信息增强规划质量: {search_query[:50]}...",
                search_query=search_query,
                destination=travel_context.get("destination")
            )
            logger.info(f"中文日志: {search_log['data']['message']}")
            
            try:
                travel_info = await tavily_tool.ainvoke({"query": search_query})
                state["travel_search_results"] = travel_info
                
                # 将搜索结果注入到消息上下文
                if travel_info:
                    search_content = "\n\n# 旅游信息增强\n\n"
                    search_content += json.dumps([
                        {'title': item.get('title', ''), 'content': item.get('content', '')[:200]} 
                        for item in travel_info[:3]  # 只取前3个结果
                    ], ensure_ascii=False, indent=2)
                    
                    # 增强消息内容
                    messages = apply_prompt_template("travel_planner", state)
                    if messages:
                        enhanced_messages = deepcopy(messages)
                        enhanced_messages[-1]["content"] += search_content
                        messages = enhanced_messages
                else:
                    messages = apply_prompt_template("travel_planner", state)
            except Exception as e:
                logger.warning(f"旅游信息搜索失败: {e}")
                messages = apply_prompt_template("travel_planner", state)
        else:
            # 3. 应用旅游专用提示词模板
            messages = apply_prompt_template("travel_planner", state)
        
        # 4. 使用推理型LLM增强旅游分析
        llm = get_llm_by_type("reasoning")
        
        # 5. 生成旅游计划
        planning_log = generate_chinese_log(
            "travel_plan_generation",
            f"🧠 正在生成专业旅游计划，推荐智能体: {', '.join(optimal_agents[:3])}等{len(optimal_agents)}个",
            llm_type="reasoning",
            template="travel_planner",
            recommended_agents_count=len(optimal_agents)
        )
        logger.info(f"中文日志: {planning_log['data']['message']}")
        
        response = await llm.ainvoke(messages)
        content = response.content
        
        # 6. 旅游计划后处理和验证
        try:
            travel_plan_data = json.loads(content)
            
            # 注入推荐的旅游智能体到新智能体需求
            if "new_agents_needed" in travel_plan_data:
                # 基于推荐的智能体更新计划
                current_agents = [step.get("agent_name") for step in travel_plan_data.get("steps", [])]
                missing_agents = [agent for agent in optimal_agents if agent not in current_agents]
                
                if missing_agents:
                    logger.info(f"建议补充智能体: {missing_agents}")
            
            # 缓存计划步骤
            if "steps" in travel_plan_data:
                cache.set_steps(state["workflow_id"], travel_plan_data["steps"])
            
            content = json.dumps(travel_plan_data, ensure_ascii=False, indent=2)
            
            # 规划成功日志
            success_log = generate_chinese_log(
                "travel_plan_success",
                f"✅ 旅游计划生成成功 - {len(travel_plan_data.get('steps', []))}个步骤，"
                f"涉及{len(set([step.get('agent_name') for step in travel_plan_data.get('steps', [])]))}个智能体",
                steps_count=len(travel_plan_data.get("steps", [])),
                unique_agents_count=len(set([step.get("agent_name") for step in travel_plan_data.get("steps", [])])),
                has_new_agents=len(travel_plan_data.get("new_agents_needed", [])) > 0
            )
            logger.info(f"中文日志: {success_log['data']['message']}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"旅游计划JSON解析警告: {e}")
            # 不影响流程，使用原始内容
            
    except json.JSONDecodeError as e:
        logger.error(f"旅游计划JSON解析失败: {e}")
        error_log = generate_chinese_log(
            "travel_plan_json_error",
            f"❌ 旅游计划JSON格式错误: {str(e)[:100]}",
            error_type="json_decode_error"
        )
        logger.error(f"中文日志: {error_log['data']['message']}")
        goto = "__end__"
        
    except Exception as e:
        logger.error(f"旅游规划器执行错误: {e}", exc_info=True)
        error_log = generate_chinese_log(
            "travel_planner_error",
            f"❌ 旅游规划器执行异常: {str(e)[:100]}",
            error_type=type(e).__name__
        )
        logger.error(f"中文日志: {error_log['data']['message']}")
        goto = "__end__"
    
    # 完成日志
    complete_log = generate_chinese_log(
        "travel_planner_complete",
        f"🎯 旅游规划器完成，准备移交给: {goto}",
        next_node=goto,
        planning_status="completed" if goto in ["publisher", "travel_publisher"] else "terminated"
    )
    logger.info(f"中文日志: {complete_log['data']['message']}")
    
    return Command(
        update={
            "messages": [{"content": content, "tool": "travel_planner", "role": "assistant"}],
            "agent_name": "travel_planner",
            "full_plan": content,
            "travel_context": travel_context
        },
        goto=goto
    ) 