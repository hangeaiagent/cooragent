"""
模板渲染器

负责渲染生成项目所需的各种模板文件
"""

from datetime import datetime
from typing import Dict, Any, List
from src.interface.agent import Agent


class TemplateRenderer:
    """模板渲染器，生成各种项目文件"""
    
    async def render_main_app(self, agents_config: Dict[str, Any]) -> str:
        """渲染主应用入口文件"""
        agents = agents_config["agents"]
        agent_names = [agent.agent_name for agent in agents]
        tools_used = agents_config["tools_used"]
        
        return f'''"""
基于Cooragent的多智能体应用
自动生成于: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

生成的智能体: {", ".join(agent_names)}
使用的工具: {", ".join(tools_used)}
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn

# 导入Cooragent核心组件
from src.workflow.process import run_agent_workflow
from src.manager import agent_manager
from src.interface.agent import TaskType
from src.utils.path_utils import get_project_root
from src.service.env import load_env

# 加载环境变量
load_env()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class TaskRequest(BaseModel):
    content: str
    user_id: str = "app_user"
    mode: str = "production"

class TaskResponse(BaseModel):
    status: str
    result: Dict[str, Any]
    agents_used: list[str]
    execution_time: float

class AppInfo(BaseModel):
    name: str
    version: str
    description: str
    available_agents: list[str]
    custom_agents: list[str]
    based_on: str

# 创建FastAPI应用
app = FastAPI(
    title="定制化多智能体应用",
    description="基于Cooragent生成的专业多智能体协作应用",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("初始化智能体管理器...")
    
    # 确保存储目录存在
    store_dirs = ["store/agents", "store/prompts", "store/workflows"]
    for dir_path in store_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    await agent_manager.initialize()
    logger.info(f"应用启动完成，可用智能体: {{list(agent_manager.available_agents.keys())}}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 显示简单的Web界面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>多智能体协作应用</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                max-width: 800px;
                width: 90%;
            }}
            .title {{
                font-size: 2.5em;
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }}
            .description {{
                color: #666;
                margin-bottom: 30px;
                text-align: center;
                font-size: 1.1em;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
            }}
            .form-control {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }}
            .form-control:focus {{
                outline: none;
                border-color: #667eea;
            }}
            textarea.form-control {{
                min-height: 120px;
                resize: vertical;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s;
                font-weight: 600;
            }}
            .btn:hover:not(:disabled) {{
                transform: translateY(-2px);
            }}
            .btn:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
            }}
            .result {{
                margin-top: 30px;
                padding: 20px;
                border-radius: 8px;
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                display: none;
            }}
            .agents-info {{
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .agents-info h3 {{
                margin-bottom: 15px;
                color: #333;
            }}
            .agent-list {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .agent-tag {{
                background: #667eea;
                color: white;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 0.9em;
            }}
            .loading {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title">🤖 多智能体协作应用</h1>
            <p class="description">基于Cooragent架构的智能体协作平台，输入您的任务需求，智能体将协作完成。</p>
            
            <form id="taskForm">
                <div class="form-group">
                    <label for="taskContent">任务描述</label>
                    <textarea 
                        id="taskContent" 
                        class="form-control" 
                        placeholder="请详细描述您需要完成的任务，例如：分析最新的AI发展趋势，搜集相关资料并生成一份详细报告..."
                        required
                    ></textarea>
                </div>
                
                <div class="form-group">
                    <label for="userId">用户ID（可选）</label>
                    <input 
                        type="text" 
                        id="userId" 
                        class="form-control" 
                        placeholder="默认为 app_user"
                        value="app_user"
                    >
                </div>
                
                <button type="submit" class="btn" id="submitBtn">
                    🚀 开始执行任务
                </button>
            </form>
            
            <div id="result" class="result">
                <h3>执行结果</h3>
                <div id="resultContent"></div>
            </div>
            
            <div class="agents-info">
                <h3>🎯 可用智能体</h3>
                <div class="agent-list">
                    {' '.join([f'<span class="agent-tag">{name}</span>' for name in agent_names])}
                </div>
                <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                    这些智能体将根据您的任务需求智能协作，自动分工完成复杂任务。
                </p>
            </div>
        </div>

        <script>
            document.getElementById('taskForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const content = document.getElementById('taskContent').value.trim();
                const userId = document.getElementById('userId').value.trim() || 'app_user';
                const submitBtn = document.getElementById('submitBtn');
                const result = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                
                if (!content) {{
                    alert('请输入任务描述');
                    return;
                }}
                
                // 显示加载状态
                submitBtn.innerHTML = '<span class="loading"></span>执行中...';
                submitBtn.disabled = true;
                result.style.display = 'none';
                
                try {{
                    const response = await fetch('/api/task', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            content: content,
                            user_id: userId
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultContent.innerHTML = `
                            <div style="margin-bottom: 15px;">
                                <strong>状态:</strong> <span style="color: green;">✅ 任务完成</span><br>
                                <strong>执行时间:</strong> ${{data.execution_time.toFixed(2)}}秒<br>
                                <strong>参与智能体:</strong> ${{data.agents_used.join(', ')}}
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; white-space: pre-wrap;">
                                ${{data.result.execution_summary}}
                            </div>
                        `;
                        result.style.display = 'block';
                    }} else {{
                        throw new Error(data.detail || '任务执行失败');
                    }}
                }} catch (error) {{
                    resultContent.innerHTML = `
                        <div style="color: red;">
                            <strong>❌ 执行失败:</strong> ${{error.message}}
                        </div>
                    `;
                    result.style.display = 'block';
                }} finally {{
                    submitBtn.innerHTML = '🚀 开始执行任务';
                    submitBtn.disabled = false;
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/info", response_model=AppInfo)
async def get_app_info():
    """获取应用信息"""
    available_agents = list(agent_manager.available_agents.keys())
    custom_agents = {agent_names}
    
    return AppInfo(
        name="定制化多智能体应用",
        version="1.0.0",
        description="基于Cooragent架构的智能体协作应用",
        available_agents=available_agents,
        custom_agents=custom_agents,
        based_on="Cooragent"
    )

@app.post("/api/task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """执行智能体任务"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info(f"接收到任务: {{request.content[:100]}}...")
        
        # 使用Cooragent工作流执行任务
        final_state = await run_agent_workflow(
            user_id=request.user_id,
            task_type=TaskType.AGENT_WORKFLOW,
            user_input_messages=[{{"role": "user", "content": request.content}}],
            debug=False,
            deep_thinking_mode=True,
            search_before_planning=True,
            workmode=request.mode
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # 提取执行结果
        messages = final_state.get("messages", [])
        execution_summary = "任务执行完成"
        
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                execution_summary = last_message.get("content", "任务执行完成")
            elif hasattr(last_message, 'content'):
                execution_summary = last_message.content
        
        result = {{
            "task": request.content,
            "final_state": final_state,
            "execution_summary": execution_summary
        }}
        
        # 获取使用的智能体列表
        agents_used = []
        for message in messages:
            if isinstance(message, dict):
                if message.get("tool"):
                    agents_used.append(message["tool"])
                elif message.get("name"):
                    agents_used.append(message["name"])
        
        return TaskResponse(
            status="success",
            result=result,
            agents_used=list(set(agents_used)) if agents_used else {agent_names},
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"任务执行失败: {{str(e)}}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """列出所有可用智能体"""
    agents_info = []
    for name, agent in agent_manager.available_agents.items():
        agents_info.append({{
            "name": agent.agent_name,
            "description": agent.description,
            "llm_type": agent.llm_type,
            "tools": [tool.name for tool in agent.selected_tools],
            "user_id": getattr(agent, 'user_id', 'share'),
            "is_custom": getattr(agent, 'user_id', 'share') != 'share'
        }})
    
    return {{"agents": agents_info}}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {{
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_count": len(agent_manager.available_agents),
        "tools_count": len(agent_manager.available_tools)
    }}

def main():
    """应用入口"""
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"启动应用: http://{{host}}:{{port}}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if not debug else "debug",
        reload=debug
    )

if __name__ == "__main__":
    main()
'''
    
    async def render_dockerfile(self, requirements: Dict[str, Any]) -> str:
        """渲染Dockerfile"""
        tools_used = list(requirements.get("tool_components", {}).keys())
        
        # 根据工具确定是否需要额外的系统依赖
        system_deps = []
        if "browser_tool" in tools_used:
            system_deps.extend([
                "wget",
                "gnupg", 
                "software-properties-common"
            ])
        
        system_deps_install = ""
        if system_deps:
            system_deps_install = f"""
# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    {' '.join(system_deps)} \\
    && rm -rf /var/lib/apt/lists/*"""
        
        playwright_install = ""
        if "browser_tool" in tools_used:
            playwright_install = """
# 安装Playwright浏览器
RUN pip install playwright && playwright install chromium"""
        
        return f'''FROM python:3.12-slim

WORKDIR /app
{system_deps_install}

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
{playwright_install}

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p store/agents store/prompts store/workflows logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["python", "main.py"]
'''
    
    async def render_docker_compose(self, requirements: Dict[str, Any]) -> str:
        """渲染docker-compose.yml"""
        return '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./store:/app/store
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  store:
  logs:
'''
    
    async def render_readme(self, agents_config: Dict[str, Any]) -> str:
        """渲染README.md"""
        agents = agents_config["agents"]
        agent_names = [agent.agent_name for agent in agents]
        tools_used = agents_config["tools_used"]
        
        return f'''# 多智能体协作应用

基于 [Cooragent](https://github.com/LeapLabTHU/cooragent) 架构的定制化多智能体应用

## 项目信息

- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **生成的智能体**: {", ".join(agent_names)}
- **使用的工具**: {", ".join(tools_used)}

## 快速开始

### 方式一：直接运行

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入您的API密钥
   ```

3. **启动应用**
   ```bash
   python main.py
   ```

4. **访问应用**
   
   打开浏览器访问: http://localhost:8000

### 方式二：Docker部署

1. **构建镜像**
   ```bash
   docker-compose build
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **查看日志**
   ```bash
   docker-compose logs -f
   ```

## 环境变量配置

将 `.env.example` 复制为 `.env` 并配置以下环境变量:

### 必需配置

```bash
# 基础LLM配置
BASIC_API_KEY=your_openai_api_key_here
BASIC_BASE_URL=https://api.openai.com/v1
BASIC_MODEL=gpt-4

# 代码生成LLM配置  
CODE_API_KEY=your_code_llm_api_key_here
CODE_BASE_URL=https://api.deepseek.com/v1
CODE_MODEL=deepseek-chat

# 推理LLM配置
REASONING_API_KEY=your_reasoning_api_key_here  
REASONING_BASE_URL=https://api.openai.com/v1
REASONING_MODEL=o1-preview
```

### 工具相关配置

根据您的应用使用的工具，配置相应的API密钥:

```bash
# 搜索工具 (如果使用 tavily_tool)
TAVILY_API_KEY=your_tavily_api_key_here

# 浏览器工具 (如果使用 browser_tool)  
USE_BROWSER=true
```

## API接口

### 执行任务

```bash
POST /api/task
Content-Type: application/json

{{
  "content": "您的任务描述",
  "user_id": "用户ID（可选）",
  "mode": "production"
}}
```

### 获取智能体列表

```bash
GET /api/agents
```

### 健康检查

```bash
GET /health
```

## 智能体介绍

本应用包含以下智能体:

{self._format_agents_description(agents)}

## 工具能力

本应用集成了以下工具:

{self._format_tools_description(tools_used)}

## 项目结构

```
.
├── src/                    # 核心源码
│   ├── interface/         # 接口定义
│   ├── workflow/          # 工作流引擎
│   ├── manager/           # 智能体管理
│   ├── llm/              # LLM集成
│   ├── tools/            # 工具集合
│   ├── prompts/          # 提示词管理
│   ├── utils/            # 工具函数
│   └── service/          # 服务层
├── config/               # 配置文件
├── store/               # 数据存储
│   ├── agents/         # 智能体定义
│   ├── prompts/        # 提示词
│   └── workflows/      # 工作流缓存
├── static/             # 静态文件
├── logs/               # 日志文件
├── main.py             # 应用入口
├── requirements.txt    # 依赖清单
├── .env.example       # 环境变量模板
├── Dockerfile         # Docker配置
└── docker-compose.yml # Docker Compose配置
```

## 使用示例

### Web界面使用

1. 访问 http://localhost:8000
2. 在任务描述框中输入您的需求
3. 点击"开始执行任务"
4. 等待智能体协作完成任务

### API调用示例

```python
import requests

# 执行任务
response = requests.post("http://localhost:8000/api/task", json={{
    "content": "分析最新的AI发展趋势，生成一份详细报告",
    "user_id": "demo_user"
}})

result = response.json()
print(result["result"]["execution_summary"])
```

## 技术特性

- ✅ **基于Cooragent**: 采用成熟的多智能体协作架构
- ✅ **智能协作**: 智能体自动分工协作完成复杂任务  
- ✅ **工具集成**: 支持搜索、代码执行、浏览器操作等多种工具
- ✅ **Web界面**: 提供友好的Web交互界面
- ✅ **API接口**: 支持程序化调用
- ✅ **Docker部署**: 支持容器化部署
- ✅ **可扩展**: 基于Cooragent生态，易于扩展新功能

## 故障排除

### 常见问题

1. **启动失败**: 检查环境变量配置，确保API密钥正确
2. **任务执行失败**: 查看日志文件 `logs/` 目录
3. **网络问题**: 确保API服务可访问，检查网络连接

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker日志
docker-compose logs -f app
```

## 许可证

本项目基于 Cooragent 项目生成，遵循相同的许可证条款。

## 支持

如有问题或建议，请参考 [Cooragent 官方文档](https://github.com/LeapLabTHU/cooragent)。
'''
    
    def _format_agents_description(self, agents: List[Agent]) -> str:
        """格式化智能体描述"""
        descriptions = []
        for agent in agents:
            tools_list = ", ".join([tool.name for tool in agent.selected_tools])
            descriptions.append(f"""
### {agent.agent_name}

- **描述**: {agent.description}
- **LLM类型**: {agent.llm_type}  
- **工具**: {tools_list}
""")
        return "\n".join(descriptions)
    
    def _format_tools_description(self, tools: List[str]) -> str:
        """格式化工具描述"""
        tool_descriptions = {
            "tavily_tool": "🔍 **搜索工具**: 使用Tavily进行网络搜索，获取最新信息",
            "python_repl_tool": "🐍 **Python执行器**: 执行Python代码，进行数据分析和计算",
            "bash_tool": "⚡ **Shell工具**: 执行系统命令，进行文件操作",
            "crawl_tool": "🕷️ **网页爬虫**: 爬取网页内容，提取结构化信息", 
            "browser_tool": "🌐 **浏览器工具**: 模拟浏览器操作，处理动态网页"
        }
        
        descriptions = []
        for tool in tools:
            if tool in tool_descriptions:
                descriptions.append(tool_descriptions[tool])
        
        return "\n".join(descriptions) if descriptions else "- 本应用使用基础工具集" 