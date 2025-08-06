"""
旅游计划数据接口定义

定义旅游规划相关的数据结构和接口。
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class TravelContext(BaseModel):
    """旅游上下文信息"""
    departure: Optional[str] = Field(None, description="出发地")
    destination: Optional[str] = Field(None, description="目的地")
    duration: Optional[int] = Field(None, description="旅行天数")
    budget_range: Optional[int] = Field(None, description="预算范围")
    travel_type: str = Field("general", description="旅游类型")
    complexity: str = Field("simple", description="规划复杂度")
    preferences: List[str] = Field(default_factory=list, description="旅游偏好")
    group_size: int = Field(1, description="团队人数")
    travel_dates: Optional[str] = Field(None, description="旅行日期")

class BudgetCategory(BaseModel):
    """预算分类"""
    amount: int = Field(description="金额")
    percentage: str = Field(description="占比")

class BudgetAnalysis(BaseModel):
    """预算分析结果"""
    total_budget: Union[int, str] = Field(description="总预算")
    categories: Dict[str, BudgetCategory] = Field(description="分类预算")
    recommendations: List[str] = Field(default_factory=list, description="预算建议")
    budget_level: Optional[str] = Field(None, description="预算等级")

class TravelStep(BaseModel):
    """旅游步骤"""
    agent_name: str = Field(description="执行智能体名称")
    title: str = Field(description="步骤标题")
    description: str = Field(description="详细描述")
    note: Optional[str] = Field(None, description="特殊注意事项")
    estimated_duration: Optional[str] = Field(None, description="预计耗时")
    location: Optional[str] = Field(None, description="地点")
    cost_estimate: Optional[int] = Field(None, description="费用估算")

class TravelAgent(BaseModel):
    """旅游智能体定义"""
    name: str = Field(description="智能体名称")
    role: str = Field(description="角色定义")
    capabilities: str = Field(description="核心能力")
    contribution: str = Field(description="独特价值贡献")
    specialization: Optional[str] = Field(None, description="专业领域")
    coverage_area: Optional[str] = Field(None, description="服务区域")

class ValidationResult(BaseModel):
    """验证结果"""
    valid: bool = Field(description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    suggestions: List[str] = Field(default_factory=list, description="建议信息")

class TravelInsights(BaseModel):
    """旅游洞察"""
    seasonal_advice: str = Field("", description="季节性建议")
    budget_tips: List[str] = Field(default_factory=list, description="预算建议")
    cultural_notes: List[str] = Field(default_factory=list, description="文化注意事项")
    practical_tips: List[str] = Field(default_factory=list, description="实用建议")

class TravelPlan(BaseModel):
    """旅游计划"""
    thought: str = Field(description="规划思路分析")
    title: str = Field(description="旅游计划标题")
    new_agents_needed: List[TravelAgent] = Field(default_factory=list, description="需要的新智能体")
    steps: List[TravelStep] = Field(description="执行步骤")
    travel_context: Optional[TravelContext] = Field(None, description="旅游上下文")
    budget_breakdown: Optional[BudgetAnalysis] = Field(None, description="预算分析")
    validation_result: Optional[ValidationResult] = Field(None, description="验证结果")
    insights: Optional[TravelInsights] = Field(None, description="旅游洞察")

class TravelPlanningRequest(BaseModel):
    """旅游规划请求"""
    user_query: str = Field(description="用户查询")
    user_id: str = Field(description="用户ID")
    workflow_mode: str = Field("launch", description="工作流模式")
    search_before_planning: bool = Field(True, description="规划前搜索")
    deep_thinking_mode: bool = Field(False, description="深度思考模式")

class TravelPlanningResponse(BaseModel):
    """旅游规划响应"""
    status: str = Field(description="状态")
    travel_plan: Optional[TravelPlan] = Field(None, description="旅游计划")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间")
    recommended_agents: List[str] = Field(default_factory=list, description="推荐智能体")

# 旅游类型枚举
TRAVEL_TYPES = {
    "cultural": "文化旅游",
    "leisure": "休闲度假", 
    "adventure": "探险旅游",
    "business": "商务出行",
    "family": "亲子旅游",
    "food": "美食之旅",
    "shopping": "购物旅游",
    "photography": "摄影旅游",
    "romantic": "浪漫之旅",
    "general": "普通旅游"
}

# 复杂度级别
COMPLEXITY_LEVELS = {
    "simple": "简单查询",
    "complex": "复杂规划",
    "comprehensive": "综合规划"
}

# 预算等级
BUDGET_LEVELS = {
    "economy": "经济型",
    "moderate": "中等",
    "luxury": "豪华型"
}

def create_travel_context(user_query: str) -> TravelContext:
    """从用户查询创建旅游上下文"""
    from src.utils.travel_intelligence import extract_travel_context
    
    context_data = extract_travel_context(user_query)
    return TravelContext(**context_data)

def validate_travel_plan_data(plan_data: Dict[str, Any]) -> ValidationResult:
    """验证旅游计划数据"""
    from src.utils.travel_intelligence import validate_travel_plan
    
    # 创建模拟的旅游上下文
    context = {}
    validation_data = validate_travel_plan(plan_data, context)
    return ValidationResult(**validation_data) 