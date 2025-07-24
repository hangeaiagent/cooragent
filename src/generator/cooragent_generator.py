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
        
        if progress_callback:
            await progress_callback("正在初始化项目生成器...", 5, "初始化", "设置环境和参数")
        
        try:
            # 1. 调用现有工作流系统获取智能体配置
            if progress_callback:
                await progress_callback("正在调用Cooragent工作流分析需求...", 15, "需求分析", "使用AI智能体协作分析用户需求")
            
            workflow_result = await self._run_workflow(user_input, user_id, progress_callback)
            
            # 2. 分析生成的智能体和工具需求
            if progress_callback:
                await progress_callback("正在分析智能体配置和工具需求...", 35, "配置分析", "确定需要的智能体类型和工具组件")
            
            project_config = await self._analyze_project_requirements(workflow_result, user_id, progress_callback)
            
            # 3. 复制Cooragent核心代码并定制化
            if progress_callback:
                await progress_callback("正在生成定制化项目代码...", 60, "代码生成", f"基于{len(project_config['agents'])}个智能体生成项目结构")
            
            project_path = await self._generate_customized_project(project_config, user_id, progress_callback)
            
            # 4. 压缩项目
            if progress_callback:
                await progress_callback("正在压缩项目文件...", 90, "项目打包", "生成可下载的压缩包")
            
            zip_path = await self._compress_project(project_path)
            
            if progress_callback:
                await progress_callback("项目生成完成！", 100, "完成", f"已生成基于Cooragent的多智能体应用")
            
            logger.info(f"项目生成完成: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"项目生成失败: {e}")
            if progress_callback:
                await progress_callback(f"生成失败: {str(e)}", 0, "错误", f"详细错误: {str(e)}")
            raise
        finally:
            # 清理临时生成的智能体
            if progress_callback:
                await progress_callback("正在清理临时文件...", 95, "清理", "清理临时生成的智能体配置")
            await self._cleanup_user_agents(user_id)
    
    async def _run_workflow(self, user_input: str, user_id: str, progress_callback=None) -> Dict[str, Any]:
        """调用现有工作流系统分析需求"""
        logger.info("调用Cooragent工作流分析用户需求...")
        
        try:
            # 构建消息格式
            messages = [{"role": "user", "content": user_input}]
            
            if progress_callback:
                await progress_callback("正在启动Cooragent智能体协作...", 18, "工作流启动", "初始化多智能体协作环境")
            
            # 使用Launch模式分析用户需求并生成智能体配置
            # run_agent_workflow 返回异步生成器，需要迭代处理
            final_result = {}
            events = []
            step_count = 0
            
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
                step_count += 1
                
                # 根据事件类型更新进度
                if event_data.get("event") == "start_of_agent":
                    agent_name = event_data.get("data", {}).get("agent_name", "unknown")
                    if progress_callback:
                        progress = min(20 + step_count * 2, 32)
                        await progress_callback(f"智能体 {agent_name} 开始执行...", progress, "智能体协作", f"正在执行 {agent_name} 智能体任务")
                
                elif event_data.get("event") == "end_of_agent":
                    agent_name = event_data.get("data", {}).get("agent_name", "unknown")
                    if progress_callback:
                        progress = min(22 + step_count * 2, 33)
                        await progress_callback(f"智能体 {agent_name} 执行完成", progress, "智能体协作", f"{agent_name} 已完成任务并生成结果")
                
                # 保存最终状态
                if event_data.get("event") == "end_of_workflow":
                    final_result = event_data.get("data", {})
                    if progress_callback:
                        await progress_callback("工作流执行完成，正在整理结果...", 34, "结果整理", "多智能体协作完成，正在处理生成结果")
                elif "data" in event_data and isinstance(event_data["data"], dict):
                    # 更新最终结果，保留最新的状态信息
                    final_result.update(event_data["data"])
            
            # 如果没有明确的结束事件，使用最后一个事件的数据
            if not final_result and events:
                final_result = events[-1].get("data", {})
            
            # 确保结果包含消息历史
            if "messages" not in final_result:
                final_result["messages"] = messages
            
            logger.info("工作流执行完成")
            return final_result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            if progress_callback:
                await progress_callback(f"工作流执行失败: {str(e)}", 0, "工作流错误", str(e))
            raise
    
    async def _analyze_project_requirements(self, workflow_result: Dict[str, Any], user_id: str, progress_callback=None) -> Dict[str, Any]:
        """分析项目需求并确定需要的组件"""
        logger.info("分析项目需求和智能体配置...")
        
        if progress_callback:
            await progress_callback("正在分析生成的智能体配置...", 37, "配置分析", "检查工作流生成的智能体和工具")
        
        # 获取本次工作流创建的智能体
        created_agents = []
        used_tools = set()
        
        # 从agent_manager获取用户特定的智能体
        for agent_name, agent in agent_manager.available_agents.items():
            if hasattr(agent, 'user_id') and agent.user_id == user_id:
                created_agents.append(agent)
                # 收集使用的工具
                for tool in agent.selected_tools:
                    used_tools.add(tool.name)
        
        # 如果没有找到用户特定的智能体，使用默认的智能体配置
        if not created_agents:
            logger.warning(f"未找到用户 {user_id} 的专属智能体，使用默认配置")
            # 添加一些默认智能体
            default_agents = ["researcher", "coder", "reporter"]
            for agent_name in default_agents:
                if agent_name in agent_manager.available_agents:
                    agent = agent_manager.available_agents[agent_name]
                    created_agents.append(agent)
                    for tool in agent.selected_tools:
                        used_tools.add(tool.name)
        
        if progress_callback:
            await progress_callback(f"已识别 {len(created_agents)} 个智能体和 {len(used_tools)} 个工具", 40, "配置分析", f"智能体: {[a.agent_name for a in created_agents]}, 工具: {list(used_tools)}")
        
        # 分析需要的Cooragent组件
        required_components = self._determine_required_components(created_agents, used_tools)
        
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
        
        logger.info(f"生成项目: {project_path}")
        
        if progress_callback:
            await progress_callback("正在创建项目目录结构...", 62, "代码生成", f"创建项目: {project_name}")
        
        # 创建项目目录结构
        await self._create_project_structure(project_path)
        
        if progress_callback:
            await progress_callback("正在复制Cooragent核心组件...", 68, "代码生成", "复制工作流引擎、智能体管理等核心模块")
        
        # 复制并定制化Cooragent核心代码
        await self._copy_cooragent_components(project_path, config["components"])
        
        if progress_callback:
            await progress_callback("正在生成配置文件...", 75, "代码生成", "生成环境变量、依赖清单等配置")
        
        # 生成定制化配置文件
        await self._generate_custom_configs(project_path, config)
        
        if progress_callback:
            await progress_callback("正在生成主应用入口...", 80, "代码生成", "创建基于FastAPI的Web应用入口")
        
        # 生成主应用入口
        await self._generate_main_application(project_path, config)
        
        if progress_callback:
            await progress_callback("正在生成部署配置...", 85, "代码生成", "创建Docker配置和启动脚本")
        
        # 生成部署文件
        await self._generate_deployment_files(project_path, config)
        
        if progress_callback:
            await progress_callback("正在生成项目文档...", 88, "代码生成", "生成详细的使用说明和API文档")
        
        # 生成文档
        await self._generate_project_documentation(project_path, config)
        
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
    
    async def _cleanup_user_agents(self, user_id: str):
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
                
        except Exception as e:
            logger.warning(f"清理用户智能体时出错: {e}") 