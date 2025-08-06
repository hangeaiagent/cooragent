import logging
import json
from copy import deepcopy
from langgraph.types import Command
from typing import Literal
from datetime import datetime
from src.interface.agent import COORDINATOR, PLANNER, PUBLISHER, AGENT_FACTORY
from src.llm.llm import get_llm_by_type
from src.llm.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
from src.tools.search import tavily_tool
from src.interface.agent import State, Router
from src.manager import agent_manager
from src.prompts.template import apply_prompt
from langgraph.prebuilt import create_react_agent
from src.workflow.graph import AgentWorkflow
from src.service.env import MAX_STEPS
from src.workflow.cache import workflow_cache as cache
from src.utils.content_process import clean_response_tags
from src.interface.serializer import AgentBuilder
from src.utils.chinese_names import generate_chinese_log, format_agent_progress_log, get_agent_chinese_name
import asyncio

# 🔄 新增：导入旅游规划器
from src.workflow.travel_planner import travel_planner_node


logger = logging.getLogger(__name__)


async def agent_factory_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """Node for the create agent agent that creates a new agent."""
    logger.info("Agent Factory Start to work in %s workmode", state["workflow_mode"])
    
    # 智能体工厂启动日志
    factory_start_log = generate_chinese_log(
        "agent_factory_start",
        "🏭 智能体工厂启动，开始分析智能体创建需求",
        workflow_mode=state["workflow_mode"],
        user_id=state.get("user_id", "unknown"),
        workflow_id=state.get("workflow_id", "unknown")
    )
    logger.info(f"中文日志: {factory_start_log['data']['message']}")

    goto = "publisher"
    tools = []

    if state["workflow_mode"] == "launch":
        # 恢复系统节点状态
        cache.restore_system_node(state["workflow_id"], AGENT_FACTORY, state["user_id"])
        
        # 应用智能体工厂提示词模板
        factory_prompt_log = generate_chinese_log(
            "agent_factory_prompt",
            "📋 正在应用智能体工厂提示词模板，准备调用LLM生成智能体配置",
            prompt_template="agent_factory",
            llm_type=AGENT_LLM_MAP["agent_factory"]
        )
        logger.info(f"中文日志: {factory_prompt_log['data']['message']}")
        
        messages = apply_prompt_template("agent_factory", state)
        
        # 调用LLM生成智能体规格
        llm_call_log = generate_chinese_log(
            "agent_factory_llm_call",
            "🤖 正在调用LLM生成智能体规格，使用结构化输出确保配置完整性",
            structured_output_type="AgentBuilder",
            reasoning_mode=True
        )
        logger.info(f"中文日志: {llm_call_log['data']['message']}")
        
        agent_spec = await (
            get_llm_by_type(AGENT_LLM_MAP["agent_factory"])
            .with_structured_output(AgentBuilder)
            .ainvoke(messages)
        )
        
        # 智能体规格生成完成日志
        spec_generated_log = generate_chinese_log(
            "agent_spec_generated",
            f"✅ 智能体规格生成完成: {agent_spec['agent_name']}",
            agent_name=agent_spec["agent_name"],
            agent_description=agent_spec["agent_description"],
            llm_type=agent_spec["llm_type"],
            selected_tools_count=len(agent_spec["selected_tools"]),
            selected_tools=[tool["name"] for tool in agent_spec["selected_tools"]]
        )
        logger.info(f"中文日志: {spec_generated_log['data']['message']}")

        # 工具选择和验证
        tool_selection_log = generate_chinese_log(
            "tool_selection_start", 
            f"🛠️ 开始为智能体 {agent_spec['agent_name']} 选择和验证工具",
            agent_name=agent_spec["agent_name"],
            requested_tools=[tool["name"] for tool in agent_spec["selected_tools"]],
            available_tools_count=len(agent_manager.available_tools)
        )
        logger.info(f"中文日志: {tool_selection_log['data']['message']}")

        validated_tools = []
        failed_tools = []

        for tool in agent_spec["selected_tools"]:
            if agent_manager.available_tools.get(tool["name"]):
                tools.append(agent_manager.available_tools[tool["name"]])
                validated_tools.append(tool["name"])
                
                # 工具验证成功日志
                tool_valid_log = generate_chinese_log(
                    "tool_validated",
                    f"✅ 工具验证成功: {tool['name']}",
                    tool_name=tool["name"],
                    tool_description=tool.get("description", ""),
                    validation_status="success"
                )
                logger.info(f"中文日志: {tool_valid_log['data']['message']}")
            else:
                failed_tools.append(tool["name"])
                logger.warning("Tool (%s) is not available", tool["name"])
                
                # 工具验证失败日志
                tool_invalid_log = generate_chinese_log(
                    "tool_validation_failed",
                    f"❌ 工具验证失败: {tool['name']} 不在可用工具列表中",
                    tool_name=tool["name"],
                    validation_status="failed",
                    available_tools=list(agent_manager.available_tools.keys())[:10]  # 只显示前10个避免日志过长
                )
                logger.warning(f"中文日志: {tool_invalid_log['data']['message']}")
        
        # 工具选择完成日志
        tool_selection_complete_log = generate_chinese_log(
            "tool_selection_complete",
            f"🔧 工具选择完成: {len(validated_tools)}个成功，{len(failed_tools)}个失败",
            validated_tools=validated_tools,
            failed_tools=failed_tools,
            total_requested=len(agent_spec["selected_tools"]),
            success_rate=f"{len(validated_tools)}/{len(agent_spec['selected_tools'])}"
        )
        logger.info(f"中文日志: {tool_selection_complete_log['data']['message']}")
                
        # 创建智能体
        agent_creation_log = generate_chinese_log(
            "agent_creation_start",
            f"🚀 开始创建智能体: {agent_spec['agent_name']}",
            agent_name=agent_spec["agent_name"],
            llm_type=agent_spec["llm_type"],
            tools_count=len(tools),
            user_id=state["user_id"]
        )
        logger.info(f"中文日志: {agent_creation_log['data']['message']}")
                
        await agent_manager._create_agent_by_prebuilt(
            user_id=state["user_id"],
            name=agent_spec["agent_name"],
            nick_name=agent_spec["agent_name"],
            llm_type=agent_spec["llm_type"],
            tools=tools,
            prompt=agent_spec["prompt"],
            description=agent_spec["agent_description"],
        )
        
        # 智能体创建成功日志
        agent_created_log = generate_chinese_log(
            "agent_created_success",
            f"🎉 智能体创建成功: {agent_spec['agent_name']}",
            agent_name=agent_spec["agent_name"],
            creation_status="success",
            agent_capabilities=agent_spec["agent_description"],
            prompt_length=len(agent_spec["prompt"]),
            final_tools=validated_tools
        )
        logger.info(f"中文日志: {agent_created_log['data']['message']}")
        
        state["TEAM_MEMBERS"].append(agent_spec["agent_name"])
        
        # 团队更新日志
        team_update_log = generate_chinese_log(
            "team_updated",
            f"👥 团队成员已更新，新增智能体: {agent_spec['agent_name']}",
            new_agent=agent_spec["agent_name"],
            total_team_members=len(state["TEAM_MEMBERS"]),
            current_team=state["TEAM_MEMBERS"]
        )
        logger.info(f"中文日志: {team_update_log['data']['message']}")

    elif state["workflow_mode"] == "polish":
        # this will be support soon
        polish_log = generate_chinese_log(
            "polish_mode",
            "🔧 智能体工厂进入打磨模式（暂未支持）",
            workflow_mode="polish",
            support_status="coming_soon"
        )
        logger.info(f"中文日志: {polish_log['data']['message']}")
        pass

    # 工厂完成日志
    factory_complete_log = generate_chinese_log(
        "agent_factory_complete",
        f"✅ 智能体工厂任务完成，准备移交给发布器",
        next_node="publisher",
        factory_output=f"成功创建智能体: {agent_spec['agent_name'] if 'agent_spec' in locals() else '无'}",
        workflow_mode=state["workflow_mode"]
    )
    logger.info(f"中文日志: {factory_complete_log['data']['message']}")

    return Command(
        update={
            "messages": [
                {
                    "content": f"New agent {agent_spec['agent_name']} created. \n",
                    "tool": "agent_factory",
                    "role": "assistant",
                }
            ],
            "new_agent_name": agent_spec["agent_name"],
            "agent_name": "agent_factory",
        },
        goto=goto,
    )


async def publisher_node(
    state: State,
) -> Command[Literal["agent_proxy", "agent_factory", "__end__"]]:
    """publisher node that decides which agent should act next."""
    logger.info("publisher evaluating next action in %s mode ", state["workflow_mode"])
    
    # 发布器启动日志
    publisher_start_log = generate_chinese_log(
        "publisher_start",
        "📨 发布器启动，开始评估下一个执行节点",
        workflow_mode=state["workflow_mode"],
        current_step=state.get("current_step", "unknown"),
        workflow_id=state.get("workflow_id", "unknown")
    )
    logger.info(f"中文日志: {publisher_start_log['data']['message']}")

    if state["workflow_mode"] == "launch":
        cache.restore_system_node(state["workflow_id"], PUBLISHER, state["user_id"])
        
        # 应用发布器提示词模板
        publisher_prompt_log = generate_chinese_log(
            "publisher_prompt",
            "📋 正在应用发布器提示词模板，准备决策下一个执行节点",
            prompt_template="publisher",
            llm_type=AGENT_LLM_MAP["publisher"]
        )
        logger.info(f"中文日志: {publisher_prompt_log['data']['message']}")
        
        messages = apply_prompt_template("publisher", state)
        
        # 调用LLM进行路由决策
        routing_decision_log = generate_chinese_log(
            "publisher_routing",
            "🤖 正在调用LLM进行路由决策，使用结构化输出确保决策准确性",
            structured_output_type="Router",
            decision_stage="next_agent_selection"
        )
        logger.info(f"中文日志: {routing_decision_log['data']['message']}")
        
        response = await (
            get_llm_by_type(AGENT_LLM_MAP["publisher"])
            .with_structured_output(Router)
            .ainvoke(messages)
        )
        agent = response["next"]

        # 路由决策完成日志
        routing_complete_log = generate_chinese_log(
            "publisher_decision",
            f"🎯 发布器决策完成，下一个执行节点: {agent}",
            next_agent=agent,
            decision_type="structured_routing",
            routing_successful=True
        )
        logger.info(f"中文日志: {routing_complete_log['data']['message']}")

        if agent == "FINISH":
            goto = "__end__"
            logger.info("Workflow completed \n")
            
            # 工作流完成日志
            workflow_complete_log = generate_chinese_log(
                "workflow_complete",
                "🏁 工作流执行完成，所有任务已完成",
                final_status="completed",
                total_steps_completed=state.get("step_count", "unknown"),
                workflow_id=state.get("workflow_id", "unknown")
            )
            logger.info(f"中文日志: {workflow_complete_log['data']['message']}")
            
            cache.restore_node(
                state["workflow_id"], goto, state["initialized"], state["user_id"]
            )
            return Command(goto=goto, update={"next": goto})
        elif agent != "agent_factory":
            cache.restore_system_node(state["workflow_id"], agent, state["user_id"])
            goto = "agent_proxy"
            
            # 代理节点分发日志
            proxy_dispatch_log = generate_chinese_log(
                "publisher_dispatch_proxy",
                f"🔄 发布器将任务分发给代理节点，目标智能体: {agent}",
                target_agent=agent,
                dispatch_type="agent_proxy",
                next_node="agent_proxy"
            )
            logger.info(f"中文日志: {proxy_dispatch_log['data']['message']}")
        else:
            cache.restore_system_node(
                state["workflow_id"], "agent_factory", state["user_id"]
            )
            goto = "agent_factory"
            
            # 智能体工厂分发日志
            factory_dispatch_log = generate_chinese_log(
                "publisher_dispatch_factory",
                "🏭 发布器将任务分发给智能体工厂，准备创建新智能体",
                target_node="agent_factory",
                dispatch_type="agent_creation",
                next_node="agent_factory"
            )
            logger.info(f"中文日志: {factory_dispatch_log['data']['message']}")

        logger.info("publisher delegating to: %s ", agent)

        cache.restore_node(
            state["workflow_id"], agent, state["initialized"], state["user_id"]
        )

    elif state["workflow_mode"] in ["production", "polish"]:
        # todo add polish history
        production_mode_log = generate_chinese_log(
            "publisher_production_mode",
            f"⚙️ 发布器运行在{state['workflow_mode']}模式",
            workflow_mode=state["workflow_mode"],
            mode_type="cached_execution"
        )
        logger.info(f"中文日志: {production_mode_log['data']['message']}")
        
        agent = cache.get_next_node(state["workflow_id"])
        if agent == "FINISH":
            goto = "__end__"
            logger.info("Workflow completed \n")
            
            # 生产模式完成日志
            production_complete_log = generate_chinese_log(
                "workflow_complete_production",
                f"🏁 {state['workflow_mode']}模式工作流执行完成",
                workflow_mode=state["workflow_mode"],
                final_status="completed"
            )
            logger.info(f"中文日志: {production_complete_log['data']['message']}")
            
            return Command(goto=goto, update={"next": goto})
        else:
            goto = "agent_proxy"
            
            # 生产模式代理分发日志
            production_dispatch_log = generate_chinese_log(
                "publisher_production_dispatch",
                f"🔄 {state['workflow_mode']}模式下分发任务给智能体: {agent}",
                target_agent=agent,
                workflow_mode=state["workflow_mode"],
                next_node="agent_proxy"
            )
            logger.info(f"中文日志: {production_dispatch_log['data']['message']}")
    
    logger.info("publisher delegating to: %s", agent)
    
    # 发布器完成日志
    publisher_complete_log = generate_chinese_log(
        "publisher_complete",
        f"✅ 发布器任务完成，成功分发给: {agent}",
        delegated_to=agent,
        next_goto=goto,
        delegation_successful=True
    )
    logger.info(f"中文日志: {publisher_complete_log['data']['message']}")

    return Command(
        goto=goto,
        update={
            "messages": [
                {
                    "content": f"Next step is delegating to: {agent}\n",
                    "tool": "publisher",
                    "role": "assistant",
                }
            ],
            "next": agent,
        },
    )


async def agent_proxy_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """智能体代理节点"""
    _agent = state["next"]
    
    # 处理_agent可能是字符串或对象的情况
    if isinstance(_agent, str):
        # 如果是字符串，从agent_manager中获取智能体对象
        agent_name = _agent
        if agent_name not in agent_manager.available_agents:
            logger.error(f"智能体 {agent_name} 不存在")
            return Command(
                update={
                    "messages": [
                        {
                            "content": f"❌ 智能体 {agent_name} 不存在",
                            "tool": state["next"],
                            "role": "assistant",
                        }
                    ],
                    "processing_agent_name": agent_name,
                    "agent_name": agent_name,
                },
                goto="publisher",
    )
        _agent = agent_manager.available_agents[agent_name]
    else:
        # 如果是对象，直接使用
        agent_name = _agent.agent_name
    
    # 智能体代理开始日志
    proxy_start_log = generate_chinese_log(
        "agent_proxy_start",
        f"🎯 智能体代理开始执行: {agent_name}",
        agent_name=agent_name,
        workflow_mode=state.get("workflow_mode", "unknown"),
        user_id=state.get("user_id")
    )
    logger.info(f"中文日志: {proxy_start_log['data']['message']}")

    # 检查工具可用性
    available_tools = []
    missing_tools = []
    
    for tool in _agent.selected_tools:
        if tool.name in agent_manager.available_tools:
            available_tools.append(agent_manager.available_tools[tool.name])
        else:
            missing_tools.append(tool.name)
            logger.warning(f"工具 {tool.name} 不可用，跳过")
    
    if missing_tools:
        logger.warning(f"智能体 {agent_name} 缺少工具: {missing_tools}")
    
    if not available_tools:
        logger.error(f"智能体 {agent_name} 没有可用的工具")
        return Command(
            update={
                "messages": [
                    {
                        "content": f"❌ 智能体 {agent_name} 执行失败：没有可用的工具。缺少的工具：{missing_tools}",
                        "tool": state["next"],
                        "role": "assistant",
                    }
                ],
                "processing_agent_name": agent_name,
                "agent_name": agent_name,
            },
            goto="publisher",
        )

    react_creation_log = generate_chinese_log(
        "react_agent_creation",
        f"⚙️ 正在创建ReAct智能体实例: {agent_name}",
        agent_name=agent_name,
        react_pattern="observation_thought_action",
        tools_integrated=len(available_tools)
    )
    logger.info(f"中文日志: {react_creation_log['data']['message']}")

    agent = create_react_agent(
        get_llm_by_type(_agent.llm_type),
        tools=available_tools,
        prompt=apply_prompt(state, _agent.prompt),
    )

    # Create config with user_id for tool notifications
    config = {
        "configurable": {"user_id": state.get("user_id")},
        "recursion_limit": int(MAX_STEPS),
    }
    
    # 智能体执行开始日志
    agent_execution_log = generate_chinese_log(
        "agent_execution_start",
        f"🚀 智能体开始执行任务: {agent_name}",
        agent_name=agent_name,
        max_steps=int(MAX_STEPS),
        user_id=state.get("user_id"),
        execution_config=config
    )
    logger.info(f"中文日志: {agent_execution_log['data']['message']}")

    try:
        # 添加超时机制
        response = await asyncio.wait_for(
            agent.ainvoke(state, config=config),
            timeout=300  # 5分钟超时
        )
    
    # 智能体执行完成日志
        agent_execution_complete_log = generate_chinese_log(
            "agent_execution_complete",
            f"✅ 智能体任务执行完成: {agent_name}",
            agent_name=agent_name,
            execution_status="completed",
            response_length=len(response["messages"][-1].content) if response.get("messages") else 0,
            final_message_preview=response["messages"][-1].content[:100] + "..." if response.get("messages") and len(response["messages"][-1].content) > 100 else response["messages"][-1].content if response.get("messages") else ""
        )
        logger.info(f"中文日志: {agent_execution_complete_log['data']['message']}")

    except asyncio.TimeoutError:
            logger.error(f"智能体 {agent_name} 执行超时")
            return Command(
                update={
                    "messages": [
                        {
                            "content": f"⏰ 智能体 {agent_name} 执行超时，请重试或简化需求",
                            "tool": state["next"],
                            "role": "assistant",
                        }
                    ],
                "processing_agent_name": agent_name,
                "agent_name": agent_name,
            },
            goto="publisher",
        )
    except Exception as e:
        logger.error(f"智能体 {agent_name} 执行出错: {e}")
        return Command(
            update={
                "messages": [
                    {
                        "content": f"❌ 智能体 {agent_name} 执行出错: {str(e)}",
                        "tool": state["next"],
                        "role": "assistant",
                    }
                ],
                "processing_agent_name": agent_name,
                "agent_name": agent_name,
            },
            goto="publisher",
        )

    if state["workflow_mode"] == "launch":
        cache.restore_node(
            state["workflow_id"], _agent, state["initialized"], state["user_id"]
        )
        
        # 缓存状态保存日志
        cache_save_log = generate_chinese_log(
            "cache_state_saved",
            f"💾 智能体执行状态已保存到缓存: {agent_name}",
            agent_name=agent_name,
            workflow_mode="launch",
            cache_operation="restore_node"
        )
        logger.info(f"中文日志: {cache_save_log['data']['message']}")
    elif state["workflow_mode"] == "production":
        cache.update_stack(state["workflow_id"], state["user_id"])
        
        # 生产模式缓存更新日志
        production_cache_log = generate_chinese_log(
            "production_cache_updated",
            f"📊 生产模式缓存堆栈已更新: {agent_name}",
            agent_name=agent_name,
            workflow_mode="production",
            cache_operation="update_stack"
        )
        logger.info(f"中文日志: {production_cache_log['data']['message']}")

    # 代理节点完成日志
    proxy_complete_log = generate_chinese_log(
        "agent_proxy_complete",
        f"🎯 智能体代理任务完成，准备返回发布器: {agent_name}",
        agent_name=agent_name,
        return_to="publisher",
        proxy_status="completed"
    )
    logger.info(f"中文日志: {proxy_complete_log['data']['message']}")

    return Command(
        update={
            "messages": [
                {
                    "content": response["messages"][-1].content,
                    "tool": state["next"],
                    "role": "assistant",
                }
            ],
            "processing_agent_name": agent_name,
            "agent_name": agent_name,
        },
        goto="publisher",
    )


async def planner_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """Planner node that generate the full plan."""
    logger.info("Planner generating full plan in %s mode", state["workflow_mode"])
    
    # 规划器启动日志
    planner_start_log = generate_chinese_log(
        "planner_start",
        "🧠 规划器启动，开始分析用户需求并生成执行计划",
        workflow_mode=state["workflow_mode"],
        user_query=state.get("USER_QUERY", "")[:100] + "..." if len(state.get("USER_QUERY", "")) > 100 else state.get("USER_QUERY", ""),
        deep_thinking_mode=state.get("deep_thinking_mode", False),
        search_before_planning=state.get("search_before_planning", False)
    )
    logger.info(f"中文日志: {planner_start_log['data']['message']}")

    content = ""
    goto = "publisher"

    if state["workflow_mode"] == "launch":
        # 应用规划器提示词模板
        planner_prompt_log = generate_chinese_log(
            "planner_prompt",
            "📋 正在应用规划器提示词模板，准备深度分析用户需求",
            prompt_template="planner",
            available_agents=len(state.get("TEAM_MEMBERS", [])),
            available_tools=len(state.get("TOOLS", "").split("\n")) if state.get("TOOLS") else 0
        )
        logger.info(f"中文日志: {planner_prompt_log['data']['message']}")
        
        messages = apply_prompt_template("planner", state)
        llm = get_llm_by_type(AGENT_LLM_MAP["planner"])
        
        # 深度思考模式检查
        if state.get("deep_thinking_mode"):
            llm = get_llm_by_type("reasoning")
            deep_thinking_log = generate_chinese_log(
                "planner_deep_thinking",
                "🤔 启用深度思考模式，使用推理型LLM进行复杂需求分析",
                reasoning_llm=True,
                enhanced_analysis=True
            )
            logger.info(f"中文日志: {deep_thinking_log['data']['message']}")
        
        # 规划前搜索检查
        if state.get("search_before_planning"):
            search_before_log = generate_chinese_log(
                "planner_search_before",
                "🔍 启用规划前搜索，获取相关信息以提升规划质量",
                search_enabled=True,
                search_query=state["messages"][-1]["content"][:100] + "..."
            )
            logger.info(f"中文日志: {search_before_log['data']['message']}")
            
            config = {"configurable": {"user_id": state.get("user_id")}}
            searched_content = tavily_tool.invoke(
                {
                    "query": [
                        "".join(message["content"])
                        for message in state["messages"]
                        if message["role"] == "user"
                    ][0]
                },
                config=config,
            )
            
            # 搜索结果获取日志
            search_results_log = generate_chinese_log(
                "planner_search_results",
                f"📊 搜索完成，获得{len(searched_content)}条相关信息",
                search_results_count=len(searched_content),
                search_titles=[elem.get('title', '') for elem in searched_content[:3]]  # 只显示前3个标题
            )
            logger.info(f"中文日志: {search_results_log['data']['message']}")
            
            messages = deepcopy(messages)
            messages[-1]["content"] += (
                f"\n\n# Relative Search Results\n\n{json.dumps([{'titile': elem['title'], 'content': elem['content']} for elem in searched_content], ensure_ascii=False)}"
            )
        
        cache.restore_system_node(state["workflow_id"], PLANNER, state["user_id"])
        
        # LLM调用开始日志
        llm_planning_log = generate_chinese_log(
            "planner_llm_call",
            "🤖 正在调用LLM生成详细执行计划",
            llm_type=llm.__class__.__name__,
            message_length=len(str(messages)),
            planning_stage="llm_generation"
        )
        logger.info(f"中文日志: {llm_planning_log['data']['message']}")
        
        response = llm.stream(messages)
        for chunk in response:
            if chunk.content:
                content += chunk.content  # type: ignore
        content = clean_response_tags(content)
        
        # 规划生成完成日志
        planning_complete_log = generate_chinese_log(
            "planner_plan_generated",
            "✅ 执行计划生成完成，正在解析和验证计划结构",
            plan_length=len(content),
            content_preview=content[:200] + "..." if len(content) > 200 else content
        )
        logger.info(f"中文日志: {planning_complete_log['data']['message']}")
        
    elif state["workflow_mode"] == "production":
        # watch out the json style
        production_plan_log = generate_chinese_log(
            "planner_production_mode",
            "⚙️ 规划器运行在生产模式，使用缓存的执行计划",
            workflow_mode="production",
            cache_source="planning_steps"
        )
        logger.info(f"中文日志: {production_plan_log['data']['message']}")
        
        content = json.dumps(
            cache.get_planning_steps(state["workflow_id"]), indent=4, ensure_ascii=False
        )

    elif state["workflow_mode"] == "polish" and state["polish_target"] == "planner":
        # this will be support soon
        polish_mode_log = generate_chinese_log(
            "planner_polish_mode",
            "🔧 规划器进入打磨模式，优化现有执行计划",
            workflow_mode="polish",
            polish_target="planner",
            historical_plan_available=bool(state.get("historical_plan"))
        )
        logger.info(f"中文日志: {polish_mode_log['data']['message']}")
        
        state["historical_plan"] = cache.get_planning_steps(state["workflow_id"])
        state["adjustment_instruction"] = state["polish_instruction"]

        messages = apply_prompt_template("planner_polishment", state)
        llm = get_llm_by_type(AGENT_LLM_MAP["planner"])
        if state.get("deep_thinking_mode"):
            llm = get_llm_by_type("reasoning")
        if state.get("search_before_planning"):
            config = {"configurable": {"user_id": state.get("user_id")}}
            searched_content = tavily_tool.invoke(
                {
                    "query": [
                        "".join(message["content"])
                        for message in state["messages"]
                        if message["role"] == "user"
                    ][0]
                },
                config=config,
            )
            messages = deepcopy(messages)
            messages[-1]["content"] += (
                f"\n\n# Relative Search Results\n\n{json.dumps([{'titile': elem['title'], 'content': elem['content']} for elem in searched_content], ensure_ascii=False)}"
            )

        response = await llm.ainvoke(messages)
        content = clean_response_tags(response.content)  # type: ignore
    
    # steps need to be stored in cache
    if state["workflow_mode"] in ["launch", "polish"]:
        try:
            # 解析和验证规划步骤
            steps_parsing_log = generate_chinese_log(
                "planner_parse_steps",
                "🔍 正在解析规划步骤JSON结构",
                parsing_stage="json_validation",
                content_length=len(content)
            )
            logger.info(f"中文日志: {steps_parsing_log['data']['message']}")
            
            steps_obj = json.loads(content)
            steps = steps_obj.get("steps", [])
            
            # 规划步骤解析成功日志
            steps_parsed_log = generate_chinese_log(
                "planner_steps_parsed",
                f"✅ 规划步骤解析成功，共{len(steps)}个执行步骤",
                total_steps=len(steps),
                step_agents=[step.get("agent_name") for step in steps],
                plan_title=steps_obj.get("title", ""),
                new_agents_needed=len(steps_obj.get("new_agents_needed", []))
            )
            logger.info(f"中文日志: {steps_parsed_log['data']['message']}")
            
            cache.restore_planning_steps(state["workflow_id"], steps, state["user_id"])
            
            # 缓存步骤保存日志
            cache_steps_log = generate_chinese_log(
                "planner_steps_cached",
                f"💾 执行步骤已保存到缓存，工作流可以开始执行",
                workflow_id=state["workflow_id"],
                steps_cached=len(steps),
                cache_operation="restore_planning_steps"
            )
            logger.info(f"中文日志: {cache_steps_log['data']['message']}")
            
        except json.JSONDecodeError:
            logger.warning("Planner response is not a valid JSON \n")
            
            # JSON解析失败日志
            json_error_log = generate_chinese_log(
                "planner_json_error",
                "❌ 规划器响应不是有效的JSON格式，工作流将终止",
                error_type="json_decode_error",
                content_preview=content[:200] + "..." if len(content) > 200 else content,
                workflow_termination=True
            )
            logger.error(f"中文日志: {json_error_log['data']['message']}")
            
            goto = "__end__"
        cache.restore_system_node(state["workflow_id"], goto, state["user_id"])
    
    # 规划器完成日志
    planner_complete_log = generate_chinese_log(
        "planner_complete",
        f"🎯 规划器任务完成，准备移交给: {goto}",
        next_node=goto,
        planning_status="completed" if goto == "publisher" else "terminated",
        workflow_mode=state["workflow_mode"]
    )
    logger.info(f"中文日志: {planner_complete_log['data']['message']}")
    
    return Command(
        update={
            "messages": [{"content": content, "tool": "planner", "role": "assistant"}],
            "agent_name": "planner",
            "full_plan": content,
        },
        goto=goto,
    )


async def coordinator_node(state: State) -> Command[Literal["planner", "travel_planner", "__end__"]]:
    """Coordinator node that communicate with customers."""
    logger.info("Coordinator talking. \n")
    
    # 协调器启动日志
    coordinator_start_log = generate_chinese_log(
        "coordinator_start",
        "🎯 协调器启动，开始分析用户输入并决定处理路径",
        user_query=state.get("USER_QUERY", "")[:100] + "..." if len(state.get("USER_QUERY", "")) > 100 else state.get("USER_QUERY", ""),
        workflow_mode=state.get("workflow_mode", "unknown"),
        user_id=state.get("user_id", "unknown")
    )
    logger.info(f"中文日志: {coordinator_start_log['data']['message']}")

    goto = "__end__"
    content = ""

    # 应用协调器提示词模板
    coordinator_prompt_log = generate_chinese_log(
        "coordinator_prompt",
        "📋 正在应用协调器提示词模板，准备进行智能分类",
        prompt_template="coordinator",
        classification_protocols=2,  # Protocol 1: 直接回复, Protocol 2: 任务移交
        llm_type=AGENT_LLM_MAP["coordinator"]
    )
    logger.info(f"中文日志: {coordinator_prompt_log['data']['message']}")

    messages = apply_prompt_template("coordinator", state)
    
    # LLM调用进行分类决策
    classification_log = generate_chinese_log(
        "coordinator_classification",
        "🤖 正在调用LLM进行智能分类决策",
        decision_stage="protocol_selection",
        input_analysis="user_intent_classification"
    )
    logger.info(f"中文日志: {classification_log['data']['message']}")
    
    response = await get_llm_by_type(AGENT_LLM_MAP["coordinator"]).ainvoke(messages)
    if state["workflow_mode"] == "launch":
        cache.restore_system_node(state["workflow_id"], COORDINATOR, state["user_id"])

    content = clean_response_tags(response.content)  # type: ignore
    
    # 分类结果分析
    if "handover_to_planner" in content:
        # 🔄 新增：检查是否为旅游相关任务
        user_query = state.get("USER_QUERY", "")
        travel_keywords = ["旅游", "旅行", "行程", "景点", "攻略", "计划", "规划", "出游", "度假", "玩", "游览", "参观", "住宿", "交通", "去", "到", "travel", "trip", "visit", "tour", "vacation", "holiday"]
        is_travel_related = any(keyword in user_query for keyword in travel_keywords)
        
        if is_travel_related:
            goto = "travel_planner"
            # Protocol 2: 旅游任务移交日志
            handover_log = generate_chinese_log(
                "coordinator_travel_handover",
                "🗺️ 协调器决策: Protocol 2 - 旅游任务移交给旅游规划器",
                protocol_selected=2,
                decision_type="travel_task",
                handover_target="travel_planner",
                task_complexity="requires_travel_planning"
            )
        else:
            goto = "planner"
            # Protocol 2: 通用任务移交日志
            handover_log = generate_chinese_log(
                "coordinator_handover",
                "🔄 协调器决策: Protocol 2 - 任务移交给标准规划器",
                protocol_selected=2,
                decision_type="complex_task",
                handover_target="planner",
                task_complexity="requires_planning"
            )
        
        logger.info(f"中文日志: {handover_log['data']['message']}")
    else:
        # Protocol 1: 直接回复日志
        direct_reply_log = generate_chinese_log(
            "coordinator_direct_reply",
            "💬 协调器决策: Protocol 1 - 直接回复用户",
            protocol_selected=1,
            decision_type="simple_task",
            response_type="direct_answer",
            response_preview=content[:100] + "..." if len(content) > 100 else content
        )
        logger.info(f"中文日志: {direct_reply_log['data']['message']}")
    
    if state["workflow_mode"] == "launch":
        cache.restore_system_node(state["workflow_id"], "planner", state["user_id"])
    
    # 协调器完成日志
    coordinator_complete_log = generate_chinese_log(
        "coordinator_complete",
        f"✅ 协调器任务完成，选择的处理路径: {goto}",
        selected_protocol=2 if goto == "planner" else 1,
        next_node=goto,
        coordination_successful=True
    )
    logger.info(f"中文日志: {coordinator_complete_log['data']['message']}")
    
    return Command(
        update={
            "messages": [
                {"content": content, "tool": "coordinator", "role": "assistant"}
            ],
            "agent_name": "coordinator",
        },
        goto=goto,
    )


def build_graph():
    """Build and return the agent workflow graph."""
    workflow = AgentWorkflow()
    workflow.add_node("coordinator", coordinator_node)  # type: ignore
    workflow.add_node("planner", planner_node)  # type: ignore
    workflow.add_node("publisher", publisher_node)  # type: ignore
    workflow.add_node("agent_factory", agent_factory_node)  # type: ignore
    workflow.add_node("agent_proxy", agent_proxy_node)  # type: ignore
    
    # 🔄 新增：旅游专用节点
    workflow.add_node("travel_planner", travel_planner_node)  # type: ignore

    workflow.set_start("coordinator")
    return workflow.compile()
