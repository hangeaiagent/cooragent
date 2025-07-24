"""
中文日志支持工具

提供智能体中文名称映射和中文日志生成功能
"""

from datetime import datetime
from typing import Dict, Any, Optional


# 智能体中文名称映射
AGENT_CHINESE_NAMES = {
    "coordinator": "协调器",
    "planner": "规划器",
    "publisher": "发布器",
    "agent_factory": "智能体工厂",
    "agent_proxy": "智能体代理",
    "researcher": "研究员",
    "coder": "程序员",
    "reporter": "报告员",
    "browser": "浏览器操作员"
}

# 执行阶段中文描述
STAGE_CHINESE_DESCRIPTIONS = {
    "workflow_init": "初始化工作流",
    "team_setup": "组建智能体团队",
    "workflow_start": "启动协作流程",
    "agent_start": "智能体开始工作",
    "agent_complete": "智能体完成任务",
    "workflow_complete": "工作流执行完成",
    "error_occurred": "执行过程出现错误",
    
    # 代码生成相关阶段
    "code_generation_init": "初始化代码生成器",
    "requirement_analysis": "分析用户需求",
    "project_planning": "制定项目方案",
    "code_creation": "生成项目代码",
    "project_packaging": "打包项目文件",
    "generation_complete": "代码生成完成",
    
    # 下载相关阶段
    "download_request": "处理下载请求",
    "file_preparation": "准备下载文件",
    "download_complete": "下载完成"
}

# 执行状态中文描述
STATUS_CHINESE_DESCRIPTIONS = {
    "started": "已启动",
    "processing": "处理中", 
    "completed": "已完成",
    "failed": "执行失败",
    "skipped": "已跳过",
    "waiting": "等待中",
    "cancelled": "已取消"
}


def get_agent_chinese_name(agent_name: str) -> str:
    """获取智能体的中文名称"""
    return AGENT_CHINESE_NAMES.get(agent_name, f"智能体-{agent_name}")


def get_stage_description(stage: str) -> str:
    """获取阶段中文描述"""
    return STAGE_CHINESE_DESCRIPTIONS.get(stage, stage)


def get_execution_status_chinese(status: str) -> str:
    """获取执行状态的中文描述"""
    return STATUS_CHINESE_DESCRIPTIONS.get(status, status)


def generate_chinese_log(stage: str, message: str, **details) -> Dict[str, Any]:
    """
    生成中文日志事件
    
    Args:
        stage: 执行阶段标识
        message: 中文日志消息
        **details: 详细信息字典
        
    Returns:
        格式化的中文日志事件字典
    """
    return {
        "event": "chinese_log",
        "data": {
            "stage": stage,
            "stage_description": get_stage_description(stage),
            "message": message,
            "details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }


def format_agent_progress_log(agent_name: str, action: str, details: Optional[Dict] = None) -> str:
    """
    格式化智能体进度日志消息
    
    Args:
        agent_name: 智能体名称
        action: 动作描述 (start, complete, error等)
        details: 额外详细信息
        
    Returns:
        格式化的中文日志消息
    """
    chinese_name = get_agent_chinese_name(agent_name)
    
    action_emojis = {
        "start": "🚀",
        "processing": "⚙️", 
        "complete": "✅",
        "error": "❌",
        "analyzing": "🔍",
        "creating": "🏗️",
        "planning": "📋"
    }
    
    emoji = action_emojis.get(action, "🔄")
    
    if action == "start":
        return f"{emoji} 启动{chinese_name}"
    elif action == "complete":
        return f"{emoji} {chinese_name}完成任务"
    elif action == "processing":
        return f"{emoji} {chinese_name}正在处理中..."
    elif action == "error":
        error_msg = details.get("error", "未知错误") if details else "未知错误"
        return f"{emoji} {chinese_name}执行失败: {error_msg}"
    elif action == "analyzing":
        return f"{emoji} {chinese_name}正在分析中..."
    elif action == "creating":
        return f"{emoji} {chinese_name}正在创建中..."
    elif action == "planning":
        return f"{emoji} {chinese_name}正在制定方案..."
    else:
        return f"{emoji} {chinese_name}: {action}"


def format_code_generation_log(stage: str, progress: int, details: Optional[Dict] = None) -> str:
    """
    格式化代码生成进度日志消息
    
    Args:
        stage: 生成阶段
        progress: 进度百分比
        details: 详细信息
        
    Returns:
        格式化的中文日志消息
    """
    stage_messages = {
        "init": "🔧 正在初始化代码生成环境...",
        "analysis": "🧠 正在分析用户需求和智能体配置...",
        "workflow": "🤖 正在调用Cooragent工作流系统...",
        "planning": "📋 正在制定项目架构方案...",
        "code_creation": "💻 正在生成项目代码文件...",
        "component_copy": "📦 正在复制Cooragent核心组件...",
        "config_generation": "⚙️ 正在生成配置文件...",
        "packaging": "📦 正在打包项目文件...",
        "compression": "🗜️ 正在压缩项目代码...",
        "complete": "🎉 代码生成完成！"
    }
    
    base_msg = stage_messages.get(stage, f"🔄 正在执行 {stage}...")
    
    if details:
        if "agents_count" in details:
            base_msg += f" (智能体数量: {details['agents_count']})"
        if "tools_count" in details:
            base_msg += f" (工具数量: {details['tools_count']})"
        if "project_name" in details:
            base_msg += f" (项目: {details['project_name']})"
            
    return f"[{progress}%] {base_msg}"


def format_download_log(action: str, details: Optional[Dict] = None) -> str:
    """
    格式化下载相关日志消息
    
    Args:
        action: 下载动作
        details: 详细信息
        
    Returns:
        格式化的中文日志消息
    """
    action_messages = {
        "request": "📥 接收到代码下载请求",
        "validation": "🔍 正在验证下载文件...",
        "preparation": "📁 正在准备下载文件...",
        "start": "⬇️ 开始下载文件...",
        "complete": "✅ 文件下载完成",
        "error": "❌ 下载失败"
    }
    
    base_msg = action_messages.get(action, f"🔄 {action}")
    
    if details:
        if "file_name" in details:
            base_msg += f" ({details['file_name']})"
        if "file_size" in details:
            size_mb = details['file_size'] / (1024 * 1024)
            base_msg += f" ({size_mb:.1f}MB)"
        if "task_id" in details:
            base_msg += f" [任务ID: {details['task_id'][:8]}]"
            
    return base_msg 