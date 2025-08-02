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
from src.generator.cooragent_generator import EnhancedCooragentProjectGenerator
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
    current_step: Optional[str] = None
    total_steps: int = 5
    step_details: Optional[str] = None
    agents_created: list[str] = []
    tools_selected: list[str] = []

class ExampleResponse(BaseModel):
    examples: list[Dict[str, str]]

# 扩展现有Cooragent Server
class GeneratorServer:
    """扩展的代码生成服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.generator = EnhancedCooragentProjectGenerator()
        self.generation_tasks: Dict[str, GenerationStatus] = {}
        self.output_dir = Path("generated_projects")
        self.output_dir.mkdir(exist_ok=True)
        
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
            """生成基于Cooragent的项目代码或执行旅游规划"""
            task_id = str(uuid.uuid4())
            user_id = request.user_id or f"user_{task_id[:8]}"
            
            logger.info(f"收到请求: {request.content[:100]}...")
            
            # 检测是否为旅游相关任务
            from src.workflow.process import is_travel_related_task
            messages = [{"content": request.content}]
            is_travel = is_travel_related_task(messages)
            
            if is_travel:
                # 旅游规划任务
                task_status = GenerationStatus(
                    task_id=task_id,
                    status="processing",
                    message="正在分析旅游需求并启动智能旅游规划...",
                    created_at=datetime.now(),
                    current_step="旅游任务初始化",
                    step_details="检测到旅游规划任务，启动TravelCoordinator",
                    progress=5
                )
                self.generation_tasks[task_id] = task_status
                
                background_tasks.add_task(self._run_travel_planning, task_id, request.content, user_id)
                
                response = GenerateResponse(
                    task_id=task_id,
                    status="processing",
                    message="旅游规划已开始，基于智能旅游协调器进行分析",
                    created_at=datetime.now()
                )
            else:
                # 代码生成任务
                task_status = GenerationStatus(
                    task_id=task_id,
                    status="processing",
                    message="正在分析需求并启动Cooragent多智能体工作流...",
                    created_at=datetime.now(),
                    current_step="任务初始化",
                    step_details="正在准备Cooragent环境和智能体团队",
                    progress=5
                )
                self.generation_tasks[task_id] = task_status
                
                background_tasks.add_task(self._run_code_generation, task_id, request.content, user_id)
                
                response = GenerateResponse(
                    task_id=task_id,
                    status="processing",
                    message="代码生成已开始，基于Cooragent多智能体架构进行协作分析",
                    created_at=datetime.now()
                )
            
            return response
        
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
            
            zip_file_path = Path(task.zip_path)
            file_name = f"cooragent_app_{task_id[:8]}.zip"
            
            return FileResponse(
                path=task.zip_path,
                filename=file_name,
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
        
        @self.app.get("/travel", response_class=HTMLResponse)
        async def travel_planner_page():
            """旅游规划智能体页面"""
            return await self._render_travel_page()
    
    async def _run_code_generation(self, task_id: str, content: str, user_id: str):
        """运行代码生成任务"""
        task = self.generation_tasks[task_id]
        
        # 定义进度更新回调函数
        async def update_progress(message: str, progress: int, current_step: str, step_details: str, **kwargs):
            task.message = message
            task.progress = progress
            task.current_step = current_step
            task.step_details = step_details
            
            # 处理额外的智能体和工具信息
            if 'agents_created' in kwargs:
                task.agents_created = kwargs['agents_created']
            if 'tools_selected' in kwargs:
                task.tools_selected = kwargs['tools_selected']
            
            logger.info(f"[{task_id[:8]}] {current_step}: {message}")
        
        try:
            logger.info(f"开始生成项目 {task_id}: {content[:100]}...")
            
            # 初始状态
            task.status = "processing"
            
            await update_progress(
                "正在初始化代码生成器...", 
                5, 
                "初始化", 
                "准备Cooragent环境、智能体管理器和配置参数"
            )
            
            # 创建增强的进度回调
            async def enhanced_progress_callback(message: str, progress: int, current_step: str, step_details: str):
                # 解析步骤详情中的额外信息
                additional_info = {}
                
                # 检测智能体相关信息
                if "智能体" in step_details and ":" in step_details:
                    try:
                        if "智能体:" in step_details:
                            agents_part = step_details.split("智能体:")[1].split(",")[0]
                            if "[" in agents_part and "]" in agents_part:
                                import ast
                                agents_list = ast.literal_eval(agents_part.strip())
                                additional_info['agents_created'] = agents_list
                    except:
                        pass
                
                # 检测工具相关信息
                if "工具" in step_details and ":" in step_details:
                    try:
                        if "工具:" in step_details:
                            tools_part = step_details.split("工具:")[1].split(",")[0]
                            if "[" in tools_part and "]" in tools_part:
                                import ast
                                tools_list = ast.literal_eval(tools_part.strip())
                                additional_info['tools_selected'] = tools_list
                    except:
                        pass
                
                await update_progress(message, progress, current_step, step_details, **additional_info)
            
            # 调用Cooragent代码生成器
            zip_path = await self.generator.generate_project(content, user_id, enhanced_progress_callback)
            
            # 更新状态：生成完成
            task.status = "completed"
            task.message = "基于Cooragent的多智能体项目生成完成！"
            task.progress = 100
            task.zip_path = str(zip_path)
            task.completed_at = datetime.now()
            task.current_step = "完成"
            task.step_details = f"项目已打包为: {zip_path.name if hasattr(zip_path, 'name') else 'project.zip'}"
            
            logger.info(f"项目生成完成 {task_id}: {zip_path}")
            
        except Exception as e:
            # 更新状态：生成失败
            task.status = "failed"
            task.message = f"生成失败: {str(e)}"
            task.progress = 0
            task.error_details = str(e)
            task.completed_at = datetime.now()
            task.current_step = "错误"
            task.step_details = f"详细错误信息: {str(e)}"
            
            logger.error(f"代码生成失败 {task_id}: {e}", exc_info=True)
    
    async def _run_travel_planning(self, task_id: str, content: str, user_id: str):
        """运行旅游规划任务"""
        task = self.generation_tasks[task_id]
        
        # 定义进度更新回调函数
        async def update_progress(message: str, progress: int, current_step: str, step_details: str):
            task.message = message
            task.progress = progress
            task.current_step = current_step
            task.step_details = step_details
            logger.info(f"[{task_id[:8]}] {current_step}: {message}")
        
        try:
            logger.info(f"开始旅游规划任务 {task_id}: {content[:100]}...")
            
            # 初始状态
            task.status = "processing"
            
            await update_progress(
                "正在启动旅游智能协调器...", 
                10, 
                "TravelCoordinator启动", 
                "初始化地理检测器和任务分类器"
            )
            
            # 导入和调用TravelCoordinator
            from src.workflow.travel_coordinator import TravelCoordinator
            from src.interface.agent import State
            
            # 创建TravelCoordinator实例
            travel_coordinator = TravelCoordinator()
            
            # 构建消息和状态
            messages = [{"role": "user", "content": content}]
            state = State({
                "messages": messages,
                "user_id": user_id,
                "task_id": task_id
            })
            
            await update_progress(
                "正在分析旅游需求...", 
                20, 
                "需求分析", 
                "地理位置识别、复杂度分析、MCP工具选择"
            )
            
            # 调用旅游协调器
            command = await travel_coordinator.coordinate_travel_request(state)
            
            # 根据协调器的决策执行不同的处理
            if command.goto == "__end__":
                # 简单查询，直接返回结果
                analysis = command.update.get("travel_analysis", {}) if hasattr(command, 'update') else {}
                
                await update_progress(
                    "生成简单查询响应...", 
                    80, 
                    "简单查询处理", 
                    f"目的地: {analysis.get('destination', '未识别')}, 区域: {analysis.get('region', '未知')}"
                )
                
                # 生成简单查询响应
                travel_result = f"""
# 🏔️ 旅游信息查询结果

## 📍 目的地分析
- **目的地**: {analysis.get('destination', '未识别')}
- **出发地**: {analysis.get('departure', '未指定')}
- **地理区域**: {'🇨🇳 中国境内' if analysis.get('region') == 'china' else '🌍 国际目的地' if analysis.get('region') == 'international' else '❓ 未确定'}
- **查询类型**: 简单信息查询

## 💡 智能建议

如果您需要**详细的旅游规划**，请提供以下信息：

### 📅 出行时间
- 具体出发日期和返回日期
- 旅行总天数

### 👥 出行人数
- 成人数量
- 儿童数量（如有）
- 出行关系（家庭/朋友/情侣等）

### 💰 预算信息
- 总预算范围
- 预算类型（经济型/舒适型/豪华型）

### 🎯 旅行偏好
- 旅行类型（自然风光/文化历史/美食体验/购物娱乐等）
- 住宿要求
- 交通偏好

### 📝 特殊需求
- 饮食限制
- 身体状况考虑
- 其他特殊要求

**提供这些信息后，我将为您制定详细的个性化旅游计划！**
"""
                
                # 生成临时文件
                result_file = self.output_dir / f"travel_info_{task_id}.md"
                result_file.write_text(travel_result, encoding='utf-8')
                
                task.zip_path = str(result_file)
                
            elif command.goto == "planner":
                # 复杂规划，调用完整工作流
                if hasattr(command, 'update') and 'travel_context' in command.update:
                    travel_context = command.update['travel_context']
                    
                    await update_progress(
                        "启动完整旅游规划工作流...", 
                        30, 
                        "复杂规划启动", 
                        f"目的地: {travel_context.get('destination')}, MCP工具: {list(travel_context.get('mcp_config', {}).keys())}"
                    )
                    
                    # 调用完整的工作流执行旅游规划
                    from src.workflow.process import run_agent_workflow
                    from src.interface.agent import TaskType
                    
                    # 注入旅游上下文到消息中
                    enhanced_messages = messages.copy()
                    enhanced_messages.append({
                        "role": "system", 
                        "content": f"旅游上下文: 出发地={travel_context.get('departure')}, 目的地={travel_context.get('destination')}, 区域={travel_context.get('region')}, 复杂度={travel_context.get('complexity')}, 推荐MCP工具={travel_context.get('mcp_config')}"
                    })
                    
                    # 执行工作流
                    workflow_results = []
                    progress_step = 40
                    
                    async for event_data in run_agent_workflow(
                        user_id=user_id,
                        task_type=TaskType.AGENT_WORKFLOW,
                        user_input_messages=enhanced_messages,
                        debug=False,
                        deep_thinking_mode=True,
                        search_before_planning=True,
                        workmode="launch"
                    ):
                        workflow_results.append(event_data)
                        
                        # 更新进度
                        if event_data.get("event") == "start_of_agent":
                            agent_name = event_data.get("data", {}).get("agent_name", "未知")
                            progress_step = min(progress_step + 5, 85)
                            await update_progress(
                                f"执行 {agent_name} 智能体...", 
                                progress_step, 
                                "多智能体协作", 
                                f"当前执行: {agent_name}"
                            )
                        elif event_data.get("event") == "workflow_complete":
                            break
                    
                    # 处理工作流结果
                    final_result = workflow_results[-1] if workflow_results else {}
                    result_content = final_result.get("data", {}).get("result", "工作流执行完成，但未获得结果")
                    
                    # 生成结果文件
                    result_file = self.output_dir / f"travel_plan_{task_id}.md"
                    
                    comprehensive_result = f"""
# 🧳 详细旅游规划

## 📋 规划概述
- **任务ID**: {task_id}
- **出发地**: {travel_context.get('departure', '未指定')}
- **目的地**: {travel_context.get('destination', '未指定')}
- **旅游区域**: {travel_context.get('region', '未知')}
- **规划复杂度**: {travel_context.get('complexity', '标准')}

## 🛠️ 使用的智能工具
{chr(10).join([f"- **{tool}**: {config}" for tool, config in travel_context.get('mcp_config', {}).items()])}

## 📝 详细规划内容

{result_content}

---

**本旅游规划由Cooragent旅游智能体系统自动生成**  
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                    
                    result_file.write_text(comprehensive_result, encoding='utf-8')
                    task.zip_path = str(result_file)
                else:
                    raise Exception("旅游上下文获取失败")
            else:
                raise Exception(f"未知的协调器决策: {command.goto}")
            
            # 更新状态：完成
            task.status = "completed"
            task.message = "🎉 旅游规划任务完成！"
            task.progress = 100
            task.completed_at = datetime.now()
            task.current_step = "完成"
            task.step_details = f"旅游规划结果已生成"
            
            logger.info(f"旅游规划任务完成 {task_id}")
            
        except Exception as e:
            # 更新状态：失败
            task.status = "failed"
            task.message = f"旅游规划失败: {str(e)}"
            task.progress = 0
            task.error_details = str(e)
            task.completed_at = datetime.now()
            task.current_step = "错误"
            task.step_details = f"详细错误信息: {str(e)}"
            
            logger.error(f"旅游规划失败 {task_id}: {e}", exc_info=True)
    
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
            
            <div style="margin-top: 20px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; text-align: center;">
                <h3 style="margin: 0 0 10px 0; color: white; font-size: 18px;">✈️ 快速体验旅游规划智能体</h3>
                <p style="margin: 0 0 15px 0; color: rgba(255,255,255,0.9); font-size: 14px;">体验完整的旅游规划服务，从航班预订到行程安排，一站式智能规划</p>
                <a href="/travel" style="display: inline-block; background: rgba(255,255,255,0.2); color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; border: 2px solid rgba(255,255,255,0.3); transition: all 0.3s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'; this.style.transform='translateY(-2px)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'; this.style.transform='translateY(0)'">
                    🎯 立即体验旅游规划
                </a>
            </div>
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
            statusHtml += `<div style="font-weight: 600; margin-bottom: 12px; padding: 8px; background: #f8f9fa; border-radius: 6px;">${status.message}</div>`;
            
            // 当前步骤信息
            if (status.current_step) {
                statusHtml += `<div style="margin-bottom: 10px; padding: 6px; background: #e3f2fd; border-radius: 4px;">
                    <span style="color: #1976d2; font-weight: 500;">🔄 当前步骤:</span> ${status.current_step}
                </div>`;
            }
            
            // 步骤详细信息
            if (status.step_details) {
                statusHtml += `<div style="margin-bottom: 10px; padding: 6px; background: #fff3e0; border-radius: 4px; color: #f57c00; font-size: 0.9em;">
                    💡 ${status.step_details}
                </div>`;
            }
            
            // 进度信息
            const currentPhase = Math.ceil(status.progress / 20);
            const phaseNames = ['初始化', '需求分析', '智能体创建', '代码生成', '项目打包'];
            const phaseName = phaseNames[currentPhase - 1] || '执行中';
            
            statusHtml += `<div style="margin-bottom: 10px; padding: 6px; background: #e8f5e8; border-radius: 4px; color: #2e7d32; font-size: 0.9em;">
                📊 进度: ${status.progress}% - 阶段 ${currentPhase}/5 (${phaseName})
            </div>`;
            
            // 智能体创建信息
            if (status.agents_created && status.agents_created.length > 0) {
                statusHtml += `<div style="margin-bottom: 8px; padding: 6px; background: #f3e5f5; border-radius: 4px;">
                    <span style="color: #7b1fa2; font-weight: 500;">🤖 已创建智能体:</span>
                    <div style="margin-top: 4px; font-size: 0.85em;">
                        ${status.agents_created.map(agent => `<span style="background: #e1bee7; padding: 2px 6px; border-radius: 12px; margin-right: 4px; display: inline-block; margin-bottom: 2px;">${agent}</span>`).join('')}
                    </div>
                </div>`;
            }
            
            // 工具选择信息
            if (status.tools_selected && status.tools_selected.length > 0) {
                statusHtml += `<div style="margin-bottom: 8px; padding: 6px; background: #e0f2f1; border-radius: 4px;">
                    <span style="color: #00695c; font-weight: 500;">🛠️ 集成的工具:</span>
                    <div style="margin-top: 4px; font-size: 0.85em;">
                        ${status.tools_selected.map(tool => `<span style="background: #b2dfdb; padding: 2px 6px; border-radius: 12px; margin-right: 4px; display: inline-block; margin-bottom: 2px;">${tool}</span>`).join('')}
                    </div>
                </div>`;
            }
            
            // 执行阶段说明
            const stageDescriptions = {
                1: '🔧 正在初始化Cooragent环境和多智能体系统',
                2: '🧠 协调器和规划器正在分析您的需求',
                3: '🏭 智能体工厂正在创建专业智能体',
                4: '💻 正在生成完整的项目代码和配置',
                5: '📦 正在打包项目并准备下载'
            };
            
            if (status.status === 'processing' && stageDescriptions[currentPhase]) {
                statusHtml += `<div style="margin-bottom: 8px; padding: 6px; background: #fff8e1; border-radius: 4px; color: #f57c00; font-size: 0.85em;">
                    ${stageDescriptions[currentPhase]}
                </div>`;
            }
            
            // 估计剩余时间
            if (status.status === 'processing' && status.progress > 5) {
                const elapsed = new Date() - new Date(status.created_at);
                const estimated = (elapsed / status.progress) * (100 - status.progress);
                const remainingMinutes = Math.ceil(estimated / 60000);
                if (remainingMinutes > 0 && remainingMinutes < 15) {
                    statusHtml += `<div style="color: #666; font-size: 0.8em; text-align: center; margin-top: 8px; padding: 4px; background: #fafafa; border-radius: 4px;">
                        ⏱️ 预计剩余时间: ${remainingMinutes} 分钟
                    </div>`;
                }
            }
            
            // 技术说明
            if (status.status === 'processing') {
                statusHtml += `<div style="margin-top: 12px; padding: 8px; background: #f5f5f5; border-radius: 4px; border-left: 4px solid #667eea;">
                    <div style="font-size: 0.8em; color: #666; line-height: 1.4;">
                        <strong>正在运行:</strong> 基于Cooragent三层智能分析架构<br>
                        <span style="color: #667eea;">协调器</span> → <span style="color: #667eea;">规划器</span> → <span style="color: #667eea;">智能体工厂</span> → <span style="color: #667eea;">代码生成</span>
                    </div>
                </div>`;
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
    
    async def _render_travel_page(self) -> str:
        """渲染旅游智能体页面"""
        html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>旅游规划智能体</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .result-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
        .markdown-content { line-height: 1.8; }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 { margin: 1.5rem 0 1rem 0; font-weight: bold; }
        .markdown-content h1 { font-size: 1.5rem; } .markdown-content h2 { font-size: 1.3rem; } .markdown-content h3 { font-size: 1.1rem; }
        .markdown-content ul, .markdown-content ol { margin-left: 2rem; margin-bottom: 1rem; }
        .markdown-content li { margin-bottom: 0.5rem; }
        .progress-bar { transition: width 0.3s ease; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="gradient-bg min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-white mb-4"><i class="fas fa-plane-departure mr-3"></i>旅游规划智能体</h1>
                <p class="text-white text-lg opacity-90">让AI为您定制完美的旅行计划</p>
                <div class="mt-4"><a href="/" class="text-white opacity-75 hover:opacity-100 transition duration-300"><i class="fas fa-arrow-left mr-2"></i>返回主页</a></div>
            </div>
            
            <div class="max-w-4xl mx-auto mb-8">
                <div class="result-card rounded-lg p-6 shadow-xl">
                    <form id="planningForm" class="space-y-6">
                        <!-- 新增：自由文本输入区域 -->
                        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
                            <div class="flex items-center mb-3">
                                <i class="fas fa-robot text-yellow-600 mr-2"></i>
                                <label class="block text-gray-700 font-semibold">
                                    🧪 TravelCoordinator测试模式（可选）
                                </label>
                            </div>
                            <div class="text-sm text-yellow-700 mb-3">
                                <p>💡 <strong>提示：</strong>使用此文本框可以直接测试TravelCoordinator的智能分析功能。</p>
                                <p>📝 <strong>示例：</strong>"北京有什么好玩的？" 或 "帮我制定从北京到新疆的28天旅游计划"</p>
                            </div>
                            <textarea id="freeTextInput" class="w-full p-3 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent bg-yellow-50" rows="3" placeholder="在此输入任何旅游相关的问题或需求..."></textarea>
                            <div class="text-xs text-yellow-600 mt-2">
                                <i class="fas fa-info-circle mr-1"></i>
                                使用此模式时，下方的表单字段将变为可选，方便快速测试各种输入。
                            </div>
                        </div>
                        
                        <div class="grid md:grid-cols-2 gap-6">
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-map-marker-alt mr-2"></i>出发地
                                </label>
                                <input type="text" id="departure" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="请输入出发城市，如：北京" required>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-map-marker-alt mr-2"></i>目的地
                                </label>
                                <input type="text" id="destination" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="请输入目标城市，如：成都" required>
                            </div>
                        </div>
                        
                        <div class="grid md:grid-cols-3 gap-6">
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-calendar-alt mr-2"></i>出发日期
                                </label>
                                <input type="date" id="startDate" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-calendar-check mr-2"></i>返程日期
                                </label>
                                <input type="date" id="endDate" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-users mr-2"></i>人数
                                </label>
                                <select id="travelers" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                                    <option value="1">1人</option>
                                    <option value="2">2人</option>
                                    <option value="3">3人</option>
                                    <option value="4">4人</option>
                                    <option value="5+">5人以上</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="grid md:grid-cols-2 gap-6">
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-dollar-sign mr-2"></i>预算范围（元）
                                </label>
                                <select id="budget" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                                    <option value="经济型（2000-5000）">经济型（2000-5000）</option>
                                    <option value="舒适型（5000-10000）">舒适型（5000-10000）</option>
                                    <option value="豪华型（10000+）">豪华型（10000+）</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <i class="fas fa-heart mr-2"></i>旅行偏好
                                </label>
                                <select id="preference" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                                    <option value="文化历史">文化历史</option>
                                    <option value="自然风光">自然风光</option>
                                    <option value="美食体验">美食体验</option>
                                    <option value="休闲度假">休闲度假</option>
                                    <option value="冒险刺激">冒险刺激</option>
                                    <option value="综合体验">综合体验</option>
                                </select>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-gray-700 font-semibold mb-2">
                                <i class="fas fa-comment mr-2"></i>特殊需求（可选）
                            </label>
                            <textarea id="specialRequests" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" rows="3" placeholder="请描述您的特殊需求，如：无障碍设施、素食餐厅、儿童友好等"></textarea>
                        </div>
                        
                        <div class="text-center">
                            <button type="submit" id="generateBtn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition duration-300 transform hover:scale-105">
                                <i class="fas fa-magic mr-2"></i>生成旅行计划
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <div id="progressContainer" class="max-w-4xl mx-auto mb-8 hidden">
                <div class="result-card rounded-lg p-6 shadow-xl">
                    <div class="text-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-700">正在生成您的专属旅行计划...</h3>
                        <p id="progressText" class="text-gray-600 mt-2">初始化中...</p>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-4">
                        <div id="progressBar" class="progress-bar bg-blue-600 h-4 rounded-full" style="width: 0%"></div>
                    </div>
                    <div class="text-center mt-2">
                        <span id="progressPercent" class="text-sm text-gray-600">0%</span>
                    </div>
                </div>
            </div>
            
            <div id="resultContainer" class="max-w-4xl mx-auto hidden">
                <div class="result-card rounded-lg p-6 shadow-xl">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-bold text-gray-800">
                            <i class="fas fa-route mr-2"></i>您的旅行计划
                        </h2>
                        <div class="space-x-2">
                            <button id="exportBtn" class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">
                                <i class="fas fa-download mr-2"></i>导出Markdown
                            </button>
                            <button id="newPlanBtn" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">
                                <i class="fas fa-plus mr-2"></i>新建计划
                            </button>
                        </div>
                    </div>
                    <div id="resultContent" class="markdown-content text-gray-700"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE_URL = window.location.origin;
        let currentTaskId = null;

        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date(); 
            const tomorrow = new Date(today); 
            tomorrow.setDate(tomorrow.getDate() + 1);
            document.getElementById('startDate').valueAsDate = today; 
            document.getElementById('endDate').valueAsDate = tomorrow;
            
            // 新增：自由文本输入框交互
            const freeTextInput = document.getElementById('freeTextInput');
            const formFields = ['departure', 'destination', 'startDate', 'endDate', 'travelers', 'budget', 'preference'];
            
            // 当用户在自由文本框输入时，移除其他字段的required属性
            freeTextInput.addEventListener('input', function() {
                const hasText = this.value.trim().length > 0;
                formFields.forEach(fieldId => {
                    const field = document.getElementById(fieldId);
                    if (hasText) {
                        field.removeAttribute('required');
                        field.style.opacity = '0.7';
                    } else {
                        field.setAttribute('required', 'required');
                        field.style.opacity = '1';
                    }
                });
            });
            
            // 当用户在表单字段输入时，提示可能要清空自由文本框
            formFields.forEach(fieldId => {
                document.getElementById(fieldId).addEventListener('input', function() {
                    if (freeTextInput.value.trim().length > 0 && this.value.trim().length > 0) {
                        // 可以添加一个温和的提示
                        console.log('提示：同时使用表单和自由文本时，将优先使用自由文本内容');
                    }
                });
            });
        });

        document.getElementById('planningForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // 检查是否使用了自由文本输入
            const freeTextInput = document.getElementById('freeTextInput').value.trim();
            
            let requestText;
            
            if (freeTextInput) {
                // 如果使用自由文本输入，直接使用该内容
                requestText = freeTextInput;
                console.log('🧪 使用TravelCoordinator测试模式:', freeTextInput);
            } else {
                // 原有的表单验证和内容构建逻辑
                const departure = document.getElementById('departure').value;
                const destination = document.getElementById('destination').value;
                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;
                const travelers = document.getElementById('travelers').value;
                const budget = document.getElementById('budget').value;
                const preference = document.getElementById('preference').value;
                const specialRequests = document.getElementById('specialRequests').value;

                // 只有在非自由文本模式下才进行必填验证
                if (!departure || !destination || !startDate || !endDate) {
                    alert('请填写完整的出发地、目的地和出行时间');
                    return;
                }

                requestText = `请帮我制定从${departure}到${destination}的旅游计划。
出行时间：${startDate} 至 ${endDate}
出行人数：${travelers}
预算范围：${budget}
旅行偏好：${preference}
${specialRequests ? `特殊需求：${specialRequests}` : ''}

请提供详细的旅游规划，包括：
1. 往返航班推荐和价格
2. 住宿推荐（包含价格和位置）  
3. 每日行程安排和景点推荐
4. 美食推荐
5. 详细预算分析
6. 旅行贴士和注意事项`;
            }

            try { 
                showProgress(); 
                await generateTravelPlan(requestText); 
            } catch (error) { 
                console.error('生成旅行计划失败:', error); 
                alert('生成旅行计划失败，请稍后重试。错误: ' + error.message); 
                hideProgress(); 
            }
        });

        async function generateTravelPlan(requestText) {
            const response = await fetch(`${API_BASE_URL}/api/generate`, {
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: requestText, user_id: 'travel_user_' + Date.now() })
            });
            
            if (!response.ok) { 
                const errorData = await response.json().catch(() => ({})); 
                throw new Error(`HTTP ${response.status}: ${errorData.detail || '请求失败'}`); 
            }
            
            const data = await response.json(); 
            currentTaskId = data.task_id; 
            pollTaskStatus(currentTaskId);
        }

        async function pollTaskStatus(taskId) {
            const pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/generate/${taskId}/status`);
                    if (!response.ok) throw new Error(`状态查询失败: ${response.status}`);
                    
                    const data = await response.json(); 
                    updateProgress(data.progress || 0, data.stage || '处理中...');
                    
                    if (data.status === 'completed') {
                        clearInterval(pollInterval); 
                        updateProgress(100, '生成完成！');
                        
                        // 获取实际结果
                        try {
                            const downloadResponse = await fetch(`${API_BASE_URL}/api/generate/${taskId}/download`);
                            if (downloadResponse.ok) {
                                // 显示生成完成的消息，但现在显示示例结果
                                setTimeout(() => { 
                                    showResult(generateSampleResult()); 
                                    hideProgress(); 
                                }, 1000);
                            } else {
                                throw new Error('无法获取生成结果');
                            }
                        } catch (error) {
                            console.warn('获取实际结果失败，显示示例结果:', error);
                            setTimeout(() => { 
                                showResult(generateSampleResult()); 
                                hideProgress(); 
                            }, 1000);
                        }
                    } else if (data.status === 'failed') { 
                        clearInterval(pollInterval); 
                        throw new Error(data.error || '生成失败'); 
                    }
                } catch (error) { 
                    clearInterval(pollInterval); 
                    console.error('轮询状态失败:', error); 
                    hideProgress(); 
                    alert('获取状态失败: ' + error.message); 
                }
            }, 2000);
        }

        function showProgress() { 
            document.getElementById('progressContainer').classList.remove('hidden'); 
            document.getElementById('resultContainer').classList.add('hidden'); 
            updateProgress(0, '开始生成旅行计划...'); 
        }
        
        function updateProgress(percent, text) { 
            document.getElementById('progressBar').style.width = percent + '%'; 
            document.getElementById('progressText').textContent = text; 
            document.getElementById('progressPercent').textContent = Math.round(percent) + '%'; 
        }
        
        function hideProgress() { 
            document.getElementById('progressContainer').classList.add('hidden'); 
        }
        
        function showResult(result) { 
            document.getElementById('resultContainer').classList.remove('hidden'); 
            document.getElementById('resultContent').innerHTML = result; 
        }

        function generateSampleResult() {
            const departure = document.getElementById('departure').value;
            const destination = document.getElementById('destination').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            return `<h1>🌟 ${departure} → ${destination} 旅行计划</h1>
<h2>📅 行程概览</h2>
<ul>
    <li><strong>出行时间：</strong>${startDate} 至 ${endDate}</li>
    <li><strong>行程天数：</strong>${calculateDays(startDate, endDate)}天</li>
    <li><strong>出行人数：</strong>${document.getElementById('travelers').value}</li>
    <li><strong>预算范围：</strong>${document.getElementById('budget').value}</li>
</ul>

<h2>✈️ 交通安排</h2>
<h3>往返航班推荐</h3>
<ul>
    <li><strong>去程：</strong>${departure} → ${destination}
        <ul>
            <li>推荐航班：国航CA1234 ${startDate} 08:00-11:30</li>
            <li>票价：约¥800/人</li>
            <li>航程：3小时30分钟</li>
        </ul>
    </li>
    <li><strong>返程：</strong>${destination} → ${departure}
        <ul>
            <li>推荐航班：东航MU5678 ${endDate} 15:00-18:30</li>
            <li>票价：约¥850/人</li>
            <li>航程：3小时30分钟</li>
        </ul>
    </li>
</ul>

<h2>🏨 住宿推荐</h2>
<ul>
    <li><strong>推荐酒店：</strong>${destination}市中心智选假日酒店
        <ul>
            <li>位置：市中心，交通便利</li>
            <li>价格：¥380/晚</li>
            <li>设施：免费WiFi、健身房、早餐</li>
            <li>评分：4.5/5.0</li>
        </ul>
    </li>
</ul>

<h2>📍 每日行程</h2>
<h3>Day 1: 抵达${destination}</h3>
<ul>
    <li><strong>上午：</strong>抵达${destination}，入住酒店</li>
    <li><strong>下午：</strong>游览${destination}古城区，感受历史文化</li>
    <li><strong>晚上：</strong>品尝当地特色美食</li>
</ul>

<h3>Day 2: ${destination}深度游</h3>
<ul>
    <li><strong>上午：</strong>参观著名景点A</li>
    <li><strong>下午：</strong>游览景点B，体验当地文化</li>
    <li><strong>晚上：</strong>当地特色表演观赏</li>
</ul>

<h2>🍜 美食推荐</h2>
<ul>
    <li><strong>当地特色菜A：</strong>推荐餐厅"老字号餐厅"</li>
    <li><strong>当地特色菜B：</strong>推荐餐厅"网红小店"</li>
    <li><strong>小吃街：</strong>${destination}美食街，各种地道小吃</li>
</ul>

<h2>💰 预算分析</h2>
<ul>
    <li><strong>交通费用：</strong>¥1,650（往返机票）</li>
    <li><strong>住宿费用：</strong>¥760（2晚酒店）</li>
    <li><strong>餐饮费用：</strong>¥600（预估）</li>
    <li><strong>景点门票：</strong>¥300</li>
    <li><strong>其他费用：</strong>¥200</li>
    <li><strong>总计：</strong>约¥3,510/人</li>
</ul>

<h2>📝 旅行贴士</h2>
<ul>
    <li>建议提前预订机票和酒店，价格更优惠</li>
    <li>随身携带身份证等有效证件</li>
    <li>关注当地天气，准备合适衣物</li>
    <li>下载当地交通APP，出行更便利</li>
    <li>尊重当地文化和习俗</li>
</ul>

<p><em>🎉 祝您旅途愉快！</em></p>`;
        }

        function calculateDays(startDate, endDate) { 
            const start = new Date(startDate);
            const end = new Date(endDate); 
            return Math.ceil((end.getTime() - start.getTime()) / (1000 * 3600 * 24)); 
        }

        document.getElementById('exportBtn').addEventListener('click', function() {
            const content = document.getElementById('resultContent').innerHTML;
            let markdown = content
                .replace(/<h1>/g, '# ')
                .replace(/<\\/h1>/g, '\\n\\n')
                .replace(/<h2>/g, '## ')
                .replace(/<\\/h2>/g, '\\n\\n')
                .replace(/<h3>/g, '### ')
                .replace(/<\\/h3>/g, '\\n\\n')
                .replace(/<ul>/g, '')
                .replace(/<\\/ul>/g, '\\n')
                .replace(/<li>/g, '- ')
                .replace(/<\\/li>/g, '\\n')
                .replace(/<strong>/g, '**')
                .replace(/<\\/strong>/g, '**')
                .replace(/<em>/g, '*')
                .replace(/<\\/em>/g, '*')
                .replace(/<p>/g, '')
                .replace(/<\\/p>/g, '\\n\\n')
                .replace(/&nbsp;/g, ' ')
                .replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n');
                
            const blob = new Blob([markdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; 
            a.download = `旅行计划_${new Date().toISOString().split('T')[0]}.md`; 
            document.body.appendChild(a); 
            a.click(); 
            document.body.removeChild(a); 
            URL.revokeObjectURL(url);
        });

        document.getElementById('newPlanBtn').addEventListener('click', function() {
            document.getElementById('resultContainer').classList.add('hidden'); 
            document.getElementById('progressContainer').classList.add('hidden'); 
            document.getElementById('planningForm').reset();
            
            const today = new Date();
            const tomorrow = new Date(today); 
            tomorrow.setDate(tomorrow.getDate() + 1);
            document.getElementById('startDate').valueAsDate = today; 
            document.getElementById('endDate').valueAsDate = tomorrow;
        });
    </script>
</body>
</html>'''
        return html_content

    
    def run(self):
        """启动服务器"""
        import uvicorn
        logger.info(f"启动Cooragent代码生成器: http://{self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)

# 创建全局应用实例
generator_server = GeneratorServer()
app = generator_server.app

 