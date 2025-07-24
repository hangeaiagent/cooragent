"""
基于Cooragent架构的项目代码生成器

该模块实现了从用户需求到完整Cooragent项目的自动生成流程
"""

import asyncio
import json
import logging
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import aiofiles

from src.interface.agent import Agent, TaskType
from src.manager import agent_manager
from src.workflow.process import run_agent_workflow
from src.generator.config_generator import ConfigGenerator
from src.utils.chinese_names import generate_chinese_log, format_code_generation_log, format_agent_progress_log, get_agent_chinese_name
from src.utils.path_utils import get_project_root

logger = logging.getLogger(__name__)


class CooragentProjectGenerator:
    """基于Cooragent架构的项目代码生成器"""
    
    def __init__(self, output_dir: str = "generated_projects"):
        self.cooragent_root = get_project_root()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 组件映射表 - 定义需要复制的Cooragent核心组件
        self.core_components = {
            "interface": ["agent.py", "workflow.py", "serializer.py", "__init__.py"],
            "workflow": ["graph.py", "process.py", "cache.py", "__init__.py"],
            "manager": ["agents.py", "__init__.py"],
            "llm": ["llm.py", "agents.py", "__init__.py"],
            "utils": ["path_utils.py", "content_process.py", "__init__.py"],
            "service": ["server.py", "session.py", "env.py", "__init__.py"],
            "prompts": ["template.py", "__init__.py"]
        }
        
        # 工具文件映射
        self.tool_mapping = {
            "tavily_tool": ["search.py"],
            "python_repl_tool": ["python_repl.py"],
            "bash_tool": ["bash_tool.py"],
            "crawl_tool": ["crawl.py"],
            "browser_tool": ["browser.py", "browser_decorators.py"]
        }
    
    async def generate_project(self, user_input: str, user_id: str = None, progress_callback=None) -> Path:
        """
        生成基于Cooragent的精简项目
        
        Args:
            user_input: 用户需求描述
            user_id: 用户ID，用于隔离不同用户的智能体
            progress_callback: 进度更新回调函数
            
        Returns:
            生成的压缩包路径
        """
        if user_id is None:
            user_id = f"gen_{int(time.time())}"
            
        logger.info(f"开始为用户 {user_id} 生成项目，需求: {user_input[:100]}...")
        
        # 输出中文初始化日志
        init_log = generate_chinese_log(
            "code_generation_init",
            "🚀 开始生成基于Cooragent的多智能体应用代码",
            user_id=user_id,
            user_input=user_input[:200],
            timestamp=datetime.now().isoformat()
        )
        logger.info(f"中文日志: {init_log['data']['message']}")
        
        if progress_callback:
            await progress_callback(
                format_code_generation_log("init", 5, {"user_id": user_id}), 
                5, "初始化", "🔧 设置Cooragent代码生成环境和参数"
            )
        
        try:
            # 1. 调用现有工作流系统获取智能体配置
            workflow_log = generate_chinese_log(
                "requirement_analysis",
                "🧠 正在调用Cooragent多智能体工作流分析用户需求",
                analysis_stage="workflow_invocation",
                user_requirement=user_input[:150]
            )
            logger.info(f"中文日志: {workflow_log['data']['message']}")
            
            if progress_callback:
                await progress_callback(
                    format_code_generation_log("workflow", 15, {"analysis": "需求解析"}), 
                    15, "需求分析", "🤖 使用协调器、规划器等AI智能体协作分析用户需求"
                )
            
            workflow_result = await self._run_workflow(user_input, user_id, progress_callback)
            
            # 2. 分析生成的智能体和工具需求
            analysis_log = generate_chinese_log(
                "project_planning",
                "📋 正在分析智能体配置和工具选择，制定项目架构方案",
                workflow_completed=True,
                next_stage="configuration_analysis"
            )
            logger.info(f"中文日志: {analysis_log['data']['message']}")
            
            if progress_callback:
                await progress_callback(
                    format_code_generation_log("analysis", 35, {"stage": "配置分析"}), 
                    35, "配置分析", "📊 确定需要的智能体类型、工具组件和项目结构"
                )
            
            project_config = await self._analyze_project_requirements(workflow_result, user_id, progress_callback)
            
            # 记录分析结果
            agents_count = len(project_config['agents'])
            tools_count = len(project_config['tools'])
            planning_complete_log = generate_chinese_log(
                "project_planning", 
                f"✅ 项目方案制定完成: {agents_count}个智能体，{tools_count}个工具",
                agents_count=agents_count,
                tools_count=tools_count,
                agents_list=[agent.agent_name for agent in project_config['agents']],
                tools_list=project_config['tools']
            )
            logger.info(f"中文日志: {planning_complete_log['data']['message']}")
            
            # 3. 复制Cooragent核心代码并定制化
            code_gen_log = generate_chinese_log(
                "code_creation",
                f"💻 开始生成定制化项目代码，基于{agents_count}个智能体构建应用架构",
                generation_stage="code_creation",
                project_components=len(project_config.get('components', []))
            )
            logger.info(f"中文日志: {code_gen_log['data']['message']}")
            
            if progress_callback:
                await progress_callback(
                    format_code_generation_log("code_creation", 60, {
                        "agents_count": agents_count,
                        "tools_count": tools_count
                    }), 
                    60, "代码生成", f"🏗️ 基于{agents_count}个智能体生成完整项目结构和配置"
                )
            
            project_path = await self._generate_customized_project(project_config, user_id, progress_callback)
            
            # 4. 压缩项目
            packaging_log = generate_chinese_log(
                "project_packaging",
                "📦 正在打包项目文件，生成可部署的压缩包",
                project_path=str(project_path),
                packaging_stage="compression"
            )
            logger.info(f"中文日志: {packaging_log['data']['message']}")
            
            if progress_callback:
                await progress_callback(
                    format_code_generation_log("compression", 90, {"project_name": project_path.name}), 
                    90, "项目打包", "🗜️ 压缩项目文件，生成可下载的完整应用包"
                )
            
            zip_path = await self._compress_project(project_path)
            
            # 生成完成日志
            complete_log = generate_chinese_log(
                "generation_complete",
                "🎉 基于Cooragent的多智能体应用代码生成成功！",
                generation_success=True,
                zip_file=str(zip_path),
                file_size=zip_path.stat().st_size,
                agents_created=agents_count,
                tools_integrated=tools_count,
                user_id=user_id
            )
            logger.info(f"中文日志: {complete_log['data']['message']}")
            
            if progress_callback:
                await progress_callback(
                    format_code_generation_log("complete", 100, {
                        "project_name": zip_path.name,
                        "agents_count": agents_count
                    }), 
                    100, "完成", f"✅ 已生成基于Cooragent的多智能体应用，包含{agents_count}个智能体"
                )
            
            logger.info(f"项目生成完成: {zip_path}")
            return zip_path
            
        except Exception as e:
            # 错误日志
            error_log = generate_chinese_log(
                "error_occurred",
                f"❌ 代码生成过程中发生错误: {str(e)}",
                error_type=type(e).__name__,
                error_details=str(e),
                user_id=user_id,
                user_input=user_input[:100]
            )
            logger.error(f"中文日志: {error_log['data']['message']}")
            logger.error(f"项目生成失败: {e}")
            
            if progress_callback:
                await progress_callback(f"❌ 生成失败: {str(e)}", 0, "错误", f"详细错误信息: {str(e)}")
            raise
        finally:
            # 清理临时生成的智能体
            cleanup_log = generate_chinese_log(
                "cleanup",
                "🧹 正在清理临时文件和智能体配置",
                cleanup_stage="agent_cleanup",
                user_id=user_id
            )
            logger.info(f"中文日志: {cleanup_log['data']['message']}")
            
            if progress_callback:
                await progress_callback("🧹 正在清理临时文件...", 95, "清理", "清理临时生成的智能体配置和缓存文件")
            await self._cleanup_user_agents(user_id, progress_callback)
    
    async def _run_workflow(self, user_input: str, user_id: str, progress_callback=None) -> Dict[str, Any]:
        """调用现有工作流系统分析需求"""
        
        # 工作流启动详细日志
        workflow_start_log = generate_chinese_log(
            "workflow_analysis_start",
            "🧠 启动Cooragent多智能体工作流，开始深度分析用户需求",
            user_input_preview=user_input[:200] + "..." if len(user_input) > 200 else user_input,
            user_id=user_id,
            workflow_type="agent_workflow",
            analysis_mode="deep_thinking_enabled"
        )
        logger.info(f"中文日志: {workflow_start_log['data']['message']}")
        
        try:
            # 构建消息格式
            messages = [{"role": "user", "content": user_input}]
            
            if progress_callback:
                await progress_callback(
                    "🤖 正在启动Cooragent多智能体协作分析系统...", 
                    18, 
                    "工作流启动", 
                    "初始化协调器、规划器、智能体工厂等核心组件"
                )
            
            # 工作流配置日志
            workflow_config_log = generate_chinese_log(
                "workflow_configuration",
                "⚙️ 工作流配置完成，启用深度思考和规划前搜索模式",
                deep_thinking_mode=True,
                search_before_planning=True,
                task_type="AGENT_WORKFLOW",
                workmode="launch"
            )
            logger.info(f"中文日志: {workflow_config_log['data']['message']}")

            # 使用Launch模式分析用户需求并生成智能体配置
            # run_agent_workflow 返回异步生成器，需要迭代处理
            final_result = {}
            events = []
            step_count = 0
            current_agent = None
            
            # 工作流执行日志
            workflow_execution_log = generate_chinese_log(
                "workflow_execution_start",
                "🔄 开始执行多智能体协作工作流，预计经过协调器→规划器→智能体工厂流程",
                expected_flow="coordinator→planner→agent_factory→execution",
                user_input_length=len(user_input),
                messages_count=len(messages)
            )
            logger.info(f"中文日志: {workflow_execution_log['data']['message']}")
            
            async for event_data in run_agent_workflow(
                user_id=user_id,
                task_type=TaskType.AGENT_WORKFLOW,
                user_input_messages=messages,
                debug=False,
                deep_thinking_mode=True,
                search_before_planning=True,
                workmode="launch",
                coor_agents=[]  # 添加空列表避免None错误
            ):
                events.append(event_data)
                
                # 处理不同类型的事件
                if event_data.get("event") == "start_of_agent":
                    step_count += 1
                    current_agent = event_data.get("data", {}).get("agent_name")
                    
                    # 智能体启动事件日志
                    agent_start_event_log = generate_chinese_log(
                        "workflow_agent_start_event",
                        f"🤖 工作流步骤 {step_count}: {current_agent} 智能体开始执行",
                        step_number=step_count,
                        agent_name=current_agent,
                        agent_chinese_name=get_agent_chinese_name(current_agent),
                        event_type="start_of_agent"
                    )
                    logger.info(f"中文日志: {agent_start_event_log['data']['message']}")
                    
                    if progress_callback:
                        progress = min(20 + step_count * 3, 32)
                        await progress_callback(
                            f"正在执行 {get_agent_chinese_name(current_agent)} 智能体...", 
                            progress, 
                            f"执行步骤 {step_count}", 
                            f"{current_agent} 智能体正在分析和处理任务"
                        )
                
                elif event_data.get("event") == "messages":
                    # 消息事件不记录日志，避免过多日志
                    pass
                
                # 记录最终结果
                if "agent_name" in event_data:
                    final_result = event_data
            
            # 工作流完成分析日志
            workflow_complete_log = generate_chinese_log(
                "workflow_analysis_complete",
                f"✅ 工作流分析完成，共执行了 {step_count} 个步骤",
                total_steps=step_count,
                total_events=len(events),
                final_agent=current_agent,
                analysis_result="successful"
            )
            logger.info(f"中文日志: {workflow_complete_log['data']['message']}")
            
            if progress_callback:
                await progress_callback(
                    f"多智能体协作分析完成，共执行了 {step_count} 个步骤", 
                    35, 
                    "工作流完成", 
                    f"成功通过 {step_count} 个智能体协作完成需求分析"
                )
            
            logger.info("工作流执行完成")
            return final_result
            
        except Exception as e:
            # 工作流错误详细日志
            workflow_error_log = generate_chinese_log(
                "workflow_execution_error",
                f"❌ 工作流执行过程中发生错误: {str(e)}",
                error_type=type(e).__name__,
                error_message=str(e),
                user_input=user_input[:100] + "...",
                user_id=user_id,
                execution_stage="workflow_analysis"
            )
            logger.error(f"中文日志: {workflow_error_log['data']['message']}")
            logger.error(f"工作流执行失败: {e}")
            
            if progress_callback:
                await progress_callback(f"工作流执行失败: {str(e)}", 0, "工作流错误", str(e))
            raise
    
    async def _analyze_project_requirements(self, workflow_result: Dict[str, Any], user_id: str, progress_callback=None) -> Dict[str, Any]:
        """分析项目需求并确定需要的组件"""
        
        # 需求分析启动日志
        analysis_start_log = generate_chinese_log(
            "requirements_analysis_start",
            "📊 开始分析项目需求，识别生成的智能体和工具配置",
            user_id=user_id,
            workflow_result_available=bool(workflow_result),
            analysis_stage="project_requirements"
        )
        logger.info(f"中文日志: {analysis_start_log['data']['message']}")
        
        if progress_callback:
            await progress_callback(
                "正在分析生成的智能体配置和工具需求...", 
                37, 
                "配置分析", 
                "检查工作流生成的智能体规格和工具选择"
            )
        
        # 获取本次工作流创建的智能体
        created_agents = []
        used_tools = set()
        
        # 智能体收集日志
        agent_collection_log = generate_chinese_log(
            "agent_collection_start",
            f"🔍 正在收集用户 {user_id} 创建的智能体配置",
            user_id=user_id,
            total_available_agents=len(agent_manager.available_agents),
            collection_criteria="user_specific_agents"
        )
        logger.info(f"中文日志: {agent_collection_log['data']['message']}")
        
        # 从agent_manager获取用户特定的智能体
        for agent_name, agent in agent_manager.available_agents.items():
            if hasattr(agent, 'user_id') and agent.user_id == user_id:
                created_agents.append(agent)
                # 收集使用的工具
                for tool in agent.selected_tools:
                    used_tools.add(tool.name)
                
                # 智能体发现日志
                agent_found_log = generate_chinese_log(
                    "agent_discovered",
                    f"🤖 发现用户智能体: {agent.agent_name}",
                    agent_name=agent.agent_name,
                    agent_description=agent.description[:100] + "..." if len(agent.description) > 100 else agent.description,
                    llm_type=agent.llm_type,
                    tools_count=len(agent.selected_tools)
                )
                logger.info(f"中文日志: {agent_found_log['data']['message']}")
        
        # 如果没有找到用户特定的智能体，使用默认的智能体配置
        if not created_agents:
            logger.warning(f"未找到用户 {user_id} 的专属智能体，使用默认配置")
            
            # 默认配置警告日志
            default_config_log = generate_chinese_log(
                "using_default_config",
                f"⚠️ 未找到用户专属智能体，使用默认智能体配置",
                user_id=user_id,
                fallback_reason="no_user_specific_agents_found",
                default_agents=["researcher", "coder", "reporter"]
            )
            logger.warning(f"中文日志: {default_config_log['data']['message']}")
            
            # 添加一些默认智能体
            default_agents = ["researcher", "coder", "reporter"]
            for agent_name in default_agents:
                if agent_name in agent_manager.available_agents:
                    agent = agent_manager.available_agents[agent_name]
                    created_agents.append(agent)
                    for tool in agent.selected_tools:
                        used_tools.add(tool.name)
                    
                    # 默认智能体添加日志
                    default_agent_log = generate_chinese_log(
                        "default_agent_added",
                        f"📦 添加默认智能体: {agent_name}",
                        agent_name=agent_name,
                        agent_type="default_system_agent",
                        tools_included=[tool.name for tool in agent.selected_tools]
                    )
                    logger.info(f"中文日志: {default_agent_log['data']['message']}")
        
        # 智能体分析完成日志
        agents_analysis_log = generate_chinese_log(
            "agents_analysis_complete",
            f"✅ 智能体分析完成: 共{len(created_agents)}个智能体，{len(used_tools)}个工具",
            agents_count=len(created_agents),
            tools_count=len(used_tools),
            agent_names=[agent.agent_name for agent in created_agents],
            tool_names=list(used_tools)
        )
        logger.info(f"中文日志: {agents_analysis_log['data']['message']}")
        
        if progress_callback:
            await progress_callback(
                f"已识别 {len(created_agents)} 个智能体和 {len(used_tools)} 个工具", 
                40, 
                "配置分析", 
                f"智能体: {[a.agent_name for a in created_agents]}, 工具: {list(used_tools)}"
            )
        
        # 分析需要的Cooragent组件
        components_analysis_log = generate_chinese_log(
            "components_analysis_start",
            "🔧 开始分析项目所需的Cooragent核心组件",
            agents_to_analyze=len(created_agents),
            tools_to_analyze=len(used_tools),
            component_selection="automatic"
        )
        logger.info(f"中文日志: {components_analysis_log['data']['message']}")
        
        required_components = self._determine_required_components(created_agents, used_tools)
        
        # 组件分析完成日志
        components_complete_log = generate_chinese_log(
            "components_analysis_complete",
            f"🏗️ 组件分析完成，需要{len(required_components)}类组件",
            component_categories=list(required_components.keys()),
            total_files=sum(len(files) for files in required_components.values()),
            core_components=len([k for k in required_components.keys() if k in ["interface", "workflow", "manager", "llm"]])
        )
        logger.info(f"中文日志: {components_complete_log['data']['message']}")
        
        # 生成工作流配置
        workflow_config_generation_log = generate_chinese_log(
            "workflow_config_generation",
            "⚙️ 正在生成项目工作流配置",
            agents_for_config=len(created_agents),
            config_type="custom_app_workflow"
        )
        logger.info(f"中文日志: {workflow_config_generation_log['data']['message']}")
        
        project_config = {
            "agents": created_agents,
            "tools": list(used_tools),
            "components": required_components,
            "workflow_config": self._generate_workflow_config(created_agents),
            "project_info": {
                "user_input": workflow_result.get("messages", [{}])[0].get("content", ""),
                "generated_at": datetime.now().isoformat(),
                "user_id": user_id
            }
        }
        
        # 项目配置完成日志
        project_config_complete_log = generate_chinese_log(
            "project_config_complete",
            f"📋 项目配置生成完成: {len(created_agents)}个智能体, {len(used_tools)}个工具",
            config_summary={
                "agents_count": len(created_agents),
                "tools_count": len(used_tools),
                "components_count": len(required_components),
                "generated_at": project_config["project_info"]["generated_at"]
            }
        )
        logger.info(f"中文日志: {project_config_complete_log['data']['message']}")
        
        logger.info(f"分析完成: {len(created_agents)} 个智能体, {len(used_tools)} 个工具")
        return project_config
    
    def _determine_required_components(self, agents: List[Agent], tools: set) -> Dict[str, List[str]]:
        """确定需要复制的Cooragent组件"""
        components = {
            # 核心组件 (总是需要)
            "interface": self.core_components["interface"],
            "workflow": self.core_components["workflow"],
            "manager": self.core_components["manager"],
            "llm": self.core_components["llm"],
            "prompts": self.core_components["prompts"],
            "utils": self.core_components["utils"],
            "service": self.core_components["service"],
            
            # 根据工具需求选择
            "tools": [],
            "prompts_md": ["coordinator.md", "template.py"]  # 系统提示词
        }
        
        # 根据使用的工具确定需要复制的工具文件
        for tool in tools:
            if tool in self.tool_mapping:
                components["tools"].extend(self.tool_mapping[tool])
        
        # 去重工具文件
        components["tools"] = list(set(components["tools"]))
        
        # 根据智能体确定需要的提示词
        agent_prompts = set()
        for agent in agents:
            if hasattr(agent, 'agent_name') and agent.agent_name:
                agent_prompts.add(f"{agent.agent_name}.md")
        
        components["prompts_md"].extend(list(agent_prompts))
        components["prompts_md"] = list(set(components["prompts_md"]))
        
        return components
    
    def _generate_workflow_config(self, agents: List[Agent]) -> Dict[str, Any]:
        """生成工作流配置"""
        return {
            "workflow_id": "custom_app_workflow",
            "mode": "agent_workflow",
            "version": 1,
            "agents": [
                {
                    "agent_name": agent.agent_name,
                    "description": agent.description,
                    "llm_type": agent.llm_type,
                    "selected_tools": [tool.name for tool in agent.selected_tools],
                    "user_id": getattr(agent, 'user_id', 'app_user')
                }
                for agent in agents
            ]
        }
    
    async def _generate_customized_project(self, config: Dict[str, Any], user_id: str, progress_callback=None) -> Path:
        """生成定制化的Cooragent项目"""
        project_name = f"cooragent_app_{user_id}_{int(time.time())}"
        project_path = self.output_dir / project_name
        
        # 项目生成启动日志
        project_generation_log = generate_chinese_log(
            "project_generation_start",
            f"🏗️ 开始生成定制化Cooragent项目: {project_name}",
            project_name=project_name,
            project_path=str(project_path),
            agents_count=len(config["agents"]),
            tools_count=len(config["tools"]),
            user_id=user_id
        )
        logger.info(f"中文日志: {project_generation_log['data']['message']}")
        
        if progress_callback:
            await progress_callback(
                "正在创建项目目录结构...", 
                62, 
                "代码生成", 
                f"创建项目: {project_name}"
            )
        
        # 创建项目目录结构
        structure_creation_log = generate_chinese_log(
            "project_structure_creation",
            "📁 正在创建项目目录结构",
            project_path=str(project_path),
            structure_type="cooragent_app_structure"
        )
        logger.info(f"中文日志: {structure_creation_log['data']['message']}")
        
        await self._create_project_structure(project_path)
        
        if progress_callback:
            await progress_callback(
                "正在复制Cooragent核心组件...", 
                68, 
                "代码生成", 
                "复制工作流引擎、智能体管理等核心模块"
            )
        
        # 复制并定制化Cooragent核心代码
        components_copy_log = generate_chinese_log(
            "components_copy_start",
            f"📦 开始复制Cooragent核心组件到项目中",
            source_path=str(self.cooragent_root),
            target_path=str(project_path),
            components_to_copy=list(config["components"].keys())
        )
        logger.info(f"中文日志: {components_copy_log['data']['message']}")
        
        await self._copy_cooragent_components(project_path, config["components"])
        
        if progress_callback:
            await progress_callback(
                "正在生成配置文件...", 
                75, 
                "代码生成", 
                "生成环境变量、依赖清单等配置"
            )
        
        # 生成定制化配置文件
        config_generation_log = generate_chinese_log(
            "config_generation_start",
            "⚙️ 开始生成定制化配置文件",
            config_types=["workflow", "environment", "dependencies"],
            project_path=str(project_path)
        )
        logger.info(f"中文日志: {config_generation_log['data']['message']}")
        
        await self._generate_custom_configs(project_path, config)
        
        if progress_callback:
            await progress_callback(
                "正在生成主应用入口...", 
                80, 
                "代码生成", 
                "创建基于FastAPI的Web应用入口"
            )
        
        # 生成主应用入口
        main_app_generation_log = generate_chinese_log(
            "main_app_generation",
            "🚀 正在生成主应用入口文件",
            app_type="FastAPI",
            agents_integrated=len(config["agents"]),
            tools_integrated=len(config["tools"])
        )
        logger.info(f"中文日志: {main_app_generation_log['data']['message']}")
        
        await self._generate_main_application(project_path, config)
        
        if progress_callback:
            await progress_callback(
                "正在生成部署配置...", 
                85, 
                "代码生成", 
                "创建Docker配置和启动脚本"
            )
        
        # 生成部署文件
        deployment_generation_log = generate_chinese_log(
            "deployment_generation",
            "🐳 正在生成部署配置文件",
            deployment_types=["Docker", "docker-compose", "startup_scripts"],
            project_path=str(project_path)
        )
        logger.info(f"中文日志: {deployment_generation_log['data']['message']}")
        
        await self._generate_deployment_files(project_path, config)
        
        if progress_callback:
            await progress_callback(
                "正在生成项目文档...", 
                88, 
                "代码生成", 
                "生成详细的使用说明和API文档"
            )
        
        # 生成文档
        documentation_generation_log = generate_chinese_log(
            "documentation_generation",
            "📚 正在生成项目文档",
            documentation_types=["README", "API_docs", "deployment_guide"],
            project_path=str(project_path)
        )
        logger.info(f"中文日志: {documentation_generation_log['data']['message']}")
        
        await self._generate_project_documentation(project_path, config)
        
        # 项目生成完成日志
        project_complete_log = generate_chinese_log(
            "project_generation_complete",
            f"✅ 定制化Cooragent项目生成完成: {project_name}",
            project_name=project_name,
            project_path=str(project_path),
            generation_successful=True,
            next_step="compression"
        )
        logger.info(f"中文日志: {project_complete_log['data']['message']}")
        
        return project_path
    
    async def _create_project_structure(self, project_path: Path):
        """创建项目目录结构"""
        dirs = [
            "src/interface",
            "src/workflow", 
            "src/manager",
            "src/llm",
            "src/tools",
            "src/prompts",
            "src/utils",
            "src/service",
            "config",
            "store/agents",
            "store/prompts", 
            "store/workflows",
            "static",
            "logs"
        ]
        
        for dir_path in dirs:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    async def _copy_cooragent_components(self, project_path: Path, components: Dict[str, List[str]]):
        """复制Cooragent核心组件到项目中"""
        logger.info("复制Cooragent核心组件...")
        
        src_path = project_path / "src"
        
        for component_type, files in components.items():
            if component_type == "prompts_md":
                # 特殊处理提示词文件
                target_dir = src_path / "prompts"
                source_dir = self.cooragent_root / "src" / "prompts"
                
                for file in files:
                    source_file = source_dir / file
                    if source_file.exists():
                        target_file = target_dir / file
                        if source_file.is_file():
                            shutil.copy2(source_file, target_file)
            else:
                # 复制其他组件
                target_dir = src_path / component_type
                source_dir = self.cooragent_root / "src" / component_type
                
                for file in files:
                    source_file = source_dir / file
                    if source_file.exists():
                        target_file = target_dir / file
                        if source_file.is_file():
                            shutil.copy2(source_file, target_file)
                        elif source_file.is_dir():
                            shutil.copytree(source_file, target_file, dirs_exist_ok=True)
                
                # 确保有__init__.py文件
                init_file = target_dir / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
    
    async def _generate_custom_configs(self, project_path: Path, config: Dict[str, Any]):
        """生成定制化配置文件"""
        # 生成工作流配置
        config_dir = project_path / "config"
        workflow_config_path = config_dir / "workflow.json"
        
        async with aiofiles.open(workflow_config_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(config["workflow_config"], indent=2, ensure_ascii=False))
        
        # 生成环境配置文件
        await self._generate_env_config(project_path, config)
        
        # 生成依赖文件
        await self._generate_requirements(project_path, config)
    
    async def _generate_env_config(self, project_path: Path, config: Dict[str, Any]):
        """生成环境配置文件"""
        env_content = '''# 环境配置文件
# 复制此文件为.env并填入实际值

# LLM配置 (必需)
BASIC_API_KEY=your_openai_api_key_here
BASIC_BASE_URL=https://api.openai.com/v1
BASIC_MODEL=gpt-4

CODE_API_KEY=your_code_llm_api_key_here  
CODE_BASE_URL=https://api.deepseek.com/v1
CODE_MODEL=deepseek-chat

REASONING_API_KEY=your_reasoning_api_key_here
REASONING_BASE_URL=https://api.openai.com/v1
REASONING_MODEL=o1-preview

# 工具API密钥 (根据使用的工具配置)'''

        # 根据使用的工具添加相应的API配置
        if "tavily_tool" in config["tools"]:
            env_content += '''
TAVILY_API_KEY=your_tavily_api_key_here'''
        
        if "browser_tool" in config["tools"]:
            env_content += '''
# 浏览器工具配置
USE_BROWSER=true'''
        
        env_content += '''

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 用户代理
USR_AGENT=cooragent_generated_app

# 匿名遥测 (可选)
ANONYMIZED_TELEMETRY=false
'''
        
        async with aiofiles.open(project_path / ".env.example", "w", encoding="utf-8") as f:
            await f.write(env_content)
    
    async def _generate_requirements(self, project_path: Path, config: Dict[str, Any]):
        """生成requirements.txt"""
        # 基础依赖
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.5.0",
            "python-dotenv>=1.0.0",
            "aiofiles>=23.2.1",
            "httpx>=0.25.0",
            "python-multipart>=0.0.6",
            "langchain>=0.1.0",
            "langchain-core>=0.1.0",
            "rich>=13.0.0"
        ]
        
        # 根据工具添加依赖
        tool_deps = {
            "tavily_tool": ["tavily-python>=0.3.0"],
            "python_repl_tool": ["jupyter>=1.0.0"],
            "crawl_tool": ["beautifulsoup4>=4.12.0", "requests>=2.31.0"],
            "browser_tool": ["playwright>=1.40.0"]
        }
        
        for tool in config["tools"]:
            if tool in tool_deps:
                requirements.extend(tool_deps[tool])
        
        # 去重并排序
        requirements = sorted(list(set(requirements)))
        
        async with aiofiles.open(project_path / "requirements.txt", "w", encoding="utf-8") as f:
            await f.write("\n".join(requirements))
    
    async def _generate_main_application(self, project_path: Path, config: Dict[str, Any]):
        """生成主应用入口文件"""
        from .template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        main_content = await renderer.render_main_app(config)
        
        async with aiofiles.open(project_path / "main.py", "w", encoding="utf-8") as f:
            await f.write(main_content)
    
    async def _generate_deployment_files(self, project_path: Path, config: Dict[str, Any]):
        """生成部署文件"""
        from .template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        
        # 生成Dockerfile
        dockerfile_content = await renderer.render_dockerfile(config)
        async with aiofiles.open(project_path / "Dockerfile", "w", encoding="utf-8") as f:
            await f.write(dockerfile_content)
        
        # 生成docker-compose.yml
        compose_content = await renderer.render_docker_compose(config)
        async with aiofiles.open(project_path / "docker-compose.yml", "w", encoding="utf-8") as f:
            await f.write(compose_content)
    
    async def _generate_project_documentation(self, project_path: Path, config: Dict[str, Any]):
        """生成项目文档"""
        from .template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        readme_content = await renderer.render_readme(config)
        
        async with aiofiles.open(project_path / "README.md", "w", encoding="utf-8") as f:
            await f.write(readme_content)
    
    async def _compress_project(self, project_path: Path) -> Path:
        """压缩项目目录"""
        logger.info("压缩项目文件...")
        
        zip_path = project_path.parent / f"{project_path.name}.zip"
        
        def _zip_project():
            import os
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = Path(root) / file
                        arc_path = file_path.relative_to(project_path.parent)
                        zipf.write(file_path, arc_path)
        
        # 在线程池中执行压缩操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _zip_project)
        
        # 删除原目录以节省空间
        shutil.rmtree(project_path)
        
        logger.info(f"项目已压缩: {zip_path}")
        return zip_path
    
    async def _cleanup_user_agents(self, user_id: str, progress_callback=None):
        """清理临时生成的用户智能体"""
        try:
            agents_to_remove = []
            for agent_name, agent in agent_manager.available_agents.items():
                if hasattr(agent, 'user_id') and agent.user_id == user_id:
                    agents_to_remove.append(agent_name)
            
            for agent_name in agents_to_remove:
                await agent_manager._remove_agent(agent_name)
                
            if agents_to_remove:
                logger.info(f"已清理用户 {user_id} 的 {len(agents_to_remove)} 个临时智能体")
                
                # 记录清理完成的中文日志
                if progress_callback:
                    cleanup_log = generate_chinese_log(
                        "cleanup_complete",
                        f"🧹 已成功清理 {len(agents_to_remove)} 个临时智能体",
                        user_id=user_id,
                        cleaned_agents=agents_to_remove,
                        cleanup_count=len(agents_to_remove)
                    )
                    logger.info(f"中文日志: {cleanup_log['data']['message']}")
                
        except Exception as e:
            logger.warning(f"清理用户智能体时出错: {e}")
            
            # 记录清理错误的中文日志  
            if progress_callback:
                cleanup_error_log = generate_chinese_log(
                    "cleanup_error",
                    f"⚠️ 清理临时智能体时出现问题: {str(e)}",
                    user_id=user_id,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                logger.warning(f"中文日志: {cleanup_error_log['data']['message']}") 