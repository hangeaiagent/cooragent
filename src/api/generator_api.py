"""
代码生成器API扩展

扩展Cooragent现有的Server功能，添加项目代码生成接口
"""

import asyncio
import logging
import uuid
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 导入现有Cooragent组件
from src.service.server import Server
from src.generator.cooragent_generator import EnhancedCooragentProjectGenerator
from src.utils.path_utils import get_project_root

# 配置统一的日志输出到文件
def setup_application_logger():
    """设置应用日志，输出到 logs/generator.log"""
    # 创建logs目录
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有handlers避免重复
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建文件handler
    file_handler = logging.FileHandler("logs/generator.log", encoding='utf-8', mode='a')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台handler（可选，用于调试）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # 只显示WARNING及以上级别到控制台
    
    # 创建formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

# 初始化日志配置
setup_application_logger()
logger = logging.getLogger(__name__)

# API模型定义
class GenerateRequest(BaseModel):
    content: Optional[str] = None
    requirement: Optional[str] = None  # 兼容前端请求格式
    workflow_mode: Optional[str] = "production"  # 新增模式字段
    user_id: Optional[str] = None
    
    def get_content(self) -> str:
        """获取请求内容，兼容两种格式"""
        return self.requirement or self.content or ""
    
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
    travel_result: Optional[str] = None  # 旅游规划结果内容

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
            
            # 获取请求内容
            content = request.get_content()
            logger.info(f"收到请求: {content[:100]}...")
            logger.info(f"工作流模式: {request.workflow_mode}")
            
            # 如果是consultation模式，直接进行简单咨询处理
            if request.workflow_mode == "consultation":
                logger.info(f"🤖 [请求分析] 识别为旅游咨询任务 - user_id: {user_id}, task_id: {task_id}")
                
                task_status = GenerationStatus(
                    task_id=task_id,
                    status="processing",
                    message="正在处理您的旅游咨询...",
                    created_at=datetime.now(),
                    current_step="旅游咨询处理",
                    step_details="AI正在分析您的问题并生成专业回答",
                    progress=5
                )
                self.generation_tasks[task_id] = task_status
                
                background_tasks.add_task(self._run_consultation, task_id, content, user_id)
                
                response = GenerateResponse(
                    task_id=task_id,
                    status="processing",
                    message="正在为您生成旅游咨询回答",
                    created_at=datetime.now()
                )
                
                return response
            
            # 检测是否为旅游相关任务
            from src.workflow.process import is_travel_related_task
            messages = [{"content": content}]
            is_travel = is_travel_related_task(messages)
            
            if is_travel:
                # 旅游规划任务
                logger.info(f"🧳 [请求分析] 识别为旅游规划任务 - user_id: {user_id}, task_id: {task_id}")
                logger.info(f"🧳 [请求分析] 请求内容: {content}")
                
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
                
                background_tasks.add_task(self._run_travel_planning, task_id, content, user_id)
                
                response = GenerateResponse(
                    task_id=task_id,
                    status="processing",
                    message="旅游规划已开始，基于智能旅游协调器进行分析",
                    created_at=datetime.now()
                )
            else:
                # 代码生成任务
                logger.info(f"🔧 [请求分析] 识别为代码生成任务 - user_id: {user_id}, task_id: {task_id}")
                logger.info(f"🔧 [请求分析] 请求内容: {content}")
                
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
                
                background_tasks.add_task(self._run_code_generation, task_id, content, user_id)
                
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
            """下载生成的代码或获取旅游规划结果"""
            if task_id not in self.generation_tasks:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            task = self.generation_tasks[task_id]
            
            if task.status != "completed":
                raise HTTPException(status_code=400, detail="任务还未完成")
            
            # 优先返回travel_result（用于咨询和旅游规划结果）
            if hasattr(task, 'travel_result') and task.travel_result:
                return Response(
                    content=task.travel_result,
                    media_type="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename=travel_result_{task_id}.md"}
                )
            
            # 如果没有travel_result，检查是否有zip文件
            if not task.zip_path or not Path(task.zip_path).exists():
                raise HTTPException(status_code=404, detail="生成的文件不存在")
            
            file_path = Path(task.zip_path)
            
            # 检查文件类型
            if file_path.suffix == '.md':
                # 旅游规划结果文件，返回文本内容
                try:
                    content = file_path.read_text(encoding='utf-8')
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        content={"content": content, "type": "travel_plan"},
                        media_type="application/json"
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
            else:
                # ZIP文件，返回文件下载
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
    
    async def _run_consultation(self, task_id: str, question: str, user_id: str):
        """处理旅游咨询请求 - 使用Coordinator Agent智能判断"""
        try:
            task = self.generation_tasks[task_id]
            
            # 更新进度
            async def update_progress(message: str, progress: int, step: str, details: str):
                task.message = message
                task.progress = progress
                task.current_step = step
                task.step_details = details
                logger.info(f"📊 进度更新 [{progress}%]: {step} - {details}")
            
            await update_progress("正在启动Coordinator Agent...", 10, "Agent启动", "Coordinator Agent正在分析您的请求")
            
            # 使用Coordinator Agent进行智能判断
            from src.workflow.travel_coordinator import TravelCoordinator, GeographyDetector, TravelTaskClassifier
            
            await update_progress("正在分析问题复杂度...", 20, "智能分析", "Coordinator Agent正在判断问题类型和处理方式")
            
            # 初始化分析组件
            geo_detector = GeographyDetector()
            travel_classifier = TravelTaskClassifier()
            
            logger.info(f"🧠 [Coordinator Agent] 开始智能分析用户问题...")
            logger.info(f"🧠 [用户问题] {question}")
            
            # 创建消息格式以供分析
            messages = [{"role": "user", "content": question}]
            
            # 1. 地理位置识别
            departure, destination = geo_detector.extract_locations(messages)
            logger.info(f"🌍 [地理分析] 出发地: {departure}, 目的地: {destination}")
            
            # 2. 任务复杂度分析
            complexity = travel_classifier.analyze_complexity(messages)
            logger.info(f"🔍 [复杂度分析] 任务复杂度: {complexity}")
            
            await update_progress("正在制定处理策略...", 40, "策略制定", f"分析结果: {complexity}复杂度，根据问题类型选择处理方式")
            
            # 调用coordinator进行智能判断和处理
            try:
                if complexity == "simple":
                    # 简单查询：使用增强的LLM直接回答
                    logger.info(f"🚀 [简单查询] 使用增强LLM处理简单旅游咨询...")
                    
                    from src.llm.llm import get_llm_by_type
                    llm_client = get_llm_by_type("basic")
                    
                    # 构建增强提示词，包含地理信息
                    geo_context = ""
                    if destination:
                        travel_region = geo_detector.classify_region(destination)
                        geo_context = f"\n\n地理信息分析：\n- 目的地：{destination}\n- 区域类型：{travel_region}"
                        if departure:
                            geo_context += f"\n- 出发地：{departure}"
                    
                    prompt = f"""您是一位专业的旅游顾问，请根据用户的问题提供准确、实用的旅游建议。

用户问题：{question}{geo_context}

请提供：
1. 针对性的回答（结合目的地特色）
2. 实用的建议（根据地理位置）
3. 相关的注意事项
4. 具体的推荐（景点、美食、住宿等）

请用友好、专业的语气回答，并使用Markdown格式。"""

                    await update_progress("正在生成专业回答...", 70, "AI分析", "基于地理信息的智能回答生成中")
                    
                    logger.info(f"📝 [增强提示词] 发送给大模型的完整提示词长度: {len(prompt)} 字符")
                    response = llm_client.invoke(prompt)
                    
                    if response and hasattr(response, 'content'):
                        answer = response.content
                        logger.info(f"✅ [简单查询完成] 回答长度: {len(answer)} 字符")
                    else:
                        answer = "抱歉，我暂时无法回答您的问题，请稍后重试。"
                        logger.warning(f"⚠️ [简单查询] 无法提取有效回答")
                    
                    travel_result = f"""# 🎯 旅游咨询回答

## 📝 您的问题
{question}

## 💡 专业回答
{answer}

---

**💬 如果您需要更详细的旅游规划，请提供具体的出行时间、人数、预算等信息，我将为您制定完整的旅游计划。**
"""
                    
                else:
                    # 复杂查询：调用完整的旅游规划流程
                    logger.info(f"🚀 [复杂规划] 启动多智能体旅游规划流程...")
                    
                    await update_progress("正在启动旅游规划流程...", 60, "规划启动", "调用专业旅游规划智能体")
                    
                    # 这里应该调用完整的旅游规划流程，暂时先用增强回答
                    from src.llm.llm import get_llm_by_type
                    llm_client = get_llm_by_type("basic")
                    
                    detailed_prompt = f"""您是一位资深旅游规划专家，请为用户制定详细的旅游方案。

用户需求：{question}

请提供完整的旅游规划，包括：
1. 行程概览和时间安排
2. 景点推荐和路线规划  
3. 住宿建议（不同价位）
4. 美食推荐和特色体验
5. 交通方式和预算估算
6. 注意事项和实用建议

请用专业、详细的方式回答，使用Markdown格式，确保信息实用且可操作。"""

                    await update_progress("正在制定详细规划...", 80, "规划制定", "生成完整旅游方案中")
                    
                    logger.info(f"📝 [详细规划] 发送给大模型的规划提示词长度: {len(detailed_prompt)} 字符")
                    response = llm_client.invoke(detailed_prompt)
                    
                    if response and hasattr(response, 'content'):
                        answer = response.content
                        logger.info(f"✅ [复杂规划完成] 规划方案长度: {len(answer)} 字符")
                    else:
                        answer = "抱歉，暂时无法为您制定详细的旅游规划，请稍后重试。"
                        logger.warning(f"⚠️ [复杂规划] 无法生成规划方案")
                    
                    travel_result = f"""# 🗺️ 专业旅游规划方案

## 📝 您的需求
{question}

## 🎯 详细规划方案
{answer}

---

**📞 需要进一步咨询？请随时提出具体问题，我将为您提供更多专业建议。**
"""
                
                logger.info(f"📝 [最终结果] Coordinator Agent处理完成，结果长度: {len(travel_result)} 字符")
                
            except Exception as coordinator_error:
                logger.error(f"❌ [Coordinator错误] Coordinator处理失败: {coordinator_error}")
                logger.error(f"❌ [错误详情] {str(coordinator_error)}")
                
                # 如果Coordinator失败，降级到简单LLM处理
                await update_progress("智能分析失败，切换到基础模式...", 50, "降级处理", "使用基础大模型进行回答")
                
                from src.llm.llm import get_llm_by_type
                llm_client = get_llm_by_type("basic")
                
                prompt = f"""您是一位专业的旅游顾问，请根据用户的问题提供准确、实用的旅游建议。

用户问题：{question}

请提供：
1. 针对性的回答
2. 实用的建议
3. 相关的注意事项
4. 如果适用，提供具体的推荐

请用友好、专业的语气回答，并使用Markdown格式。"""

                logger.info(f"🔄 [降级处理] 使用基础LLM处理，提示词长度: {len(prompt)} 字符")
                response = llm_client.invoke(prompt)
                
                if response and hasattr(response, 'content'):
                    answer = response.content
                else:
                    answer = "抱歉，我暂时无法回答您的问题，请稍后重试。"
                
                travel_result = f"""# 🎯 旅游咨询回答

## 📝 您的问题
{question}

## 💡 专业回答
{answer}

---

**💬 如果您需要更详细的旅游规划，请提供具体的出行时间、人数、预算等信息，我将为您制定完整的旅游计划。**
"""
            
            # 存储结果
            task.travel_result = travel_result
            task.status = "completed"
            task.completed_at = datetime.now()
            task.progress = 100
            task.current_step = "咨询完成"
            task.step_details = "Coordinator Agent处理完成"
            
            logger.info(f"✅ 旅游咨询完成 - task_id: {task_id}")
            
        except Exception as e:
            logger.error(f"❌ 旅游咨询失败 - task_id: {task_id}, error: {e}")
            if task_id in self.generation_tasks:
                task = self.generation_tasks[task_id]
                task.status = "failed"
                task.error_details = str(e)
                task.completed_at = datetime.now()

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
                # 调用旅游协调器
            logger.info(f"🔄 正在调用TravelCoordinator处理: {content}")
            command = await travel_coordinator.coordinate_travel_request(state)
            logger.info(f"📋 TravelCoordinator返回结果: goto={command.goto}, update_keys={list(command.update.keys()) if hasattr(command, 'update') else 'None'}")
            if hasattr(command, 'update'):
                    logger.info(f"📊 返回的update内容: {command.update}")
                
            # 根据协调器的决策执行不同的处理
            if command.goto == "__end__":
                    # 简单查询，直接返回结果
                    logger.info("🎯 进入简单查询处理分支")
                    analysis = command.update.get("travel_analysis", {}) if hasattr(command, 'update') else {}
                    logger.info(f"📊 提取的travel_analysis: {analysis}")
                    
                    await update_progress(
                        "生成简单查询响应...", 
                        80, 
                        "简单查询处理", 
                        f"目的地: {analysis.get('destination', '未识别')}, 区域: {analysis.get('region', '未知')}"
                    )
                    
                    logger.info("🎯 检测到简单查询，直接使用大模型回复")
                
              
                
                    #   导入大模型服务
                    from src.llm.llm import basic_llm
                
                    try:
                        llm_client = basic_llm
                        
                        # 构建提示词
                        prompt = f"""你是一个专业的旅游顾问，请根据用户的问题提供详细、准确的回答。

用户问题：{content}

请提供：
1. 直接回答用户的具体问题
2. 相关的旅游信息和建议
3. 如果用户需要更详细的旅游规划，请提醒他们提供更多信息

请用中文回答，格式要清晰易读。"""

                        await update_progress(
                            "正在生成回答...", 
                            60, 
                            "生成回答", 
                            "大模型正在分析并生成专业回答"
                        )
                        logger.info(f"🎯 {prompt}")
                        # 调用大模型
                        response = llm_client.invoke(prompt)
                        # if response and hasattr(response, 'choices') and response.choices:
                        #     answer = response.choices[0].message.content
                        # else:
                        #     answer = "抱歉，我暂时无法回答您的问题，请稍后重试。"
                        # logger.info(f"🎯 {answer}")
                        # 提取回答内容
                        logger.info(f"response🎯 {response}")
                        if response and hasattr(response, 'content'):
                            answer = response.content
                        else:
                            answer = "抱歉，我暂时无法回答您的问题，请稍后重试。"
                        
                        await update_progress(
                            "回答生成完成...", 
                            90, 
                            "完成", 
                            "大模型回答已生成"
                        )
                        
                        # 格式化结果
                        travel_result = f"""# 🎯 旅游咨询回答

## 📝 您的问题
{content}

## 💡 专业回答
{answer}

---

**💬 如果您需要更详细的旅游规划，请提供具体的出行时间、人数、预算等信息，我将为您制定完整的旅游计划。**
"""
                        
                        # 直接存储结果到任务状态中
                        logger.info(f"回复结果🎯 {travel_result}")
                        task.travel_result = travel_result
                    
                    except Exception as e:
                        logger.error(f"大模型调用失败: {e}")
                        # 如果大模型调用失败，使用备用回答
                       
                        task.travel_result = f"大模型调用失败: {e}"
                    
            elif command.goto == "planner" or command.goto == "travel_planner":
                # 复杂规划，直接使用TravelCoordinator生成的详细计划
                logger.info("🎯 进入复杂规划处理分支")
                # 修复：从travel_context中提取数据并转换为travel_result格式
                travel_context = command.update.get("travel_context", {}) if hasattr(command, 'update') else {}
                travel_result = travel_context if travel_context else command.update.get("travel_result", {}) if hasattr(command, 'update') else {}
                logger.info(f"📊 提取的travel_result: {travel_result}")
                
                if travel_result:
                    await update_progress(
                        "生成详细旅游规划...", 
                        80, 
                        "复杂规划处理", 
                        f"目的地: {travel_result.get('destination', '未指定')}, 区域: {travel_result.get('region', '未知')}"
                    )
                    
                    # 生成实际的旅游规划内容，而不是技术配置信息
                    destination = travel_result.get('destination', '目的地')
                    departure = travel_result.get('departure', '出发地')
                    travel_type = travel_result.get('travel_type', 'general')
                    duration = travel_result.get('duration', '建议3-5天')
                    
                    # 首先使用MCP工具获取实时旅游数据
                    mcp_tools = travel_result.get('mcp_config', {})
                    mcp_data = {}
                    
                    logger.info(f"🗺️ 开始调用MCP工具获取实时数据 - 工具: {list(mcp_tools.keys())}")
                    
                    # 调用真实MCP工具获取实时数据
                    try:
                        # 导入真实MCP客户端
                        from src.tools.real_mcp_client import call_real_mcp_tools
                        
                        # 调用真实MCP工具
                        mcp_data = await call_real_mcp_tools(
                            tools_config=mcp_tools,
                            destination=destination,
                            departure=departure,
                            travel_result=travel_result
                        )
                        
                        logger.info(f"✅ 真实MCP数据获取完成: {list(mcp_data.keys())}")
                        for tool, data in mcp_data.items():
                            if isinstance(data, dict) and 'error' not in data:
                                logger.info(f"✅ {tool}数据获取成功: {len(str(data))} 字符")
                            else:
                                logger.warning(f"⚠️ {tool}数据获取失败或包含错误，将使用千问大模型生成基础旅游信息")
                                if isinstance(data, dict) and 'error_details' in data:
                                    error_details = data['error_details']
                                    if not error_details.get('api_key_configured', True):
                                        logger.warning(f"🔧 建议: 请在config/mcp.json中配置{tool.upper()}_API_KEY")
                            
                    except Exception as mcp_error:
                        logger.warning(f"⚠️ 真实MCP工具调用失败: {mcp_error}")
                        # 降级到基本信息
                        mcp_data = {
                            'error': f'MCP工具调用失败: {str(mcp_error)}',
                            'fallback_note': '已降级到基本旅游信息服务'
                        }
                    

                    
                    # 调用LLM生成详细的旅游规划，结合MCP数据
                    from src.llm.llm import get_llm_by_type
                    
                    mcp_info = ""
                    if mcp_data:
                        mcp_info = f"""

**📊 已获取的实时数据参考：**
"""
                        for tool, data in mcp_data.items():
                            if isinstance(data, dict) and 'error' not in data:
                                tool_name = {'amap': '🗺️ 高德地图'}.get(tool, tool)
                                mcp_info += f"\n**{tool_name}数据：**\n"
                                for key, value in data.items():
                                    mcp_info += f"- {value}\n"
                            elif isinstance(data, dict) and 'error' in data:
                                mcp_info += f"\n• {tool}服务暂不可用\n"
                    
                    planning_prompt = f"""
请为用户生成一份详细的旅游规划，要求如下：

**基本信息：**
- 出发地：{departure or '未指定'}
- 目的地：{destination}
- 旅游类型：{travel_type}
- 预计天数：{duration}
- 预算：{travel_result.get('budget_range', '未指定')}

{mcp_info}

**要求：**
1. 生成具体的每日行程安排
2. 推荐主要景点和特色体验（结合实时数据）
3. 提供详细交通建议（包括具体路线和价格）
4. 推荐具体的住宿和餐厅（包括名称和地址）
5. 特色美食推荐（结合当地实时评价）
6. 详细的预算估算（分项列出）
7. 最佳旅游时间建议
8. 实用贴士和注意事项

请生成专业、实用、详细的旅游规划内容，格式为markdown，内容要丰富实用，优先使用获取到的实时数据。
"""
 
                    try:
                        logger.info(f"🤖 开始调用LLM生成详细旅游规划 - 目的地: {destination}")
                        llm = get_llm_by_type("reasoning")
                        logger.info(f"🤖 LLM实例创建成功: {type(llm)}")
                        
                        # 使用同步调用，因为有些LLM可能不支持异步
                        planning_response = llm.invoke([{"role": "user", "content": planning_prompt}])
                        logger.info(f"🤖 LLM响应成功，内容长度: {len(planning_response.content)}")
                        
                        comprehensive_result = f"""
# 🧳 {destination}旅游详细规划

## 📋 规划信息
- **目的地**: {destination}
- **出发地**: {departure or '根据您的位置'}
- **旅游类型**: {travel_type}
- **规划日期**: {datetime.now().strftime('%Y-%m-%d')}

---

{planning_response.content}

---

**本旅游规划由Cooragent智能旅游规划系统生成**  
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                        logger.info(f"🎉 详细旅游规划生成成功，总长度: {len(comprehensive_result)}")
                        
                        # 直接存储结果到任务状态中
                        task.travel_result = comprehensive_result
                        
                    except Exception as llm_error:
                        logger.error(f"❌ LLM调用失败，使用基础模板: {llm_error}")
                        logger.error(f"错误类型: {type(llm_error).__name__}")
                        import traceback
                        logger.error(f"详细错误: {traceback.format_exc()}")
                        
                        # 降级到基础规划模板
                        comprehensive_result = f"""
# 🧳 {destination}旅游规划

## 📋 基本信息
- **目的地**: {destination}
- **出发地**: {departure or '待确定'}
- **旅游类型**: {travel_type}

## 🎯 规划建议

### 🚗 交通方式
- 根据距离选择合适的交通工具
- 建议提前预订机票/火车票以获得更好的价格

### 🏨 住宿建议
- 选择市中心或交通便利的区域
- 可考虑特色民宿体验当地文化

### 🎪 主要景点
- 建议游览{destination}的标志性景点
- 体验当地特色文化和自然风光

### 🍜 美食推荐
- 品尝{destination}特色美食
- 探索当地人推荐的餐厅

### 💰 预算参考
- 根据旅游天数和消费水平制定合理预算
- 建议预留应急资金

### ⚠️ 注意事项
- 关注当地天气变化
- 了解当地文化习俗
- 确保旅行证件齐全

---

**本旅游规划由Cooragent智能旅游规划系统生成**  
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*如需更详细的个性化规划，请提供更多具体信息（如旅行时间、人数、预算、特殊需求等）*
"""
                        # 直接存储结果到任务状态中
                        task.travel_result = comprehensive_result
                
                else:
                    # 容错处理：即使没有详细数据也提供基本响应
                    logger.warning("⚠️ 未获取到travel_result数据，使用基本模板")
                    await update_progress(
                        "生成基础旅游规划...", 
                        70, 
                        "基础规划处理", 
                        "使用默认模板生成旅游规划"
                    )
                    
                    # 提供基本的旅游规划结果
                    fallback_result = f"""
# 🧳 基础旅游规划

## 📋 规划概述
- **任务ID**: {task_id}
- **状态**: 已接收旅游规划请求
- **处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 规划说明
您的旅游规划请求已被系统接收并处理。虽然详细的上下文数据暂时不可用，但系统已成功识别这是一个旅游相关的任务。

## 📝 下一步建议
1. 系统已启用旅游专用智能体流程
2. 如需更详细的规划，请重新提交包含具体信息的请求
3. 建议提供：出发地、目的地、旅行天数、预算范围等信息

## 🛠️ 技术状态
- ✅ 旅游意图识别成功
- ✅ 路由到专业规划流程
- ⚠️ 上下文数据待完善

---

**本旅游规划由Cooragent旅游智能体系统自动生成**  
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
状态: ✅ 基础处理完成
"""
                    task.travel_result = fallback_result
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
    <!-- Markdown渲染支持 -->
    <script src="https://cdn.jsdelivr.net/npm/marked@5.1.1/marked.min.js"></script>
    <!-- Mermaid流程图支持 -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.2.4/dist/mermaid.min.js"></script>
    <!-- highlight.js代码高亮 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <!-- GitHub风格的markdown CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .result-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
        .progress-bar { transition: width 0.3s ease; }
        
        /* 自定义markdown样式 */
        .markdown-body {
            box-sizing: border-box;
            min-width: 200px;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            background-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        
        /* 表格样式增强 */
        .markdown-body table {
            border-collapse: collapse;
            margin: 1em 0;
            width: 100%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .markdown-body th,
        .markdown-body td {
            border: 1px solid #d0d7de;
            padding: 8px 12px;
            text-align: left;
        }
        
        .markdown-body th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        
        .markdown-body tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        /* 代码块样式 */
        .markdown-body pre {
            background-color: #f6f8fa;
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 1em 0;
        }
        
        .markdown-body code {
            background-color: rgba(175, 184, 193, 0.2);
            padding: 2px 4px;
            border-radius: 3px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
        }
        
        /* Mermaid图表容器 */
        .mermaid {
            text-align: center;
            margin: 20px 0;
        }
        
        /* 引用块样式 */
        .markdown-body blockquote {
            border-left: 4px solid #d0d7de;
            padding: 0 1em;
            color: #656d76;
            margin: 1em 0;
            background-color: #f6f8fa;
            border-radius: 0 6px 6px 0;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .markdown-body {
                padding: 15px;
                font-size: 14px;
            }
            
            .markdown-body table {
                font-size: 12px;
            }
            
            .markdown-body th,
            .markdown-body td {
                padding: 6px 8px;
            }
        }
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
                    <div id="resultContent" class="markdown-body"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE_URL = window.location.origin;
        let currentTaskId = null;
        let originalMarkdownContent = ''; // 保存原始markdown内容

        document.addEventListener('DOMContentLoaded', function() {
            // 初始化日期
            const today = new Date(); 
            const tomorrow = new Date(today); 
            tomorrow.setDate(tomorrow.getDate() + 1);
            document.getElementById('startDate').valueAsDate = today; 
            document.getElementById('endDate').valueAsDate = tomorrow;
            
            // 初始化Mermaid配置
            if (typeof mermaid !== 'undefined') {
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    themeVariables: {
                        primaryColor: '#667eea',
                        primaryTextColor: '#333',
                        primaryBorderColor: '#764ba2',
                        lineColor: '#666',
                        secondaryColor: '#f6f8fa',
                        tertiaryColor: '#fff'
                    },
                    securityLevel: 'loose',
                    flowchart: {
                        htmlLabels: true,
                        curve: 'basis'
                    }
                });
                console.log('✅ Mermaid初始化完成');
            }
            
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
                        
                        // 处理旅游规划结果
                        if (data.travel_result) {
                            console.log('✅ 获取到旅游规划结果:', data.travel_result.substring(0, 200) + '...');
                            setTimeout(() => { 
                                showResult(data.travel_result);  // 显示旅游规划内容
                                hideProgress(); 
                            }, 1000);
                        } else {
                            // 如果没有旅游规划结果，说明是代码生成任务，需要下载文件
                            try {
                                const downloadResponse = await fetch(`${API_BASE_URL}/api/generate/${taskId}/download`);
                                if (downloadResponse.ok) {
                                    const contentType = downloadResponse.headers.get('content-type');
                                    if (contentType && contentType.includes('application/json')) {
                                        // 处理JSON响应（旅游规划）
                                        const jsonResult = await downloadResponse.json();
                                        console.log('✅ 获取到旅游规划结果 (JSON):', jsonResult.content.substring(0, 200) + '...');
                                        setTimeout(() => { 
                                            showResult(jsonResult.content);  // 显示旅游规划内容
                                            hideProgress(); 
                                        }, 1000);
                                    } else {
                                        // 处理文本响应（代码生成）
                                        const actualResult = await downloadResponse.text();
                                        console.log('✅ 获取到代码生成结果:', actualResult.substring(0, 200) + '...');
                                        setTimeout(() => { 
                                            showResult(actualResult);  // 显示代码生成结果
                                            hideProgress(); 
                                        }, 1000);
                                    }
                                } else {
                                    const errorText = await downloadResponse.text();
                                    throw new Error(`服务器错误 (${downloadResponse.status}): ${errorText}`);
                                }
                            } catch (error) {
                                console.error('❌ 获取结果失败:', error);
                                hideProgress();
                                showResult(`
                                    <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px; background-color: #ffebee;">
                                        <h3>❌ 获取结果失败</h3>
                                        <p><strong>错误详情:</strong> ${error.message}</p>
                                        <p>请检查后端服务状态，或查看浏览器控制台获取更多信息。</p>
                                    </div>
                                `);
                            }
                        }
                    } else if (data.status === 'failed') { 
                        clearInterval(pollInterval); 
                        hideProgress();
                        // 显示后端失败信息
                        showResult(`
                            <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px; background-color: #ffebee; margin: 20px 0;">
                                <h3>❌ 任务执行失败</h3>
                                <p><strong>错误信息:</strong> ${data.message || '未知错误'}</p>
                                <p><strong>错误详情:</strong> ${data.error_details || '无详细信息'}</p>
                                ${data.current_step ? `<p><strong>失败步骤:</strong> ${data.current_step}</p>` : ''}
                                ${data.step_details ? `<p><strong>步骤详情:</strong> ${data.step_details}</p>` : ''}
                                <p><strong>任务ID:</strong> ${taskId}</p>
                                <hr style="margin: 15px 0;">
                                <p><strong>解决建议:</strong></p>
                                <ul>
                                    <li>检查输入参数是否正确</li>
                                    <li>尝试简化查询内容</li>
                                    <li>等待一段时间后重新尝试</li>
                                    <li>如问题持续，请联系技术支持并提供任务ID</li>
                                </ul>
                            </div>
                        `);
                    }
                } catch (error) { 
                    clearInterval(pollInterval); 
                    console.error('❌ 轮询状态失败:', error); 
                    hideProgress(); 
                    showResult(`
                        <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px; background-color: #ffebee; margin: 20px 0;">
                            <h3>❌ 状态查询失败</h3>
                            <p><strong>错误详情:</strong> ${error.message}</p>
                            <p><strong>可能原因:</strong></p>
                            <ul>
                                <li>网络连接中断</li>
                                <li>后端服务不可用</li>
                                <li>请求超时</li>
                            </ul>
                            <p><strong>建议操作:</strong></p>
                            <ul>
                                <li>检查网络连接</li>
                                <li>刷新页面重新尝试</li>
                                <li>检查后端服务状态</li>
                            </ul>
                        </div>
                    `);
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
            
            // 检测内容类型并进行相应的渲染
            const resultElement = document.getElementById('resultContent');
            
            if (typeof result === 'string' && result.includes('#') && !result.includes('<')) {
                // 如果是markdown格式的字符串，保存原始内容并使用marked库渲染
                console.log('🎨 检测到Markdown内容，开始渲染...');
                originalMarkdownContent = result; // 保存原始markdown内容
                
                try {
                    // 配置marked选项
                    marked.setOptions({
                        gfm: true,              // 启用GitHub风格的markdown
                        breaks: true,           // 换行符转为<br>
                        sanitize: false,        // 不清理HTML标签（谨慎使用）
                        highlight: function(code, lang) {
                            // 代码高亮
                            if (lang && hljs.getLanguage(lang)) {
                                try {
                                    return hljs.highlight(code, { language: lang }).value;
                                } catch (err) {
                                    console.warn('代码高亮失败:', err);
                                }
                            }
                            return hljs.highlightAuto(code).value;
                        }
                    });
                    
                    // 渲染markdown
                    const htmlContent = marked.parse(result);
                    resultElement.innerHTML = htmlContent;
                    
                    // 处理Mermaid图表
                    if (result.includes('```mermaid') || result.includes('graph') || result.includes('flowchart')) {
                        console.log('🔄 检测到Mermaid图表，正在初始化...');
                        setTimeout(() => {
                            mermaid.init();
                        }, 100);
                    }
                    
                    console.log('✅ Markdown渲染完成');
                    
                } catch (error) {
                    console.error('❌ Markdown渲染失败:', error);
                    // 如果渲染失败，回退到纯文本显示
                    originalMarkdownContent = result; // 即使渲染失败也保存原始内容
                    resultElement.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit; background: #f5f5f5; padding: 20px; border-radius: 8px;">${result}</pre>`;
                }
            } else {
                // 如果是HTML或其他格式，直接设置
                console.log('📄 直接显示HTML内容');
                resultElement.innerHTML = result;
            }
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
            let markdownContent = '';
            
            if (originalMarkdownContent) {
                // 如果有原始markdown内容，直接使用
                markdownContent = originalMarkdownContent;
                console.log('✅ 使用原始Markdown内容导出');
            } else {
                // 如果没有原始内容，尝试从HTML转换（备用方案）
                console.log('⚠️ 没有原始Markdown内容，尝试从HTML转换');
                const content = document.getElementById('resultContent').innerHTML;
                markdownContent = content
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
                    .replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n')
                    .replace(/<[^>]*>/g, ''); // 移除所有剩余的HTML标签
            }
            
            if (!markdownContent.trim()) {
                alert('没有可导出的内容');
                return;
            }
            
            // 创建并下载文件
            const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; 
            a.download = `旅游规划_${new Date().toISOString().split('T')[0]}.md`; 
            a.style.display = 'none';
            document.body.appendChild(a); 
            a.click(); 
            document.body.removeChild(a); 
            URL.revokeObjectURL(url);
            
            console.log('📁 Markdown文件导出完成');
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

 