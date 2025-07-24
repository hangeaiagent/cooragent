"""
代码生成器API扩展

扩展Cooragent现有的Server功能，添加项目代码生成接口
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 导入现有Cooragent组件
from src.service.server import Server
from src.generator.cooragent_generator import CooragentProjectGenerator
from src.utils.path_utils import get_project_root

logger = logging.getLogger(__name__)

# API模型定义
class GenerateRequest(BaseModel):
    content: str
    user_id: Optional[str] = None
    
class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str
    created_at: datetime

class GenerationStatus(BaseModel):
    task_id: str
    status: str  # processing, completed, failed
    message: str
    progress: int = 0
    zip_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    current_step: Optional[str] = None  # 当前执行的步骤
    total_steps: int = 5  # 总步骤数
    step_details: Optional[str] = None  # 步骤详细信息
    agents_created: list[str] = []  # 已创建的智能体
    tools_selected: list[str] = []  # 已选择的工具

class ExampleResponse(BaseModel):
    examples: list[Dict[str, str]]

# 扩展现有Cooragent Server
class GeneratorServer:
    """扩展的代码生成服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.generator = CooragentProjectGenerator()
        self.generation_tasks: Dict[str, GenerationStatus] = {}
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title="Cooragent代码生成器",
            description="基于Cooragent架构的多智能体项目代码生成器",
            version="1.0.0"
        )
        
        # 配置中间件
        self._setup_middleware()
        
        # 添加路由
        self._setup_routes()
        
        # 启动后台清理任务
        self._setup_background_tasks()
    
    def _setup_middleware(self):
        """设置中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_generator_page():
            """代码生成器主页"""
            return await self._render_generator_page()
        
        @self.app.post("/api/generate", response_model=GenerateResponse)
        async def generate_code(request: GenerateRequest, background_tasks: BackgroundTasks):
            """生成基于Cooragent的项目代码"""
            task_id = str(uuid.uuid4())
            user_id = request.user_id or f"user_{task_id[:8]}"
            
            logger.info(f"收到代码生成请求: {request.content[:100]}...")
            
            # 启动后台任务
            background_tasks.add_task(self._run_code_generation, task_id, request.content, user_id)
            
            # 记录任务状态
            self.generation_tasks[task_id] = GenerationStatus(
                task_id=task_id,
                status="processing",
                message="正在分析需求并启动Cooragent工作流...",
                created_at=datetime.now()
            )
            
            return GenerateResponse(
                task_id=task_id,
                status="processing",
                message="代码生成已开始，基于Cooragent架构",
                created_at=datetime.now()
            )
        
        @self.app.get("/api/generate/{task_id}/status", response_model=GenerationStatus)
        async def get_generation_status(task_id: str):
            """获取生成状态"""
            if task_id not in self.generation_tasks:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            return self.generation_tasks[task_id]
        
        @self.app.get("/api/generate/{task_id}/download")
        async def download_code(task_id: str):
            """下载生成的代码"""
            if task_id not in self.generation_tasks:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            task = self.generation_tasks[task_id]
            if task.status != "completed":
                raise HTTPException(status_code=400, detail="代码还未生成完成")
            
            if not task.zip_path or not Path(task.zip_path).exists():
                raise HTTPException(status_code=404, detail="生成的文件不存在")
            
            return FileResponse(
                path=task.zip_path,
                filename=f"cooragent_app_{task_id[:8]}.zip",
                media_type="application/zip"
            )
        
        @self.app.get("/api/generate/examples", response_model=ExampleResponse)
        async def get_examples():
            """获取需求示例"""
            examples = [
                {
                    "title": "股票分析系统",
                    "description": "创建一个股票分析专家智能体，查看小米股票走势，分析相关新闻，预测股价趋势并给出投资建议",
                    "category": "finance"
                },
                {
                    "title": "新闻情感分析",
                    "description": "构建一个新闻分析系统，能够搜索最新科技新闻、分析情感倾向并生成摘要报告",
                    "category": "nlp"
                },
                {
                    "title": "数据分析助手",
                    "description": "开发一个数据分析工具，支持Python数据处理、统计分析和可视化图表生成",
                    "category": "data"
                },
                {
                    "title": "智能研究助手", 
                    "description": "构建一个研究助手系统，能够搜索学术资料、整理信息并生成研究报告",
                    "category": "research"
                },
                {
                    "title": "旅游规划系统",
                    "description": "创建一个旅游规划助手，搜索景点信息，制定旅行计划，生成详细的旅游攻略",
                    "category": "travel"
                },
                {
                    "title": "内容创作平台",
                    "description": "开发一个内容创作助手，能够搜索资料、生成文章、优化内容并提供SEO建议",
                    "category": "content"
                }
            ]
            return ExampleResponse(examples=examples)
        
        @self.app.get("/api/tasks")
        async def list_generation_tasks():
            """列出所有生成任务"""
            tasks = []
            for task_id, task in self.generation_tasks.items():
                tasks.append({
                    "task_id": task_id,
                    "status": task.status,
                    "message": task.message,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                })
            
            return {"tasks": tasks, "total": len(tasks)}
        
        @self.app.delete("/api/generate/{task_id}")
        async def delete_generation_task(task_id: str):
            """删除生成任务和相关文件"""
            if task_id not in self.generation_tasks:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            task = self.generation_tasks[task_id]
            
            # 删除生成的文件
            if task.zip_path and Path(task.zip_path).exists():
                try:
                    Path(task.zip_path).unlink()
                    logger.info(f"已删除文件: {task.zip_path}")
                except Exception as e:
                    logger.warning(f"删除文件失败: {e}")
            
            # 删除任务记录
            del self.generation_tasks[task_id]
            
            return {"message": f"任务 {task_id} 已删除"}
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "Cooragent代码生成器",
                "version": "1.0.0",
                "active_tasks": len([t for t in self.generation_tasks.values() if t.status == "processing"]),
                "total_tasks": len(self.generation_tasks)
            }
    
    async def _run_code_generation(self, task_id: str, content: str, user_id: str):
        """运行代码生成任务"""
        task = self.generation_tasks[task_id]
        
        # 定义进度更新回调函数
        async def update_progress(message: str, progress: int, current_step: str, step_details: str):
            task.message = message
            task.progress = progress
            task.current_step = current_step
            task.step_details = step_details
            logger.info(f"[{task_id}] {current_step}: {message}")
        
        try:
            logger.info(f"开始生成项目 {task_id}: {content[:100]}...")
            
            # 初始状态
            task.status = "processing"
            await update_progress("正在初始化代码生成器...", 5, "初始化", "准备Cooragent环境和配置")
            
            # 调用Cooragent代码生成器，传入进度回调
            zip_path = await self.generator.generate_project(content, user_id, update_progress)
            
            # 更新状态：生成完成
            task.status = "completed"
            task.message = "🎉 基于Cooragent的多智能体项目生成完成！"
            task.progress = 100
            task.zip_path = str(zip_path)
            task.completed_at = datetime.now()
            task.current_step = "完成"
            task.step_details = f"项目已打包为: {zip_path.name if hasattr(zip_path, 'name') else 'project.zip'}"
            
            logger.info(f"项目生成完成 {task_id}: {zip_path}")
            
        except Exception as e:
            # 更新状态：生成失败
            task.status = "failed"
            task.message = f"❌ 生成失败: {str(e)}"
            task.progress = 0
            task.error_details = str(e)
            task.completed_at = datetime.now()
            task.current_step = "错误"
            task.step_details = f"详细错误信息: {str(e)}"
            
            logger.error(f"代码生成失败 {task_id}: {e}", exc_info=True)
    
    def _setup_background_tasks(self):
        """设置后台任务"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """应用启动事件"""
            logger.info("Cooragent代码生成器启动完成")
            
            # 启动定时清理任务
            asyncio.create_task(self._periodic_cleanup())
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """应用关闭事件"""
            logger.info("Cooragent代码生成器正在关闭...")
    
    async def _periodic_cleanup(self):
        """定期清理过期的任务和文件"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                
                current_time = datetime.now()
                expired_tasks = []
                
                for task_id, task in self.generation_tasks.items():
                    # 删除24小时前的任务
                    if current_time - task.created_at > timedelta(hours=24):
                        expired_tasks.append(task_id)
                
                for task_id in expired_tasks:
                    try:
                        task = self.generation_tasks[task_id]
                        
                        # 删除文件
                        if task.zip_path and Path(task.zip_path).exists():
                            Path(task.zip_path).unlink()
                        
                        # 删除任务记录
                        del self.generation_tasks[task_id]
                        
                        logger.info(f"已清理过期任务: {task_id}")
                        
                    except Exception as e:
                        logger.warning(f"清理任务失败 {task_id}: {e}")
                
                if expired_tasks:
                    logger.info(f"清理了 {len(expired_tasks)} 个过期任务")
                    
            except Exception as e:
                logger.error(f"定期清理任务出错: {e}")
    
    async def _render_generator_page(self) -> str:
        """渲染代码生成器主页"""
        # 这里可以返回一个简单的HTML页面或者从模板文件加载
        html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cooragent 代码生成器</title>
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
            text-align: center;
        }
        
        .header {
            margin-bottom: 30px;
        }
        
        .title {
            font-size: 2.5em;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 20px;
            font-size: 1.1em;
        }
        
        .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            display: inline-block;
        }
        
        .input-area {
            margin: 30px 0;
        }
        
        .input-box {
            width: 100%;
            min-height: 120px;
            padding: 20px;
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            font-size: 16px;
            resize: vertical;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        
        .input-box:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .generate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 30px;
            cursor: pointer;
            transition: transform 0.2s;
            font-weight: 600;
            margin: 10px;
        }
        
        .generate-btn:hover:not(:disabled) {
            transform: translateY(-2px);
        }
        
        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            margin-top: 30px;
            padding: 20px;
            border-radius: 15px;
            display: none;
        }
        
        .status.processing {
            background: #fff3cd;
            border: 2px solid #ffeaa7;
            color: #856404;
        }
        
        .status.completed {
            background: #d4edda;
            border: 2px solid #c3e6cb;
            color: #155724;
        }
        
        .status.failed {
            background: #f8d7da;
            border: 2px solid #f5c6cb;
            color: #721c24;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            margin: 15px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.3s;
            width: 0%;
        }
        
        .download-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            margin-top: 15px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-weight: 600;
        }
        
        .download-btn:hover {
            background: #218838;
            transform: translateY(-1px);
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
        
        .examples {
            margin-top: 30px;
            text-align: left;
        }
        
        .examples h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .example-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .example-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 4px solid #667eea;
        }
        
        .example-item:hover {
            background: #e9ecef;
            transform: translateY(-2px);
        }
        
        .example-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .example-desc {
            font-size: 0.9em;
            color: #666;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🤖 Cooragent 代码生成器</h1>
            <p class="subtitle">一句话描述需求，自动生成完整的多智能体应用代码</p>
            <span class="badge">基于 Cooragent 架构</span>
        </div>
        
        <div class="input-area">
            <textarea 
                id="userInput" 
                class="input-box" 
                placeholder="请详细描述您的需求，例如：创建一个股票分析系统，能够获取实时股票数据、分析技术指标、爬取相关新闻并生成投资建议报告..."
            ></textarea>
        </div>
        
        <button id="generateBtn" class="generate-btn" onclick="generateCode()">
            🚀 生成 Cooragent 应用
        </button>
        
        <div id="status" class="status">
            <div id="statusMessage"></div>
            <div class="progress-bar" id="progressBar" style="display: none;">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>
        
        <div class="examples">
            <h3>💡 需求示例:</h3>
            <div class="example-grid" id="exampleGrid">
                <!-- 示例将通过JavaScript动态加载 -->
            </div>
        </div>
        
        <div class="footer">
            <p>✨ 基于 Cooragent 多智能体协作平台构建</p>
            <p>🔧 生成的应用包含完整的部署配置和文档</p>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let examples = [];
        
        // 页面加载时获取示例
        window.onload = async function() {
            await loadExamples();
        };
        
        async function loadExamples() {
            try {
                const response = await fetch('/api/generate/examples');
                const data = await response.json();
                examples = data.examples;
                renderExamples();
            } catch (error) {
                console.error('加载示例失败:', error);
            }
        }
        
        function renderExamples() {
            const grid = document.getElementById('exampleGrid');
            grid.innerHTML = '';
            
            examples.forEach(example => {
                const item = document.createElement('div');
                item.className = 'example-item';
                item.onclick = () => setExample(example.description);
                item.innerHTML = `
                    <div class="example-title">${example.title}</div>
                    <div class="example-desc">${example.description}</div>
                `;
                grid.appendChild(item);
            });
        }
        
        function setExample(description) {
            document.getElementById('userInput').value = description;
        }
        
        async function generateCode() {
            const input = document.getElementById('userInput').value.trim();
            if (!input) {
                alert('请输入您的需求描述');
                return;
            }
            
            const btn = document.getElementById('generateBtn');
            const status = document.getElementById('status');
            
            // 禁用按钮
            btn.disabled = true;
            btn.innerHTML = '<span class="loading"></span>正在启动 Cooragent...';
            
            try {
                // 发起生成请求
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: input })
                });
                
                const result = await response.json();
                currentTaskId = result.task_id;
                
                // 显示状态
                showStatus('processing', '🔄 正在调用 Cooragent 工作流分析需求...');
                
                // 开始轮询状态
                pollStatus();
                
            } catch (error) {
                showStatus('failed', '❌ 生成失败: ' + error.message);
                resetButton();
            }
        }
        
        async function pollStatus() {
            if (!currentTaskId) return;
            
            try {
                const response = await fetch(`/api/generate/${currentTaskId}/status`);
                const status = await response.json();
                
                // 更新进度条
                updateProgress(status.progress);
                
                // 更新详细状态信息
                updateDetailedStatus(status);
                
                if (status.status === 'completed') {
                    showStatus('completed', 
                        '✅ 基于 Cooragent 的项目代码生成完成！<br>' +
                        '📦 包含完整的多智能体架构和部署配置<br>' +
                        `<a href="/api/generate/${currentTaskId}/download" class="download-btn">📥 下载完整项目</a>`
                    );
                    resetButton();
                } else if (status.status === 'failed') {
                    showStatus('failed', '❌ 生成失败: ' + status.message + 
                        (status.error_details ? '<br><small>' + status.error_details + '</small>' : ''));
                    resetButton();
                } else {
                    // 更新消息并继续轮询
                    setTimeout(pollStatus, 2000);
                }
                
            } catch (error) {
                showStatus('failed', '❌ 状态查询失败: ' + error.message);
                resetButton();
            }
        }
        
        function showStatus(type, message) {
            const status = document.getElementById('status');
            const messageEl = document.getElementById('statusMessage');
            const progressBar = document.getElementById('progressBar');
            
            status.className = 'status ' + type;
            messageEl.innerHTML = message;
            status.style.display = 'block';
            
            if (type === 'processing') {
                progressBar.style.display = 'block';
            } else {
                progressBar.style.display = 'none';
            }
        }
        
        function updateProgress(progress) {
            const progressFill = document.getElementById('progressFill');
            progressFill.style.width = progress + '%';
        }

        function updateDetailedStatus(status) {
            const messageEl = document.getElementById('statusMessage');
            let statusHtml = '';
            
            // 主要状态消息
            statusHtml += `<div style="font-weight: 600; margin-bottom: 10px;">${status.message}</div>`;
            
            // 当前步骤信息
            if (status.current_step) {
                statusHtml += `<div style="margin-bottom: 8px;">
                    <span style="color: #667eea; font-weight: 500;">🔄 当前步骤:</span> ${status.current_step}
                </div>`;
            }
            
            // 步骤详细信息
            if (status.step_details) {
                statusHtml += `<div style="margin-bottom: 8px; color: #666; font-size: 0.9em;">
                    💡 ${status.step_details}
                </div>`;
            }
            
            // 进度信息
            statusHtml += `<div style="margin-bottom: 8px; color: #555; font-size: 0.9em;">
                📊 进度: ${status.progress}% (步骤 ${Math.ceil(status.progress / 20)} / ${status.total_steps})
            </div>`;
            
            // 智能体和工具信息
            if (status.agents_created && status.agents_created.length > 0) {
                statusHtml += `<div style="margin-bottom: 8px; color: #555; font-size: 0.9em;">
                    🤖 已创建智能体: ${status.agents_created.join(', ')}
                </div>`;
            }
            
            if (status.tools_selected && status.tools_selected.length > 0) {
                statusHtml += `<div style="margin-bottom: 8px; color: #555; font-size: 0.9em;">
                    🛠️ 选择的工具: ${status.tools_selected.join(', ')}
                </div>`;
            }
            
            // 估计剩余时间
            if (status.status === 'processing' && status.progress > 0) {
                const elapsed = new Date() - new Date(status.created_at);
                const estimated = (elapsed / status.progress) * (100 - status.progress);
                const remainingMinutes = Math.ceil(estimated / 60000);
                if (remainingMinutes > 0 && remainingMinutes < 10) {
                    statusHtml += `<div style="color: #888; font-size: 0.8em;">
                        ⏱️ 预计剩余时间: ${remainingMinutes} 分钟
                    </div>`;
                }
            }
            
            messageEl.innerHTML = statusHtml;
        }
        
        function resetButton() {
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.innerHTML = '🚀 生成 Cooragent 应用';
        }
    </script>
</body>
</html>
'''
        return html_content
    
    def run(self):
        """启动服务器"""
        import uvicorn
        logger.info(f"启动Cooragent代码生成器: http://{self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)

# 创建全局应用实例
generator_server = GeneratorServer()
app = generator_server.app 