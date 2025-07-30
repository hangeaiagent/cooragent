"""
基于Cooragent架构的项目代码生成器 - 增强版

该模块实现了从用户需求到完整Cooragent项目的自动生成流程
包含工作流同步化、动态组件分析、MCP生态集成等增强功能
"""

import asyncio
import json
import logging
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import aiofiles

from src.interface.agent import Agent, TaskType
from src.manager import agent_manager
from src.workflow.process import run_agent_workflow
from src.generator.config_generator import ConfigGenerator
from src.utils.path_utils import get_project_root

logger = logging.getLogger(__name__)


class DynamicComponentAnalyzer:
    """动态组件需求分析器"""
    
    def __init__(self):
        self.core_components = {
            "interface": ["agent.py", "workflow.py", "serializer.py", "mcp.py", "__init__.py"],
            "workflow": [
                "graph.py", "process.py", "cache.py", "template.py", 
                "coor_task.py", "agent_factory.py", "dynamic.py", "manager.py",
                "polish_task.py", "__init__.py"
            ],
            "manager": ["agents.py", "mcp.py", "__init__.py"],
            "llm": ["llm.py", "agents.py", "__init__.py"],
            "utils": ["path_utils.py", "content_process.py", "chinese_names.py", "file_cleaner.py", "__init__.py"],
            "service": ["server.py", "session.py", "env.py", "tool_tracker.py", "__init__.py"],
            "prompts": ["template.py", "__init__.py"]
        }
        
        self.tool_dependencies = {
            "tavily_tool": ["search.py", "decorators.py"],
            "python_repl_tool": ["python_repl.py", "decorators.py"],
            "bash_tool": ["bash_tool.py", "decorators.py"],
            "crawl_tool": ["crawl.py", "crawler/", "decorators.py"],
            "browser_tool": ["browser.py", "browser_decorators.py", "decorators.py"],
            "excel_tool": ["excel/", "decorators.py"],
            "gmail_tool": ["gmail.py", "decorators.py"],
            "slack_tool": ["slack.py", "decorators.py"],
            "video_tool": ["video.py", "decorators.py"],
            "file_management_tool": ["file_management.py", "decorators.py"],
            "avatar_tool": ["avatar_tool.py", "decorators.py"],
            "office365_tool": ["office365.py", "decorators.py"],
            "web_preview_tool": ["web_preview_tool.py", "web_preview/", "decorators.py"],
            "websocket_tool": ["websocket_manager.py", "decorators.py"],
            "decorators": ["decorators.py"]
        }
        
        self.mcp_dependencies = {
            "mcp_doc": ["MCP-Doc/"],
            "mcp_image_downloader": ["mcp-image-downloader/"],
            "filesystem": ["需要mcp配置"]
        }
    
    async def analyze_requirements(self, agents_config: Dict[str, Any]) -> Dict[str, Any]:
        """动态分析项目需求"""
        
        agents = agents_config["agents"]
        tools_used = agents_config["tools_used"]
        
        requirements = {
            "core_components": self.core_components.copy(),
            "tool_components": {},
            "mcp_components": {},
            "llm_requirements": {},
            "workflow_requirements": {},
            "deployment_requirements": {}
        }
        
        # 分析LLM需求
        llm_types = set(agent.llm_type for agent in agents)
        requirements["llm_requirements"] = {
            "types": list(llm_types),
            "reasoning_enabled": "reasoning" in llm_types,
            "vision_enabled": "vision" in llm_types,
            "code_enabled": "code" in llm_types
        }
        
        # 根据LLM类型添加组件
        if "reasoning" in llm_types:
            requirements["core_components"]["llm"].append("reasoning_config.py")
        if "vision" in llm_types:
            requirements["core_components"]["llm"].append("vision_config.py")
        
        # 分析工具需求
        for tool in tools_used:
            if tool in self.tool_dependencies:
                requirements["tool_components"][tool] = self.tool_dependencies[tool]
            elif tool.startswith("mcp_"):
                requirements["mcp_components"][tool] = self.mcp_dependencies.get(tool, [])
        
        # 确保decorators.py总是被包含，所有工具都需要它
        if requirements["tool_components"]:
            requirements["tool_components"]["decorators"] = ["decorators.py"]
        
        # 如果使用了MCP工具，需要MCP管理器
        if requirements["mcp_components"]:
            requirements["core_components"]["manager"].append("mcp.py")
        
        # 分析工作流需求
        agent_count = len(agents)
        requirements["workflow_requirements"] = {
            "agent_count": agent_count,
            "needs_factory": any(agent.agent_name != "agent_factory" for agent in agents),
            "needs_cache": agent_count > 1,
            "needs_state_management": True,
            "complexity": "complex" if agent_count > 3 else "simple"
        }
        
        # 分析部署需求
        requirements["deployment_requirements"] = {
            "needs_docker": True,
            "needs_env_config": True,
            "needs_startup_scripts": True,
            "needs_nginx": agent_count > 3,
            "estimated_memory": f"{max(512, agent_count * 128)}MB"
        }
        
        return requirements


class MCPEcosystemIntegrator:
    """MCP生态系统集成器"""
    
    async def integrate_mcp_ecosystem(self, project_path: Path, tools_used: List[str], progress_callback=None):
        """集成完整的MCP生态系统"""
        
        if progress_callback:
            await progress_callback("集成MCP生态系统...", 70, "MCP集成", "配置MCP工具和服务器")
        
        # 1. 复制MCP管理器
        await self._copy_mcp_manager(project_path)
        
        # 2. 生成MCP配置文件
        await self._generate_mcp_config(project_path, tools_used)
        
        # 3. 复制MCP工具服务器
        await self._copy_mcp_tools(project_path, tools_used)
        
        # 4. 生成MCP安装脚本
        await self._generate_mcp_setup_scripts(project_path, tools_used)
    
    async def _copy_mcp_manager(self, project_path: Path):
        """复制MCP管理器"""
        cooragent_root = get_project_root()
        mcp_manager_source = cooragent_root / "src" / "manager" / "mcp.py"
        mcp_manager_target = project_path / "src" / "manager" / "mcp.py"
        
        if mcp_manager_source.exists():
            shutil.copy2(mcp_manager_source, mcp_manager_target)
    
    async def _generate_mcp_config(self, project_path: Path, tools_used: List[str]):
        """生成MCP配置文件"""
        
        mcp_config = {
            "mcpServers": {}
        }
        
        # 基础文件系统工具（大多数项目都需要）
        mcp_config["mcpServers"]["filesystem"] = {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(project_path / "store"),
                str(project_path / "static")
            ]
        }
        
        # 根据使用的工具添加MCP服务器
        if "mcp_doc" in tools_used:
            mcp_config["mcpServers"]["mcp-doc"] = {
                "command": "python",
                "args": [str(project_path / "src" / "tools" / "MCP-Doc" / "server.py")],
                "env": {}
            }
        
        if "mcp_image_downloader" in tools_used:
            mcp_config["mcpServers"]["image-downloader"] = {
                "command": "node",
                "args": [str(project_path / "src" / "tools" / "mcp-image-downloader" / "build" / "index.js")],
                "env": {}
            }
        
        # 保存配置文件
        config_path = project_path / "config" / "mcp.json"
        async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(mcp_config, indent=2, ensure_ascii=False))
    
    async def _copy_mcp_tools(self, project_path: Path, tools_used: List[str]):
        """复制MCP工具服务器"""
        cooragent_root = get_project_root()
        tools_source_dir = cooragent_root / "src" / "tools"
        tools_target_dir = project_path / "src" / "tools"
        
        mcp_tools_mapping = {
            "mcp_doc": "MCP-Doc",
            "mcp_image_downloader": "mcp-image-downloader"
        }
        
        for tool in tools_used:
            if tool in mcp_tools_mapping:
                tool_dir = mcp_tools_mapping[tool]
                source_path = tools_source_dir / tool_dir
                target_path = tools_target_dir / tool_dir
                
                if source_path.exists():
                    shutil.copytree(source_path, target_path, dirs_exist_ok=True)
    
    async def _generate_mcp_setup_scripts(self, project_path: Path, tools_used: List[str]):
        """生成MCP安装脚本"""
        
        setup_script = '''#!/bin/bash
# MCP工具安装脚本

echo "正在安装MCP工具依赖..."

# 安装Node.js MCP工具
if command -v npm &> /dev/null; then
    echo "安装文件系统MCP服务器..."
    npm install -g @modelcontextprotocol/server-filesystem
    
'''
        
        if "mcp_image_downloader" in tools_used:
            setup_script += '''    echo "构建图片下载器MCP工具..."
    cd src/tools/mcp-image-downloader
    npm install
    npm run build
    cd ../../../
    
'''
        
        setup_script += '''else
    echo "警告: 未找到npm，请手动安装Node.js和npm"
fi

# 安装Python MCP工具依赖
if [ -f requirements.txt ]; then
    echo "安装Python依赖..."
    pip install -r requirements.txt
fi

echo "MCP工具安装完成！"
'''
        
        script_path = project_path / "setup_mcp.sh"
        async with aiofiles.open(script_path, "w", encoding="utf-8") as f:
            await f.write(setup_script)
        
        # 设置执行权限
        script_path.chmod(0o755)


class ProjectIntegrityValidator:
    """项目完整性验证器"""
    
    async def validate_project_integrity(self, project_path: Path, requirements: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """验证生成项目的完整性"""
        
        if progress_callback:
            await progress_callback("验证项目完整性...", 95, "项目验证", "检查目录结构、配置文件和智能体完整性")
        
        validation_results = {
            "structure_check": await self._validate_directory_structure(project_path),
            "dependencies_check": await self._validate_dependencies(project_path),
            "configuration_check": await self._validate_configurations(project_path),
            "agents_check": await self._validate_agents_integrity(project_path),
            "runtime_check": await self._validate_runtime_requirements(project_path)
        }
        
        overall_status = all(result["status"] == "pass" for result in validation_results.values())
        
        return {
            "overall_status": "pass" if overall_status else "warning",
            "validation_results": validation_results,
            "recommendations": self._generate_recommendations(validation_results)
        }
    
    async def _validate_directory_structure(self, project_path: Path) -> Dict[str, Any]:
        """验证目录结构"""
        required_dirs = [
            "src/interface", "src/workflow", "src/manager", "src/llm",
            "src/tools", "src/prompts", "src/utils", "src/service",
            "config", "store/agents", "store/prompts", "store/workflows", "static"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not (project_path / dir_path).exists():
                missing_dirs.append(dir_path)
        
        return {
            "status": "pass" if not missing_dirs else "fail",
            "missing_directories": missing_dirs,
            "total_required": len(required_dirs)
        }
    
    async def _validate_agents_integrity(self, project_path: Path) -> Dict[str, Any]:
        """验证智能体完整性"""
        
        agents_dir = project_path / "store" / "agents"
        prompts_dir = project_path / "store" / "prompts"
        
        agent_files = list(agents_dir.glob("*.json"))
        prompt_files = list(prompts_dir.glob("*.md"))
        
        missing_prompts = []
        invalid_agents = []
        
        for agent_file in agent_files:
            try:
                # 验证JSON格式
                async with aiofiles.open(agent_file, "r", encoding="utf-8") as f:
                    agent_data = json.loads(await f.read())
                
                # 验证必需字段
                required_fields = ["agent_name", "description", "llm_type", "selected_tools", "prompt"]
                missing_fields = [field for field in required_fields if field not in agent_data]
                
                if missing_fields:
                    invalid_agents.append({
                        "file": agent_file.name,
                        "missing_fields": missing_fields
                    })
                
                # 检查对应的提示词文件
                prompt_file = prompts_dir / f"{agent_data['agent_name']}.md"
                if not prompt_file.exists():
                    missing_prompts.append(agent_data['agent_name'])
                
            except Exception as e:
                invalid_agents.append({
                    "file": agent_file.name,
                    "error": str(e)
                })
        
        status = "pass" if not missing_prompts and not invalid_agents else "fail"
        
        return {
            "status": status,
            "agent_count": len(agent_files),
            "prompt_count": len(prompt_files),
            "missing_prompts": missing_prompts,
            "invalid_agents": invalid_agents
        }
    
    async def _validate_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """验证依赖文件"""
        required_files = ["requirements.txt", ".env.example", "main.py"]
        missing_files = []
        
        for file_name in required_files:
            if not (project_path / file_name).exists():
                missing_files.append(file_name)
        
        return {
            "status": "pass" if not missing_files else "fail",
            "missing_files": missing_files
        }
    
    async def _validate_configurations(self, project_path: Path) -> Dict[str, Any]:
        """验证配置文件"""
        config_files = ["config/workflow.json"]
        invalid_configs = []
        
        for config_file in config_files:
            config_path = project_path / config_file
            if config_path.exists():
                try:
                    async with aiofiles.open(config_path, "r", encoding="utf-8") as f:
                        json.loads(await f.read())
                except json.JSONDecodeError as e:
                    invalid_configs.append({
                        "file": config_file,
                        "error": str(e)
                    })
        
        return {
            "status": "pass" if not invalid_configs else "fail",
            "invalid_configs": invalid_configs
        }
    
    async def _validate_runtime_requirements(self, project_path: Path) -> Dict[str, Any]:
        """验证运行时需求"""
        issues = []
        
        # 检查主应用文件
        main_py = project_path / "main.py"
        if not main_py.exists():
            issues.append("缺少主应用入口文件 main.py")
        
        # 检查启动脚本
        start_script = project_path / "start.sh"
        if not start_script.exists():
            issues.append("缺少启动脚本 start.sh")
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues
        }
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for check_name, result in validation_results.items():
            if result["status"] == "fail":
                if check_name == "structure_check" and result.get("missing_directories"):
                    recommendations.append(f"创建缺失的目录: {', '.join(result['missing_directories'])}")
                elif check_name == "agents_check" and result.get("missing_prompts"):
                    recommendations.append(f"补充缺失的提示词文件: {', '.join(result['missing_prompts'])}")
                elif check_name == "dependencies_check" and result.get("missing_files"):
                    recommendations.append(f"添加缺失的依赖文件: {', '.join(result['missing_files'])}")
        
        return recommendations


class EnhancedCooragentProjectGenerator:
    """增强的Cooragent项目生成器"""
    
    def __init__(self, output_dir: str = "generated_projects"):
        self.cooragent_root = get_project_root()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.component_analyzer = DynamicComponentAnalyzer()
        self.mcp_integrator = MCPEcosystemIntegrator()
        self.validator = ProjectIntegrityValidator()
        self.config_generator = ConfigGenerator()
    
    async def generate_project(self, user_input: str, user_id: str = None, progress_callback=None) -> Path:
        """
        增强的项目生成流程
        
        Args:
            user_input: 用户需求描述
            user_id: 用户ID，用于隔离不同用户的智能体
            progress_callback: 进度更新回调函数
            
        Returns:
            生成的压缩包路径
        """
        if user_id is None:
            user_id = f"gen_{int(time.time())}"
            
        logger.info(f"开始为用户 {user_id} 生成增强项目，需求: {user_input[:100]}...")
        
        if progress_callback:
            await progress_callback(
                "初始化增强代码生成器...", 
                5, "初始化", "设置Cooragent增强生成环境和组件"
            )
        
        try:
            # 第一阶段：执行完整工作流并等待完成
            workflow_result = await self._execute_complete_workflow(user_input, user_id, progress_callback)
            
            # 第二阶段：从store读取智能体配置
            agents_config = await self._load_agents_from_store(user_id, progress_callback)
            
            # 第三阶段：动态分析项目需求
            project_requirements = await self._analyze_dynamic_requirements(agents_config, progress_callback)
            
            # 第四阶段：生成独立项目
            project_path = await self._generate_independent_project(project_requirements, agents_config, progress_callback)
            
            # 第五阶段：验证项目完整性
            validation_result = await self.validator.validate_project_integrity(project_path, project_requirements, progress_callback)
            
            # 第六阶段：压缩项目
            if progress_callback:
                await progress_callback("压缩项目文件...", 98, "项目打包", "生成可下载的完整应用包")
            
            zip_path = await self._compress_project(project_path)
            
            if progress_callback:
                await progress_callback(
                    f"生成完成！验证状态: {validation_result['overall_status']}", 
                    100, "完成", 
                    f"项目已打包为: {zip_path.name}"
                )
            
            logger.info(f"增强项目生成完成: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"增强项目生成失败: {e}")
            
            if progress_callback:
                await progress_callback(f"生成失败: {str(e)}", 0, "错误", f"详细错误信息: {str(e)}")
            raise
        finally:
            # 清理临时生成的智能体
            await self._cleanup_user_agents(user_id, progress_callback)
    
    async def _execute_complete_workflow(self, user_input: str, user_id: str, progress_callback=None) -> Dict[str, Any]:
        """执行完整的工作流并等待所有智能体创建完成"""
        
        if progress_callback:
            await progress_callback("启动Cooragent多智能体协作分析...", 10, "工作流执行", "初始化协调器、规划器、智能体工厂")
        
        messages = [{"role": "user", "content": user_input}]
        final_result = {}
        events = []
        
        logger.info("开始执行完整工作流...")
        
        # 执行完整工作流
        async for event_data in run_agent_workflow(
            user_id=user_id,
            task_type=TaskType.AGENT_WORKFLOW,
            user_input_messages=messages,
            debug=False,
            deep_thinking_mode=True,
            search_before_planning=True,
            workmode="launch"
        ):
            events.append(event_data)
            
            # 更新进度
            if event_data.get("event") == "start_of_agent":
                agent_name = event_data.get("data", {}).get("agent_name")
                if progress_callback:
                    progress = min(15 + len(events), 25)
                    await progress_callback(
                        f"执行 {agent_name} 智能体...", 
                        progress, 
                        "多智能体协作", 
                        f"当前执行: {agent_name}"
                    )
            
            final_result = event_data
        
        # 等待智能体完全创建和持久化
        if progress_callback:
            await progress_callback("等待智能体配置持久化完成...", 30, "配置同步", "确保所有智能体配置已保存到store目录")
        
        logger.info("工作流执行完成，等待智能体持久化...")
        await asyncio.sleep(3)  # 给足时间让智能体完全创建和持久化
        
        return final_result
    
    async def _load_agents_from_store(self, user_id: str, progress_callback=None) -> Dict[str, Any]:
        """从store目录读取用户的智能体配置"""
        
        if progress_callback:
            await progress_callback("从store目录加载智能体配置...", 35, "配置加载", "读取持久化的智能体和提示词文件")
        
        agents = []
        prompts = {}
        tools_used = set()
        
        # 读取智能体配置文件
        agents_dir = get_project_root() / "store" / "agents"
        prompts_dir = get_project_root() / "store" / "prompts"
        
        logger.info(f"从 {agents_dir} 加载智能体配置...")
        
        for agent_file in agents_dir.glob("*.json"):
            try:
                async with aiofiles.open(agent_file, "r", encoding="utf-8") as f:
                    agent_data = json.loads(await f.read())
                
                # 只收集属于该用户的智能体
                if agent_data.get("user_id") == user_id:
                    agent = Agent.model_validate(agent_data)
                    agents.append(agent)
                    
                    logger.info(f"找到用户智能体: {agent.agent_name}")
                    
                    # 收集使用的工具
                    for tool in agent.selected_tools:
                        tools_used.add(tool.name)
                    
                    # 读取对应的提示词文件
                    prompt_file = prompts_dir / f"{agent.agent_name}.md"
                    if prompt_file.exists():
                        async with aiofiles.open(prompt_file, "r", encoding="utf-8") as f:
                            prompts[agent.agent_name] = await f.read()
                    
            except Exception as e:
                logger.warning(f"Failed to load agent from {agent_file}: {e}")
        
        # 如果没有找到用户特定的智能体，使用默认配置
        if not agents:
            logger.warning(f"未找到用户 {user_id} 的专属智能体，使用默认配置")
            
            # 添加一些默认智能体
            default_agents = ["researcher", "coder", "reporter"]
            for agent_name in default_agents:
                if agent_name in agent_manager.available_agents:
                    agent = agent_manager.available_agents[agent_name]
                    # 修改user_id为当前用户
                    agent_data = agent.model_dump()
                    agent_data["user_id"] = user_id
                    agent = Agent.model_validate(agent_data)
                    agents.append(agent)
                    
                    for tool in agent.selected_tools:
                        tools_used.add(tool.name)
        
        if progress_callback:
            await progress_callback(
                f"成功加载 {len(agents)} 个智能体配置", 
                40, 
                "配置加载完成", 
                f"智能体: {[a.agent_name for a in agents]}, 工具: {list(tools_used)}"
            )
        
        logger.info(f"智能体配置加载完成: {len(agents)} 个智能体, {len(tools_used)} 个工具")
        
        return {
            "agents": agents,
            "prompts": prompts,
            "tools_used": list(tools_used),
            "user_id": user_id
        }
    
    async def _analyze_dynamic_requirements(self, agents_config: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """动态分析项目需求"""
        
        if progress_callback:
            await progress_callback("动态分析项目需求...", 45, "需求分析", "根据智能体配置分析所需组件和依赖")
        
        requirements = await self.component_analyzer.analyze_requirements(agents_config)
        
        logger.info(f"项目需求分析完成: {len(requirements['core_components'])} 类核心组件, {len(requirements['tool_components'])} 个工具组件")
        
        return requirements
    
    async def _generate_independent_project(self, requirements: Dict[str, Any], agents_config: Dict[str, Any], progress_callback=None) -> Path:
        """生成独立可运行的项目"""
        
        project_name = f"cooragent_app_{int(time.time())}"
        project_path = self.output_dir / project_name
        
        # 1. 创建项目结构
        await self._create_enhanced_project_structure(project_path, requirements)
        
        # 2. 复制和定制核心组件
        if progress_callback:
            await progress_callback("复制Cooragent核心组件...", 50, "项目构建", "复制智能体管理、工作流引擎等核心模块")
        
        await self._copy_and_customize_components(project_path, requirements)
        
        # 3. 生成智能体配置文件
        if progress_callback:
            await progress_callback("生成智能体配置...", 60, "智能体配置", "创建智能体JSON配置和提示词文件")
        
        await self._generate_agent_configs(project_path, agents_config)
        
        # 4. 集成MCP生态系统
        await self.mcp_integrator.integrate_mcp_ecosystem(project_path, agents_config["tools_used"], progress_callback)
        
        # 5. 生成独立的主应用
        if progress_callback:
            await progress_callback("生成主应用入口...", 75, "应用生成", "创建FastAPI应用和路由配置")
        
        await self._generate_independent_main_app(project_path, requirements, agents_config)
        
        # 6. 生成环境配置和依赖文件
        if progress_callback:
            await progress_callback("生成环境配置...", 80, "环境配置", "创建环境变量、依赖文件和配置模板")
        
        await self._generate_environment_configs(project_path, requirements, agents_config)
        await self._generate_requirements(project_path, agents_config)
        
        # 7. 生成部署文件
        if progress_callback:
            await progress_callback("生成部署文件...", 85, "部署配置", "创建Docker、docker-compose和启动脚本")
        
        await self._generate_deployment_configs(project_path, requirements, agents_config)
        
        # 8. 生成缺失的系统文件
        if progress_callback:
            await progress_callback("生成缺失的系统文件...", 88, "系统文件", "创建chinese_names.py、coor_task.py等自创建文件")
        
        await self._generate_missing_system_files(project_path, agents_config)
        
        # 9. 生成文档
        if progress_callback:
            await progress_callback("生成项目文档...", 90, "文档生成", "创建README、API文档和使用指南")
        
        await self._generate_comprehensive_documentation(project_path, requirements, agents_config)
        
        return project_path
    
    async def _create_enhanced_project_structure(self, project_path: Path, requirements: Dict[str, Any]):
        """创建增强的项目目录结构"""
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
    
    async def _copy_and_customize_components(self, project_path: Path, requirements: Dict[str, Any]):
        """复制和定制化Cooragent核心组件"""
        logger.info("复制Cooragent核心组件...")
        
        src_path = project_path / "src"
        
        # 复制核心组件
        for component_type, files in requirements["core_components"].items():
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
        
        # 复制工具组件
        for tool_name, files in requirements["tool_components"].items():
            tools_source_dir = self.cooragent_root / "src" / "tools"
            tools_target_dir = src_path / "tools"
            
            # 确保tools目录存在
            tools_target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                source_file = tools_source_dir / file
                if source_file.exists():
                    if source_file.is_file():
                        target_file = tools_target_dir / file
                        shutil.copy2(source_file, target_file)
                    elif source_file.is_dir():
                        target_dir = tools_target_dir / file
                        shutil.copytree(source_file, target_dir, dirs_exist_ok=True)
                else:
                    logger.warning(f"工具文件不存在: {source_file}")
            
            # 确保tools目录有__init__.py文件
            tools_init_file = src_path / "tools" / "__init__.py"
            if not tools_init_file.exists():
                tools_init_file.touch()
        
        # 复制MCP管理器
        mcp_manager_source = self.cooragent_root / "src" / "manager" / "mcp.py"
        mcp_manager_target = project_path / "src" / "manager" / "mcp.py"
        if mcp_manager_source.exists():
            shutil.copy2(mcp_manager_source, mcp_manager_target)
        
        # 复制MCP工具服务器
        for tool_name, files in requirements["mcp_components"].items():
            tools_source_dir = self.cooragent_root / "src" / "tools"
            tools_target_dir = src_path / "tools"
            
            # 确保tools目录存在
            tools_target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                source_file = tools_source_dir / file
                if source_file.exists():
                    if source_file.is_file():
                        target_file = tools_target_dir / file
                        shutil.copy2(source_file, target_file)
                    elif source_file.is_dir():
                        target_dir = tools_target_dir / file
                        shutil.copytree(source_file, target_dir, dirs_exist_ok=True)
                else:
                    logger.warning(f"MCP工具文件不存在: {source_file}")
            
            # 确保tools目录有__init__.py文件
            tools_init_file = src_path / "tools" / "__init__.py"
            if not tools_init_file.exists():
                tools_init_file.touch()
    
    async def _generate_agent_configs(self, project_path: Path, agents_config: Dict[str, Any]):
        """生成智能体配置文件"""
        agents_dir = project_path / "store" / "agents"
        prompts_dir = project_path / "store" / "prompts"
        
        for agent in agents_config["agents"]:
            agent_data = agent.model_dump()
            agent_data["user_id"] = agents_config["user_id"]
            
            agent_file = agents_dir / f"{agent_data['agent_name']}.json"
            async with aiofiles.open(agent_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(agent_data, indent=2, ensure_ascii=False))
            
            prompt_file = prompts_dir / f"{agent_data['agent_name']}.md"
            if agent_data["prompt"]:
                async with aiofiles.open(prompt_file, "w", encoding="utf-8") as f:
                    await f.write(agent_data["prompt"])
            else:
                prompt_file.touch() # 确保提示词文件存在
    
    async def _generate_environment_configs(self, project_path: Path, requirements: Dict[str, Any], agents_config: Dict[str, Any]):
        """生成环境配置文件"""
        env_content = '''# ==========================================
# Cooragent 多智能体应用环境配置
# 基于历史文档需求的完整配置
# 复制此文件为.env并填入实际值
# ==========================================

# === LLM模型配置 (基于历史文档要求) ===
# 推理模型配置
REASONING_API_KEY=your_reasoning_api_key_here
REASONING_BASE_URL=https://api.openai.com/v1
REASONING_MODEL=o1-preview

# 基础模型配置
BASIC_API_KEY=your_basic_api_key_here
BASIC_BASE_URL=https://api.openai.com/v1
BASIC_MODEL=gpt-4

# 代码模型配置
CODE_API_KEY=your_code_api_key_here
CODE_BASE_URL=https://api.deepseek.com/v1
CODE_MODEL=deepseek-chat

# 视觉模型配置
VL_API_KEY=your_vl_api_key_here
VL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
VL_MODEL=qwen2.5-vl-72b-instruct

# === 工作流配置 ===
MAX_STEPS=25
MCP_AGENT=true
USE_BROWSER=false

# === 工具API密钥 (根据使用的工具配置) ===
TAVILY_API_KEY=your_tavily_api_key_here
JINA_API_KEY=your_jina_api_key_here'''

        # 根据使用的工具添加相应的API配置
        for tool in agents_config["tools_used"]:
            if tool in self.component_analyzer.tool_dependencies:
                tool_deps = self.component_analyzer.tool_dependencies[tool]
                for dep in tool_deps:
                    if dep.startswith("mcp_"):
                        env_content += f'''
{dep.upper()}_API_KEY=your_{dep.replace("_", "").replace("-", "")}_api_key_here'''
            elif tool.startswith("mcp_"):
                env_content += f'''
{tool.upper()}_API_KEY=your_{tool.replace("_", "").replace("-", "")}_api_key_here'''
        
        env_content += '''

# === 云服务配置 ===
# 阿里云DashScope
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# === 应用配置 ===
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
APP_ENV=production
LOG_LEVEL=INFO
USR_AGENT=cooragent_generated_app

# === 安全配置 ===
SECRET_KEY=your_secret_key_here
ANONYMIZED_TELEMETRY=false

# === 数据库配置 (可选) ===
# DATABASE_URL=sqlite:///./data/app.db

# === 缓存配置 (可选) ===
# REDIS_URL=redis://localhost:6379/0

# === 监控配置 (可选) ===
# SENTRY_DSN=your_sentry_dsn_here
'''
        
        async with aiofiles.open(project_path / ".env.example", "w", encoding="utf-8") as f:
            await f.write(env_content)
    
    async def _generate_missing_system_files(self, project_path: Path, agents_config: Dict[str, Any]):
        """生成历史文档中提到的缺失文件"""
        
        # 1. 生成 src/utils/chinese_names.py
        chinese_names_content = '''"""中文名称和日志工具模块"""
import json
from datetime import datetime
from typing import Dict, Any

def generate_chinese_log(log_type: str, message: str, **kwargs) -> Dict[str, Any]:
    """生成中文日志消息"""
    return {
        "timestamp": datetime.now().isoformat(),
        "type": log_type,
        "data": {
            "message": message,
            **kwargs
        }
    }

def get_agent_chinese_name(agent_name: str) -> str:
    """获取智能体的中文名称"""
    chinese_names = {
        "coordinator": "协调员",
        "planner": "规划师", 
        "researcher": "研究员",
        "coder": "程序员",
        "reporter": "报告员",
        "browser": "浏览器操作员",
        "agent_factory": "智能体工厂",
        "publisher": "发布员"
    }
    return chinese_names.get(agent_name, agent_name)

def format_agent_progress_log(agent_name: str, progress: str) -> str:
    """格式化智能体进度日志"""
    return f"[{get_agent_chinese_name(agent_name)}] {progress}"

def format_code_generation_log(stage: str, progress: int, details: Dict[str, Any]) -> str:
    """格式化代码生成日志"""
    return f"{stage} 进度: {progress}% - {details}"

def format_download_log(action: str, details: Dict[str, Any]) -> str:
    """格式化下载日志"""
    return f"下载{action}: {details}"

def get_execution_status_chinese(status: str) -> str:
    """获取执行状态的中文描述"""
    status_map = {
        "pending": "等待中",
        "processing": "处理中", 
        "completed": "已完成",
        "failed": "失败"
    }
    return status_map.get(status, status)
'''
        
        # 2. 生成 src/workflow/coor_task.py
        coor_task_content = '''"""协调任务工作流构建模块"""
import logging
import time
from typing import Dict, Any, List
from langchain.schema import BaseMessage
from langgraph.types import Command
from src.interface.agent import State
from src.workflow.graph import AgentWorkflow

logger = logging.getLogger(__name__)

async def coordinator_node(state: State) -> Command:
    """协调员节点 - 智能分类用户请求"""
    messages = state.get("messages", [])
    if not messages:
        return Command(goto="__end__", update={"messages": []})
    
    # 基础协调逻辑
    user_input = messages[-1].content if messages else ""
    
    # 简单的任务分类
    if len(user_input.split()) > 20:  # 复杂任务
        return Command(goto="planner", update={"task_type": "complex"})
    else:  # 简单任务  
        return Command(goto="agent_proxy", update={"task_type": "simple"})

def build_graph() -> AgentWorkflow:
    """构建协调任务工作流图"""
    workflow = AgentWorkflow()
    workflow.add_node("coordinator", coordinator_node)
    workflow.set_start("coordinator")
    return workflow.compile()
'''
        
        # 3. 生成 src/workflow/agent_factory.py
        agent_factory_content = '''"""智能体工厂工作流构建模块"""
import logging
import time
from typing import Dict, Any
from langgraph.types import Command
from src.interface.agent import State, Agent
from src.workflow.graph import AgentWorkflow

logger = logging.getLogger(__name__)

async def agent_factory_node(state: State) -> Command:
    """智能体工厂节点 - 动态创建智能体"""
    messages = state.get("messages", [])
    task_requirements = state.get("task_requirements", {})
    
    # 基础智能体创建逻辑
    new_agent = {
        "agent_name": f"dynamic_agent_{int(time.time())}",
        "description": "动态创建的智能体",
        "llm_type": "basic",
        "selected_tools": [],
        "prompt": "你是一个智能助手，帮助用户完成任务。"
    }
    
    return Command(
        goto="__end__", 
        update={
            "created_agent": new_agent,
            "messages": messages
        }
    )

def agent_factory_graph() -> AgentWorkflow:
    """构建智能体工厂工作流图"""
    workflow = AgentWorkflow()
    workflow.add_node("agent_factory", agent_factory_node)
    workflow.set_start("agent_factory")
    return workflow.compile()
'''
        
        # 写入文件
        utils_dir = project_path / "src" / "utils"
        workflow_dir = project_path / "src" / "workflow"
        
        async with aiofiles.open(utils_dir / "chinese_names.py", "w", encoding="utf-8") as f:
            await f.write(chinese_names_content)
            
        async with aiofiles.open(workflow_dir / "coor_task.py", "w", encoding="utf-8") as f:
            await f.write(coor_task_content)
            
        async with aiofiles.open(workflow_dir / "agent_factory.py", "w", encoding="utf-8") as f:
            await f.write(agent_factory_content)
        
        logger.info("生成了3个缺失的系统文件: chinese_names.py, coor_task.py, agent_factory.py")
    
    async def _generate_requirements(self, project_path: Path, agents_config: Dict[str, Any]):
        """生成完整的requirements.txt，包含所有历史问题中的依赖"""
        # 基础依赖
        base_requirements = [
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
        
        # LangGraph工作流框架 (关键依赖)
        langgraph_requirements = [
            "langgraph>=0.5.4",
            "langgraph-checkpoint>=2.1.1",
            "langgraph-prebuilt>=0.5.2",
            "langgraph-sdk>=0.1.74"
        ]
        
        # MCP生态系统 (关键依赖)
        mcp_requirements = [
            "langchain-mcp-adapters>=0.1.9",
            "mcp>=1.12.2",
            "httpx-sse>=0.4.1",
            "jsonschema>=4.25.0",
            "pydantic-settings>=2.10.1",
            "sse-starlette>=2.4.1"
        ]
        
        # LangChain生态扩展
        langchain_extended = [
            "langchain-community>=0.3.27",
            "langchain-experimental>=0.3.4",
            "langchain-openai>=0.2.0"
        ]
        
        # 网页处理和爬取
        web_processing = [
            "beautifulsoup4>=4.13.4",
            "lxml>=6.0.0",
            "markdownify>=1.1.0",
            "readabilipy>=0.3.0",
            "html5lib>=1.1",
            "requests>=2.31.0"
        ]
        
        # 搜索和自动化工具
        automation_tools = [
            "tavily-python>=0.7.10",
            "playwright>=1.54.0",
            "selenium>=4.34.2",
            "pyee>=13.0.0"
        ]
        
        # 云服务集成
        cloud_services = [
            "dashscope>=1.19.0"
        ]
        
        # AI和ML工具
        ai_tools = [
            "tiktoken>=0.9.0",
            "numpy>=2.3.2"
        ]
        
        # 异步和网络支持
        async_network = [
            "aiohttp>=3.12.14",
            "websocket-client>=1.8.0",
            "trio>=0.30.0",
            "trio-websocket>=0.12.2"
        ]
        
        # 系统和工具
        system_tools = [
            "distro>=1.9.0",
            "psutil>=5.9.0"
        ]
        
        # 工具特定依赖
        tool_specific_deps = {
            "tavily_tool": ["tavily-python>=0.7.10"],
            "python_repl_tool": ["jupyter>=1.0.0", "ipython>=8.0.0"],
            "crawl_tool": ["beautifulsoup4>=4.13.4", "requests>=2.31.0", "lxml>=6.0.0"],
            "browser_tool": ["playwright>=1.54.0", "selenium>=4.34.2"],
            "excel_tool": ["openpyxl>=3.1.0", "pandas>=2.0.0"],
            "gmail_tool": ["google-api-python-client>=2.100.0"],
            "slack_tool": ["slack-sdk>=3.21.0"],
            "video_tool": ["opencv-python>=4.8.0"],
            "mcp_doc": ["python-docx>=1.1.0"],
            "web_preview_tool": ["jinja2>=3.1.0"]
        }
        
        # 合并所有依赖
        all_requirements = []
        all_requirements.extend(base_requirements)
        all_requirements.extend(langgraph_requirements)
        all_requirements.extend(mcp_requirements)
        all_requirements.extend(langchain_extended)
        all_requirements.extend(web_processing)
        all_requirements.extend(automation_tools)
        all_requirements.extend(cloud_services)
        all_requirements.extend(ai_tools)
        all_requirements.extend(async_network)
        all_requirements.extend(system_tools)
        
        # 添加工具特定依赖
        for tool in agents_config["tools_used"]:
            if tool in tool_specific_deps:
                all_requirements.extend(tool_specific_deps[tool])
        
        # 去重并排序
        final_requirements = sorted(list(set(all_requirements)))
        
        async with aiofiles.open(project_path / "requirements.txt", "w", encoding="utf-8") as f:
            await f.write("\n".join(final_requirements))
        
        logger.info(f"生成了包含 {len(final_requirements)} 个依赖包的 requirements.txt")
    
    async def _generate_independent_main_app(self, project_path: Path, requirements: Dict[str, Any], agents_config: Dict[str, Any]):
        """生成独立的主应用入口文件"""
        from .template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        main_content = await renderer.render_main_app(agents_config)
        
        async with aiofiles.open(project_path / "main.py", "w", encoding="utf-8") as f:
            await f.write(main_content)
    
    async def _generate_deployment_configs(self, project_path: Path, requirements: Dict[str, Any], agents_config: Dict[str, Any]):
        """生成部署文件"""
        from .template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        
        # 生成Dockerfile
        dockerfile_content = await renderer.render_dockerfile(requirements)
        async with aiofiles.open(project_path / "Dockerfile", "w", encoding="utf-8") as f:
            await f.write(dockerfile_content)
        
        # 生成docker-compose.yml
        compose_content = await renderer.render_docker_compose(requirements)
        async with aiofiles.open(project_path / "docker-compose.yml", "w", encoding="utf-8") as f:
            await f.write(compose_content)
    
    async def _generate_comprehensive_documentation(self, project_path: Path, requirements: Dict[str, Any], agents_config: Dict[str, Any]):
        """生成项目文档"""
        from .template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        readme_content = await renderer.render_readme(agents_config)
        
        async with aiofiles.open(project_path / "README.md", "w", encoding="utf-8") as f:
            await f.write(readme_content)
    
    async def _compress_project(self, project_path: Path) -> Path:
        """压缩项目为zip文件"""
        zip_path = project_path.with_suffix('.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    # 计算相对路径
                    arcname = file_path.relative_to(project_path.parent)
                    zipf.write(file_path, arcname)
        
        # 删除原目录（可选）
        shutil.rmtree(project_path)
        
        logger.info(f"项目已压缩为: {zip_path}")
        return zip_path
    
    async def _cleanup_user_agents(self, user_id: str, progress_callback=None):
        """清理临时生成的用户智能体"""
        try:
            if progress_callback:
                await progress_callback("清理临时文件...", 99, "清理", "清理临时生成的智能体配置")
            
            # 从运行时管理器清理
            agents_to_remove = []
            for agent_name, agent in agent_manager.available_agents.items():
                if hasattr(agent, 'user_id') and agent.user_id == user_id:
                    agents_to_remove.append(agent_name)
            
            for agent_name in agents_to_remove:
                if agent_name in agent_manager.available_agents:
                    del agent_manager.available_agents[agent_name]
            
            logger.info(f"清理完成，移除了 {len(agents_to_remove)} 个临时智能体")
            
        except Exception as e:
            logger.warning(f"清理用户智能体时出错: {e}")


# 为了向后兼容，保留原来的类名作为别名
CooragentProjectGenerator = EnhancedCooragentProjectGenerator 