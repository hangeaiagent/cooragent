"""
配置生成器

负责生成项目的各种配置文件
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import aiofiles

from src.interface.agent import Agent


class ConfigGenerator:
    """配置文件生成器"""
    
    async def generate_workflow_config(self, project_path: Path, config: Dict[str, Any]):
        """生成工作流配置"""
        workflow_config = {
            "workflow_id": "custom_app_workflow",
            "mode": "agent_workflow", 
            "version": 1,
            "description": f"基于用户需求生成的工作流: {config['project_info']['user_input'][:100]}...",
            "created_at": config["project_info"]["generated_at"],
            "user_id": config["project_info"]["user_id"],
            "agents": []
        }
        
        # 添加定制智能体配置
        for agent in config["agents"]:
            agent_config = {
                "agent_name": agent.agent_name,
                "description": agent.description,
                "llm_type": agent.llm_type,
                "selected_tools": [tool.name for tool in agent.selected_tools],
                "user_id": getattr(agent, 'user_id', 'share')
            }
            workflow_config["agents"].append(agent_config)
        
        config_dir = project_path / "config"
        config_dir.mkdir(exist_ok=True)
        
        async with aiofiles.open(config_dir / "workflow.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(workflow_config, indent=2, ensure_ascii=False))
    
    async def generate_global_variables(self, project_path: Path, config: Dict[str, Any]):
        """生成全局变量配置"""
        global_vars_content = f'''"""
全局变量配置

自动生成于: {config["project_info"]["generated_at"]}
"""

# 应用信息
APP_NAME = "基于Cooragent的多智能体应用"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "自动生成的智能体协作应用"

# 用户配置
USER_ID = "{config["project_info"]["user_id"]}"
GENERATED_AGENTS = {[agent.agent_name for agent in config["agents"]]}
AVAILABLE_TOOLS = {config["tools"]}

# 存储路径
STORE_DIR = "store"
AGENTS_DIR = "store/agents"
PROMPTS_DIR = "store/prompts" 
WORKFLOWS_DIR = "store/workflows"
LOGS_DIR = "logs"

# 工作流配置
DEFAULT_WORK_MODE = "production"
ENABLE_DEEP_THINKING = True
ENABLE_SEARCH_BEFORE_PLANNING = True

# 性能配置
MAX_CONCURRENT_TASKS = 5
TASK_TIMEOUT = 300  # 5分钟

# 日志配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
'''
        
        config_dir = project_path / "config"
        config_dir.mkdir(exist_ok=True)
        
        async with aiofiles.open(config_dir / "global_variables.py", "w", encoding="utf-8") as f:
            await f.write(global_vars_content)
    
    async def generate_env_config(self, project_path: Path, config: Dict[str, Any]):
        """生成环境配置文件"""
        env_content = '''# 环境配置文件
# 复制此文件为.env并填入实际值

# ================================
# LLM配置 (必需)
# ================================

# 基础LLM配置 (用于一般对话和协调)
BASIC_API_KEY=your_openai_api_key_here
BASIC_BASE_URL=https://api.openai.com/v1
BASIC_MODEL=gpt-4

# 代码生成LLM配置 (用于代码相关任务)
CODE_API_KEY=your_code_llm_api_key_here  
CODE_BASE_URL=https://api.deepseek.com/v1
CODE_MODEL=deepseek-chat

# 推理LLM配置 (用于复杂推理任务)
REASONING_API_KEY=your_reasoning_api_key_here
REASONING_BASE_URL=https://api.openai.com/v1
REASONING_MODEL=o1-preview

# ================================
# 工具API配置 (根据使用的工具配置)
# ================================'''

        # 根据使用的工具添加相应的API配置
        if "tavily_tool" in config["tools"]:
            env_content += '''

# Tavily搜索工具
TAVILY_API_KEY=your_tavily_api_key_here'''
        
        if "serper_tool" in config["tools"]:
            env_content += '''

# Serper搜索工具
SERPER_API_KEY=your_serper_api_key_here'''
        
        if "browser_tool" in config["tools"]:
            env_content += '''

# 浏览器工具配置
USE_BROWSER=true'''
        
        env_content += '''

# ================================
# 应用配置
# ================================

# 服务器配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

# 日志配置
LOG_LEVEL=INFO

# 用户代理
USR_AGENT=True

# ================================
# 可选配置
# ================================

# MCP工具集成 (Model Context Protocol)
USE_MCP_TOOLS=false

# 匿名遥测 (帮助改进Cooragent)
ANONYMIZED_TELEMETRY=false

# 缓存配置
ENABLE_CACHE=true
CACHE_TTL=3600

# 并发配置
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
'''
        
        async with aiofiles.open(project_path / ".env.example", "w", encoding="utf-8") as f:
            await f.write(env_content)
    
    async def generate_requirements(self, project_path: Path, config: Dict[str, Any]):
        """生成requirements.txt"""
        # 基础依赖
        requirements = [
            "# 基础Web框架",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.5.0",
            "python-multipart>=0.0.6",
            "",
            "# 异步IO和文件操作",
            "aiofiles>=23.2.1",
            "httpx>=0.25.0",
            "",
            "# 环境配置",
            "python-dotenv>=1.0.0",
            "",
            "# LangChain生态",
            "langchain>=0.1.0",
            "langchain-core>=0.1.0",
            "langchain-community>=0.0.20",
            "",
            "# UI和日志",
            "rich>=13.0.0",
            "",
            "# 工具依赖"
        ]
        
        # 根据工具添加特定依赖
        tool_deps = {
            "tavily_tool": [
                "# Tavily搜索工具",
                "tavily-python>=0.3.0"
            ],
            "python_repl_tool": [
                "# Python代码执行",
                "jupyter>=1.0.0",
                "ipython>=8.0.0"
            ],
            "crawl_tool": [
                "# 网页爬虫工具", 
                "beautifulsoup4>=4.12.0",
                "requests>=2.31.0",
                "lxml>=4.9.0"
            ],
            "browser_tool": [
                "# 浏览器自动化",
                "playwright>=1.40.0",
                "selenium>=4.15.0"
            ],
            "bash_tool": [
                "# Shell工具 (无额外依赖)"
            ]
        }
        
        for tool in config["tools"]:
            if tool in tool_deps:
                requirements.extend([""] + tool_deps[tool])
        
        # 添加通用工具依赖
        requirements.extend([
            "",
            "# 通用工具",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "matplotlib>=3.7.0",
            "plotly>=5.17.0"
        ])
        
        content = "\n".join(requirements)
        async with aiofiles.open(project_path / "requirements.txt", "w", encoding="utf-8") as f:
            await f.write(content)
    
    async def generate_startup_script(self, project_path: Path, config: Dict[str, Any]):
        """生成启动脚本"""
        
        # 生成启动脚本 (Unix/Linux/macOS)
        startup_script = '''#!/bin/bash

# Cooragent多智能体应用启动脚本

echo "🤖 启动Cooragent多智能体应用..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python，请安装Python 3.12+"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 建议在虚拟环境中运行"
fi

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件，使用默认配置"
    if [ -f ".env.example" ]; then
        echo "💡 提示: 请复制.env.example为.env并配置API密钥"
    fi
fi

# 创建必要目录
mkdir -p store/agents store/prompts store/workflows logs

# 安装依赖
echo "📦 检查并安装依赖..."
pip install -r requirements.txt

# 启动应用
echo "🚀 启动应用服务器..."
echo "📱 Web界面: http://localhost:8000"
echo "📋 API文档: http://localhost:8000/docs"
echo ""

python main.py
'''
        
        async with aiofiles.open(project_path / "start.sh", "w", encoding="utf-8") as f:
            await f.write(startup_script)
        
        # 设置执行权限
        import os
        os.chmod(project_path / "start.sh", 0o755)
        
        # 生成Windows启动脚本
        windows_script = '''@echo off
echo 🤖 启动Cooragent多智能体应用...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请安装Python 3.12+
    pause
    exit /b 1
)

REM 检查环境配置文件
if not exist ".env" (
    echo ⚠️  未找到.env文件，使用默认配置
    if exist ".env.example" (
        echo 💡 提示: 请复制.env.example为.env并配置API密钥
    )
)

REM 创建必要目录
if not exist "store" mkdir store
if not exist "store\\agents" mkdir store\\agents
if not exist "store\\prompts" mkdir store\\prompts
if not exist "store\\workflows" mkdir store\\workflows
if not exist "logs" mkdir logs

REM 安装依赖
echo 📦 检查并安装依赖...
pip install -r requirements.txt

REM 启动应用
echo 🚀 启动应用服务器...
echo 📱 Web界面: http://localhost:8000
echo 📋 API文档: http://localhost:8000/docs
echo.

python main.py
pause
'''
        
        async with aiofiles.open(project_path / "start.bat", "w", encoding="utf-8") as f:
            await f.write(windows_script)
    
    async def generate_config_init(self, project_path: Path):
        """生成config包的__init__.py"""
        init_content = '''"""
配置模块

包含应用的各种配置文件和全局变量
"""

from .global_variables import *

__all__ = [
    "APP_NAME",
    "APP_VERSION", 
    "APP_DESCRIPTION",
    "USER_ID",
    "GENERATED_AGENTS",
    "AVAILABLE_TOOLS",
    "STORE_DIR",
    "AGENTS_DIR",
    "PROMPTS_DIR",
    "WORKFLOWS_DIR",
    "LOGS_DIR"
]
'''
        
        config_dir = project_path / "config"
        async with aiofiles.open(config_dir / "__init__.py", "w", encoding="utf-8") as f:
            await f.write(init_content) 