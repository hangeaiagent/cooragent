"""
基于Cooragent的多智能体应用
自动生成于: 2025-07-23 16:04:55

用户需求: workflow completed...
生成的智能体: researcher, coder, reporter
使用的工具: crawl_tool, bash_tool, python_repl_tool, tavily_tool
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
    logger.info(f"应用启动完成，可用智能体: {list(agent_manager.available_agents.keys())}")

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
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                max-width: 800px;
                width: 90%;
            }
            .title {
                font-size: 2.5em;
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }
            .description {
                color: #666;
                margin-bottom: 30px;
                text-align: center;
                font-size: 1.1em;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
            }
            .form-control {
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            .form-control:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea.form-control {
                min-height: 120px;
                resize: vertical;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s;
                font-weight: 600;
            }
            .btn:hover:not(:disabled) {
                transform: translateY(-2px);
            }
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 8px;
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                display: none;
            }
            .agents-info {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .agents-info h3 {
                margin-bottom: 15px;
                color: #333;
            }
            .agent-list {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }
            .agent-tag {
                background: #667eea;
                color: white;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 0.9em;
            }
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
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
                    <span class="agent-tag">researcher</span> <span class="agent-tag">coder</span> <span class="agent-tag">reporter</span>
                </div>
                <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                    这些智能体将根据您的任务需求智能协作，自动分工完成复杂任务。
                </p>
            </div>
        </div>

        <script>
            document.getElementById('taskForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const content = document.getElementById('taskContent').value.trim();
                const userId = document.getElementById('userId').value.trim() || 'app_user';
                const submitBtn = document.getElementById('submitBtn');
                const result = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                
                if (!content) {
                    alert('请输入任务描述');
                    return;
                }
                
                // 显示加载状态
                submitBtn.innerHTML = '<span class="loading"></span>执行中...';
                submitBtn.disabled = true;
                result.style.display = 'none';
                
                try {
                    const response = await fetch('/api/task', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            content: content,
                            user_id: userId
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultContent.innerHTML = `
                            <div style="margin-bottom: 15px;">
                                <strong>状态:</strong> <span style="color: green;">✅ 任务完成</span><br>
                                <strong>执行时间:</strong> ${data.execution_time.toFixed(2)}秒<br>
                                <strong>参与智能体:</strong> ${data.agents_used.join(', ')}
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; white-space: pre-wrap;">
                                ${data.result.execution_summary}
                            </div>
                        `;
                        result.style.display = 'block';
                    } else {
                        throw new Error(data.detail || '任务执行失败');
                    }
                } catch (error) {
                    resultContent.innerHTML = `
                        <div style="color: red;">
                            <strong>❌ 执行失败:</strong> ${error.message}
                        </div>
                    `;
                    result.style.display = 'block';
                } finally {
                    submitBtn.innerHTML = '🚀 开始执行任务';
                    submitBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/info", response_model=AppInfo)
async def get_app_info():
    """获取应用信息"""
    available_agents = list(agent_manager.available_agents.keys())
    custom_agents = ['researcher', 'coder', 'reporter']
    
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
        logger.info(f"接收到任务: {request.content[:100]}...")
        
        # 使用Cooragent工作流执行任务
        final_state = await run_agent_workflow(
            user_id=request.user_id,
            task_type=TaskType.AGENT_WORKFLOW,
            user_input_messages=[{"role": "user", "content": request.content}],
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
        
        result = {
            "task": request.content,
            "final_state": final_state,
            "execution_summary": execution_summary
        }
        
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
            agents_used=list(set(agents_used)) if agents_used else ['researcher', 'coder', 'reporter'],
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"任务执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """列出所有可用智能体"""
    agents_info = []
    for name, agent in agent_manager.available_agents.items():
        agents_info.append({
            "name": agent.agent_name,
            "description": agent.description,
            "llm_type": agent.llm_type,
            "tools": [tool.name for tool in agent.selected_tools],
            "user_id": getattr(agent, 'user_id', 'share'),
            "is_custom": getattr(agent, 'user_id', 'share') != 'share'
        })
    
    return {"agents": agents_info}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_count": len(agent_manager.available_agents),
        "tools_count": len(agent_manager.available_tools)
    }

def main():
    """应用入口"""
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"启动应用: http://{host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if not debug else "debug",
        reload=debug
    )

if __name__ == "__main__":
    main()
