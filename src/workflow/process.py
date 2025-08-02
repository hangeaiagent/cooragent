import logging
import hashlib
import asyncio
from typing import Any
from collections.abc import AsyncGenerator
from src.workflow import build_graph, agent_factory_graph
from src.manager import agent_manager
from src.interface.agent import TaskType
from rich.console import Console
from src.interface.agent import State
from src.service.env import USE_BROWSER
from src.workflow.cache import workflow_cache as cache
from src.workflow.graph import CompiledWorkflow
from src.interface.agent import WorkMode
from src.utils.chinese_names import (
    generate_chinese_log,
    format_agent_progress_log,
    get_agent_chinese_name
)
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

console = Console()


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    logging.getLogger("src").setLevel(logging.DEBUG)


def is_travel_related_task(messages: list) -> bool:
    """检测是否为旅游相关任务"""
    travel_keywords = [
        "旅游", "旅行", "出行", "度假", "行程", "景点", "机票", "酒店", 
        "住宿", "预订", "攻略", "自由行", "跟团", "导游", "门票",
        "新疆", "西藏", "云南", "海南", "北京", "上海", "成都", "杭州"
    ]
    
    # 合并所有消息内容
    content = " ".join([msg.get("content", "") if isinstance(msg, dict) else str(msg) for msg in messages])
    
    # 检查是否包含旅游关键词
    travel_score = sum(1 for keyword in travel_keywords if keyword in content)
    
    # 检查是否包含明确的旅游规划要素
    has_dates = bool(re.search(r'\d{4}-\d{2}-\d{2}|[1-9]\d*天|[1-9]\d*日', content))
    has_budget = bool(re.search(r'预算|费用|花费|多少钱|\d+元', content))
    has_travelers = bool(re.search(r'[1-9]\d*人|一家|夫妻|情侣|朋友', content))
    
    planning_elements = sum([has_dates, has_budget, has_travelers])
    
    # 判断逻辑：包含旅游关键词 或 包含多个规划要素
    is_travel = travel_score >= 1 or planning_elements >= 2
    
    if is_travel:
        logger.info(f"🎯 检测到旅游任务: 关键词匹配={travel_score}, 规划要素={planning_elements}")
    
    return is_travel


logger = logging.getLogger(__name__)

if USE_BROWSER:
    DEFAULT_TEAM_MEMBERS_DESCRIPTION = """
        - **`coder`**: Executes Python or Bash commands, performs mathematical calculations, and outputs a Markdown report. Must be used for all mathematical computations.
        - **`browser`**: Directly interacts with web pages, performing complex operations and interactions. You can also leverage `browser` to perform in-domain search, like Facebook, Instagram, Github, etc.
        - **`reporter`**: Write a professional report based on the result of each step.
        - **`agent_factory`**: Create a new agent based on the user's requirement.
        """
else:
    DEFAULT_TEAM_MEMBERS_DESCRIPTION = """
        - **`researcher`**: Uses search engines and web crawlers to gather information from the internet. Outputs a Markdown report summarizing findings. Researcher can not do math or programming.
        - **`coder`**: Executes Python or Bash commands, performs mathematical calculations, and outputs a Markdown report. Must be used for all mathematical computations.
        - **`reporter`**: Write a professional report based on the result of each step.
        - **`agent_factory`**: Create a new agent based on the user's requirement.
        """

TEAM_MEMBERS_DESCRIPTION_TEMPLATE = """
- **`{agent_name}`**: {agent_description}
"""
# Cache for coordinator messages
coordinator_cache = []
MAX_CACHE_SIZE = 2


async def run_agent_workflow(
    user_id: str,
    task_type: str,
    user_input_messages: list,
    debug: bool = False,
    deep_thinking_mode: bool = False,
    search_before_planning: bool = False,
    coor_agents: list[str] | None = None,
    polish_id: str = None,
    lap: int = 0,
    workmode: WorkMode = "launch",
    workflow_id: str = None,
    polish_instruction: str = None,
):
    """Run the agent workflow with the given user input.

    Args:
        user_input_messages: The user request messages
        debug: If True, enables debug level logging

    Returns:
        The final state after the workflow completes
    """
    if not workflow_id:
        if not polish_id:
            if workmode == "launch":
                msg = f"{user_id}_{task_type}_{user_input_messages}_{deep_thinking_mode}_{search_before_planning}_{coor_agents}"
                polish_id = hashlib.md5(msg.encode("utf-8")).hexdigest()
            else:
                polish_id = cache.get_latest_polish_id(user_id)

        workflow_id = f"{user_id}:{polish_id}"
    lap = cache.get_lap(workflow_id) if workmode != "launch" else 0

    if workmode != "production":
        lap = lap + 1

    cache.init_cache(
        user_id=user_id,
        mode=workmode,
        workflow_id=workflow_id,
        lap=lap,
        version=1,
        user_input_messages=user_input_messages.copy(),
        deep_thinking_mode=deep_thinking_mode,
        search_before_planning=search_before_planning,
        coor_agents=coor_agents,
    )

    if task_type == TaskType.AGENT_FACTORY:
        graph = agent_factory_graph()
    else:
        graph = build_graph()
    if not user_input_messages:
        raise ValueError("Input could not be empty")

    if debug:
        enable_debug_logging()

    logger.info(f"Starting workflow with user input: {user_input_messages}")
    
    # 添加工作流启动中文日志
    workflow_start_log = generate_chinese_log(
        "workflow_init",
        "🚀 开始初始化Cooragent多智能体工作流",
        workflow_id=workflow_id,
        user_id=user_id,
        task_type=task_type,
        user_input=user_input_messages[-1]["content"][:200] if user_input_messages else "",
        debug_mode=debug,
        deep_thinking_mode=deep_thinking_mode,
        search_before_planning=search_before_planning
    )
    logger.info(f"中文日志: {workflow_start_log['data']['message']}")

    TEAM_MEMBERS_DESCRIPTION_TEMPLATE = """
    - **`{agent_name}`**: {agent_description}
    """
    TOOLS_DESCRIPTION_TEMPLATE = """
    - **`{tool_name}`**: {tool_description}
    """
    TOOLS_DESCRIPTION = """
    """
    TEAM_MEMBERS_DESCRIPTION = DEFAULT_TEAM_MEMBERS_DESCRIPTION
    TEAM_MEMBERS = ["agent_factory"]
    for agent in agent_manager.available_agents.values():
        if agent.user_id == "share":
            TEAM_MEMBERS.append(agent.agent_name)

        if agent.user_id == user_id or (coor_agents and agent.agent_name in coor_agents):
            TEAM_MEMBERS.append(agent.agent_name)

        if agent.user_id != "share":
            MEMBER_DESCRIPTION = TEAM_MEMBERS_DESCRIPTION_TEMPLATE.format(
                agent_name=agent.agent_name, agent_description=agent.description
            )
            TEAM_MEMBERS_DESCRIPTION += "\n" + MEMBER_DESCRIPTION

    for tool_name, tool in agent_manager.available_tools.items():
        TOOLS_DESCRIPTION += "\n" + TOOLS_DESCRIPTION_TEMPLATE.format(
            tool_name=tool_name, tool_description=tool.description
        )

    # 记录团队组建完成日志
    team_setup_log = generate_chinese_log(
        "team_setup",
        f"👥 智能体团队组建完成: {len(TEAM_MEMBERS)}个智能体，{len(agent_manager.available_tools)}个工具",
        team_members=TEAM_MEMBERS,
        team_size=len(TEAM_MEMBERS),
        available_tools_count=len(agent_manager.available_tools),
        coordinator_agents=coor_agents or []
    )
    logger.info(f"中文日志: {team_setup_log['data']['message']}")

    global coordinator_cache
    coordinator_cache = []
    global is_handoff_case
    is_handoff_case = False

    async for event_data in _process_workflow(
        graph,
        {
            "user_id": user_id,
            "TEAM_MEMBERS": TEAM_MEMBERS,
            "TEAM_MEMBERS_DESCRIPTION": TEAM_MEMBERS_DESCRIPTION,
            "TOOLS": TOOLS_DESCRIPTION,
            "USER_QUERY": user_input_messages[-1]["content"],
            "messages": user_input_messages,
            "deep_thinking_mode": deep_thinking_mode,
            "search_before_planning": search_before_planning,
            "workflow_id": workflow_id,
            "workflow_mode": workmode,
            "polish_instruction": polish_instruction,
            "initialized": False,
        },
    ):
        yield event_data


async def _process_workflow(
    workflow: CompiledWorkflow, initial_state: dict[str, Any]
) -> AsyncGenerator[dict[str, Any], None]:
    """处理自定义工作流的事件流"""
    current_node = None

    workflow_id = initial_state["workflow_id"]
    
    # 检测是否为旅游任务
    user_messages = initial_state.get("messages", [])
    if is_travel_related_task(user_messages):
        logger.info("🎯 检测到旅游任务，启动旅游专用协调器")
        
        # 输出旅游工作流开始日志
        travel_workflow_start_log = generate_chinese_log(
            "travel_workflow_start", 
            "🧳 启动旅游专用智能体工作流",
            workflow_id=workflow_id,
            user_query=initial_state.get("USER_QUERY", "")[:150]
        )
        logger.info(f"中文日志: {travel_workflow_start_log['data']['message']}")
        
        yield {
            "event": "travel_workflow_start",
            "data": {"workflow_id": workflow_id, "message": "启动旅游专用工作流"},
        }
        
        # 导入和调用TravelCoordinator
        try:
            from src.workflow.travel_coordinator import TravelCoordinator
            
            # 创建TravelCoordinator实例
            travel_coordinator = TravelCoordinator()
            
            # 构建State对象
            state = State({
                "messages": user_messages,
                "user_id": initial_state.get("user_id"),
                "workflow_id": workflow_id
            })
            
            # 调用旅游协调器
            logger.info("🧳 调用TravelCoordinator进行旅游请求分析")
            command = await travel_coordinator.coordinate_travel_request(state)
            
            yield {
                "event": "travel_coordinator_complete",
                "data": {
                    "workflow_id": workflow_id,
                    "routing_decision": command.goto,
                    "analysis": command.update if hasattr(command, 'update') else {}
                },
            }
            
            # 如果是简单查询，直接返回结果
            if command.goto == "__end__":
                analysis = command.update.get("travel_analysis", {}) if hasattr(command, 'update') else {}
                
                # 生成简单查询响应
                simple_response = f"""
# 旅游信息查询结果

## 目的地：{analysis.get('destination', '未识别')}
**区域分类**: {analysis.get('region', '未知')}

根据您的查询，我为您提供以下信息：

### 基础信息
- 目的地：{analysis.get('destination', '未识别')}
- 地理区域：{'中国境内' if analysis.get('region') == 'china' else '国际目的地' if analysis.get('region') == 'international' else '未确定'}

### 建议
如果您需要详细的旅游规划，请提供：
1. 出行时间（具体日期）
2. 出行人数
3. 预算范围
4. 旅行偏好

这样我可以为您制定更详细的旅游计划。
"""
                
                yield {
                    "event": "workflow_complete",
                    "data": {
                        "workflow_id": workflow_id,
                        "result": simple_response,
                        "type": "simple_travel_query"
                    },
                }
                return
            
            # 如果是复杂规划，继续执行标准工作流，但注入旅游上下文
            elif command.goto == "planner":
                if hasattr(command, 'update') and 'travel_context' in command.update:
                    travel_context = command.update['travel_context']
                    
                    # 将旅游上下文注入到initial_state
                    initial_state['travel_context'] = travel_context
                    initial_state['is_travel_task'] = True
                    
                    logger.info(f"🧳 旅游上下文已注入: 出发地={travel_context.get('departure')}, 目的地={travel_context.get('destination')}, 区域={travel_context.get('region')}")
                    
                    yield {
                        "event": "travel_context_injected", 
                        "data": {
                            "workflow_id": workflow_id,
                            "travel_context": travel_context
                        },
                    }
        
        except Exception as e:
            logger.error(f"TravelCoordinator调用失败: {e}", exc_info=True)
            yield {
                "event": "travel_coordinator_error",
                "data": {"workflow_id": workflow_id, "error": str(e)},
            }
    
    # 输出工作流开始中文日志
    workflow_start_log = generate_chinese_log(
        "workflow_start",
        "🎯 开始执行多智能体协作工作流",
        workflow_id=workflow_id,
        start_node=workflow.start_node,
        total_team_members=len(initial_state.get("TEAM_MEMBERS", [])),
        user_query=initial_state.get("USER_QUERY", "")[:150]
    )
    logger.info(f"中文日志: {workflow_start_log['data']['message']}")
    
    yield {
        "event": "start_of_workflow",
        "data": {"workflow_id": workflow_id, "input": initial_state["messages"]},
    }

    try:
        current_node = workflow.start_node
        state = State(**initial_state)
        step_count = 0

        while current_node != "__end__":
            step_count += 1
            agent_name = current_node
            
            # 智能体启动中文日志
            agent_start_log = generate_chinese_log(
                "agent_start",
                format_agent_progress_log(agent_name, "start"),
                agent_name=agent_name,
                agent_chinese_name=get_agent_chinese_name(agent_name),
                step_number=step_count,
                workflow_id=workflow_id,
                workflow_progress=f"第{step_count}步"
            )
            logger.info(f"中文日志: {agent_start_log['data']['message']}")
            logger.info(f"Started node: {agent_name}")

            yield {
                "event": "start_of_agent",
                "data": {
                    "agent_name": agent_name,
                    "agent_id": f"{workflow_id}_{agent_name}_1",
                },
            }
            node_func = workflow.nodes[current_node]
            command = await node_func(state)

            if hasattr(command, "update") and command.update:
                for key, value in command.update.items():
                    if key != "messages":
                        state[key] = value

                    if key == "messages" and isinstance(value, list) and value:
                        # State ignores coordinator messages, which not only lacks contextual benefits
                        # but may also cause other unpredictable effects.
                        if agent_name != "coordinator":
                            state["messages"] += value
                        last_message = value[-1]
                        if "content" in last_message:
                            if agent_name == "coordinator":
                                content = last_message["content"]
                                if content.startswith("handover"):
                                    # mark handoff, do not send maesages
                                    global is_handoff_case
                                    is_handoff_case = True
                                    continue
                            if agent_name in ["planner", "coordinator", "agent_proxy"]:
                                content = last_message["content"]
                                chunk_size = 10  # send 10 words for each chunk
                                for i in range(0, len(content), chunk_size):
                                    chunk = content[i : i + chunk_size]
                                    if "processing_agent_name" in state:
                                        agent_name = state["processing_agent_name"]

                                    yield {
                                        "event": "messages",
                                        "agent_name": agent_name,
                                        "data": {
                                            "message_id": f"{workflow_id}_{agent_name}_msg_{i}",
                                            "delta": {"content": chunk},
                                        },
                                    }
                                    await asyncio.sleep(0.01)

                    if agent_name == "agent_factory" and key == "new_agent_name":
                        # 记录新智能体创建日志
                        new_agent_log = generate_chinese_log(
                            "new_agent_created",
                            f"🎉 成功创建新智能体: {get_agent_chinese_name(value)}",
                            new_agent_name=value,
                            new_agent_chinese_name=get_agent_chinese_name(value),
                            created_by="agent_factory",
                            workflow_id=workflow_id
                        )
                        logger.info(f"中文日志: {new_agent_log['data']['message']}")
                        
                        yield {
                            "event": "new_agent_created",
                            "agent_name": value,
                            "data": {
                                "new_agent_name": value,
                                "agent_obj": agent_manager.available_agents[value],
                            },
                        }

            # 智能体完成中文日志
            agent_complete_log = generate_chinese_log(
                "agent_complete",
                format_agent_progress_log(agent_name, "complete"),
                agent_name=agent_name,
                agent_chinese_name=get_agent_chinese_name(agent_name),
                next_node=command.goto,
                step_completed=step_count,
                workflow_id=workflow_id
            )
            logger.info(f"中文日志: {agent_complete_log['data']['message']}")

            yield {
                "event": "end_of_agent",
                "data": {
                    "agent_name": agent_name,
                    "agent_id": f"{workflow_id}_{agent_name}_1",
                },
            }

            next_node = command.goto
            current_node = next_node

        # 工作流完成中文日志
        workflow_complete_log = generate_chinese_log(
            "workflow_complete",
            "🎉 多智能体协作工作流执行完成",
            workflow_id=workflow_id,
            total_steps=step_count,
            final_status="成功完成",
            execution_summary=f"共执行{step_count}个智能体步骤"
        )
        logger.info(f"中文日志: {workflow_complete_log['data']['message']}")

        yield {
            "event": "end_of_workflow",
            "data": {
                "workflow_id": workflow_id,
                "messages": [{"role": "user", "content": "workflow completed"}],
            },
        }

        cache.dump(workflow_id, initial_state["workflow_mode"])

    except Exception as e:
        import traceback

        # 工作流错误中文日志
        workflow_error_log = generate_chinese_log(
            "workflow_error",
            f"❌ 工作流执行遇到错误: {str(e)}",
            workflow_id=workflow_id,
            error_type=type(e).__name__,
            error_details=str(e),
            current_node=current_node,
            error_location="workflow_execution"
        )
        logger.error(f"中文日志: {workflow_error_log['data']['message']}")

        traceback.print_exc()
        logger.error("Error in Agent workflow: %s", str(e))
        yield {
            "event": "error",
            "data": {
                "workflow_id": workflow_id,
                "error": str(e),
            },
        }
