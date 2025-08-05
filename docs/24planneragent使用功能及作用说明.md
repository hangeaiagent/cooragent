# Planner Agent 使用功能及作用说明

## 📋 概述

`Planner Agent`是Cooragent系统中的**智能规划器**和**任务分解器**，负责将用户需求分析转化为具体的智能体协作执行计划。它是系统的"大脑"，承担着需求理解、任务分解、智能体选择、执行规划和新智能体设计的核心职责。

---

## 🎯 核心功能

### 1. **深度需求分析 (Deep Requirements Analysis)**
Planner Agent具备强大的需求理解能力：
- **多维度分析**: 理解用户的显性需求和隐性需求
- **任务分解**: 将复杂任务拆解为可执行的子任务
- **约束识别**: 识别预算、时间、技能等限制条件
- **目标明确**: 定义清晰的成功标准和交付物

### 2. **智能体选择与匹配 (Agent Selection & Matching)**
基于现有智能体能力进行最优匹配：
- **能力评估**: 分析现有智能体的专业能力
- **适配度计算**: 评估智能体与任务的匹配程度
- **优选策略**: 选择最合适的智能体完成特定任务
- **去重优化**: 确保每个智能体(除reporter)只使用一次

### 3. **新智能体设计 (New Agent Design)**
当现有能力不足时，设计专业智能体：
- **需求识别**: 识别能力缺口和专业化需求
- **规格设计**: 定义新智能体的角色、能力、贡献
- **通用性原则**: 设计可复用的通用型智能体
- **工厂指令**: 生成agent_factory创建指令

### 4. **执行计划生成 (Execution Plan Generation)**
生成详细的步骤化执行方案：
- **步骤排序**: 合理安排任务执行顺序
- **依赖管理**: 处理任务间的前置依赖关系
- **资源分配**: 明确每个步骤的责任主体和输出
- **质量控制**: 包含必要的验证和汇总步骤

### 5. **多模式支持 (Multi-Mode Support)**
支持不同的规划模式：
- **深度思考模式**: 使用推理型LLM进行复杂分析
- **搜索增强模式**: 通过web搜索丰富规划信息
- **优化模式**: 对已有计划进行修正和优化

---

## 🏗️ 技术架构与数据结构

### 1. **核心数据结构**

#### **PlanWithAgents 接口**
```typescript
interface PlanWithAgents {
  thought: string;                    // 深度分析思路
  title: string;                     // 任务标题
  new_agents_needed: NewAgent[];     // 新智能体需求列表
  steps: Step[];                     // 执行步骤数组
}
```

#### **NewAgent 规格**
```typescript
interface NewAgent {
  name: string;                      // 智能体唯一标识 (PascalCase)
  role: string;                      // 专业角色定义
  capabilities: string;              // 核心能力描述
  contribution: string;              // 独特价值贡献
}
```

#### **Step 执行步骤**
```typescript
interface Step {
  agent_name: string;                // 执行智能体名称
  title: string;                     // 步骤标题
  description: string;               // 详细描述和期望输出
  note?: string;                     // 特殊注意事项
}
```

### 2. **提示词架构**

#### **主要提示词文件**
- **`planner.md`**: 通用规划器提示词
- **`agent_factory_planner.md`**: 智能体工厂专用规划器提示词

#### **核心设计原则**
```markdown
## Agent Selection Process
1. 仔细分析用户需求，理解任务本质
2. 多智能体可选时，选择最合适的直接智能体
3. 评估现有团队的能力匹配度
4. 不足时设计新的专业化智能体 (限一个)
5. 提供详细的新智能体规格说明

## Plan Generation Standards
- 首先重述需求并表达规划思路 (thought)
- 确保每个智能体能完成完整任务 (无会话连续性)
- 评估可用智能体；不足时描述新智能体需求
- 除reporter外，其他智能体只能使用一次
- 必须使用reporter作为最后汇总步骤
- 使用同用户输入一致的语言
```

---

## 🔍 代码实现分析

### 1. **主要实现文件**

#### **src/workflow/coor_task.py** (完整版规划器)
```python
async def planner_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """Planner node that generate the full plan."""
    
    # 1. 启动和配置检查
    logger.info("Planner generating full plan in %s mode", state["workflow_mode"])
    
    # 2. 模式选择和LLM配置
    messages = apply_prompt_template("planner", state)
    llm = get_llm_by_type(AGENT_LLM_MAP["planner"])  # "reasoning"
    
    # 3. 深度思考模式
    if state.get("deep_thinking_mode"):
        llm = get_llm_by_type("reasoning")
        
    # 4. 搜索增强模式
    if state.get("search_before_planning"):
        searched_content = tavily_tool.invoke({"query": user_query})
        # 将搜索结果注入消息上下文
        
    # 5. 计划生成和解析
    try:
        response = await llm.ainvoke(messages)
        content = clean_response_tags(response.content)
        
        # 6. JSON格式验证
        plan_data = json.loads(content)
        
        # 7. 步骤解析和缓存
        if "steps" in plan_data:
            cache.set_steps(state["workflow_id"], plan_data["steps"])
            
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        goto = "__end__"
    
    return Command(
        update={"full_plan": content, "agent_name": "planner"},
        goto="publisher"
    )
```

**完整版特色功能**:
- ✅ **丰富的中文日志记录**: 覆盖规划全流程
- ✅ **多模式支持**: 深度思考 + 搜索增强
- ✅ **优化模式支持**: 支持计划修正和优化
- ✅ **工作流缓存**: 步骤信息持久化
- ✅ **错误处理**: 完善的异常处理机制

#### **src/workflow/agent_factory.py** (智能体工厂规划器)
```python
async def planner_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """Planner node that generate the full plan."""
    
    # 使用专用的agent_factory_planner提示词
    messages = apply_prompt_template("agent_factory_planner", state)
    llm = get_llm_by_type(AGENT_LLM_MAP["planner"])
    
    # 搜索增强支持
    if state.get("search_before_planning"):
        searched_content = await tavily_tool.ainvoke({"query": state["messages"][-1]["content"]})
        # 搜索结果整合到消息中
    
    try:
        response = await llm.ainvoke(messages)
        content = clean_response_tags(response.content)
        json.loads(content)  # 验证JSON格式
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        goto = "__end__"
    
    return Command(
        update={"full_plan": content, "agent_name": "planner"},
        goto="publisher"
    )
```

**智能体工厂版特色**:
- ✅ **专业化提示词**: 使用`agent_factory_planner.md`
- ✅ **通用性强调**: 专注于设计可复用智能体
- ✅ **严格格式控制**: 强制JSON输出验证
- ✅ **语言一致性**: 严格的多语言输出控制

### 2. **配置与集成**

#### **LLM类型配置**
```python
# src/llm/agents.py
AGENT_LLM_MAP: dict[str, LLMType] = {
    "planner": "reasoning",  # 使用推理型LLM
    "coordinator": "basic",
    # ...
}
```

#### **工作流集成**
```python
# src/workflow/coor_task.py
workflow.add_node("planner", planner_node)

# 工作流路由
coordinator → planner → publisher → agent_proxy → reporter
```

---

## 🎯 在项目中的使用情况

### 1. **核心工作流场景**

#### **Agent Workflow (智能体协作工作流)**
```
用户输入 → Coordinator(分类) → Planner(规划) → Publisher(分发) → Agent Proxy(执行) → Reporter(汇总)
```
**使用文件**: `src/workflow/coor_task.py`
**特点**: 完整的需求分析和多智能体协作规划

#### **Agent Factory Workflow (智能体工厂工作流)**
```
需求输入 → Coordinator → Planner(设计) → Publisher → Agent Factory(创建)
```
**使用文件**: `src/workflow/agent_factory.py`
**特点**: 专注于新智能体的设计和创建

### 2. **调用统计与分布**

根据代码搜索结果，planner在以下模块中被广泛使用：
- **核心工作流**: `src/workflow/coor_task.py`, `src/workflow/agent_factory.py`
- **动态注册**: `src/workflow/dynamic.py`
- **模板定义**: `src/workflow/template.py`
- **工作流配置**: `config/workflow.json`
- **接口定义**: `src/interface/agent.py`
- **工具名映射**: `src/utils/chinese_names.py`

### 3. **性能特性**

#### **强化功能**
- **深度思考模式**: 复杂任务自动启用推理型LLM
- **搜索增强**: 规划前自动获取相关信息
- **计划缓存**: 执行步骤持久化存储
- **错误恢复**: JSON解析失败时优雅降级

#### **约束限制**
- **智能体使用限制**: 除reporter外每个智能体只能用一次
- **语言一致性**: 严格保持与用户输入语言一致
- **输出格式**: 必须生成有效的JSON格式计划
- **报告强制**: 必须以reporter作为最后汇总步骤

---

## 🎨 旅游智能体定制方案

### 1. **需求分析：旅游规划的特殊性**

#### **旅游规划核心特征**
- **多维度约束**: 预算、时间、偏好、天气、季节
- **地理空间优化**: 路线规划、交通衔接、住宿位置
- **动态信息依赖**: 实时价格、天气、可用性
- **个性化程度高**: 兴趣偏好、体验需求、舒适度

#### **现有系统挑战**
- **通用性限制**: 现有planner缺乏旅游专业知识
- **工具选择**: 无法智能选择地图、预订、天气等专业工具
- **优化算法**: 缺乏路线优化和成本效益分析能力

### 2. **定制Strategy A: 创建专用Travel Planner**

#### **创建travel_planner.md**
```markdown
---
CURRENT_TIME: <<CURRENT_TIME>>
---

# TRAVEL PLANNING SPECIALIST

You are a professional travel planning agent with deep expertise in itinerary optimization, destination analysis, and travel logistics coordination.

## Core Travel Planning Capabilities

### 1. Destination Analysis
- Research attractions, activities, and local experiences
- Analyze seasonal factors, weather patterns, and optimal timing
- Evaluate cultural significance and traveler reviews
- Assess accessibility and transportation options

### 2. Budget & Cost Optimization
- Calculate comprehensive trip costs (transport, accommodation, food, activities)
- Identify cost-saving opportunities and deals
- Balance budget constraints with experience quality
- Provide alternative options for different budget levels

### 3. Itinerary Optimization
- Optimize geographical routing to minimize travel time
- Balance must-see attractions with discovery opportunities  
- Account for rest periods and meal times
- Consider crowd patterns and peak hours

### 4. Logistics Coordination
- Coordinate transportation between destinations
- Ensure smooth hotel check-in/check-out timing
- Plan for contingencies and backup options
- Integrate booking requirements and lead times

## Travel Agent Selection Process

1. **Specialized Travel Agents Priority**: Always prefer travel-specific agents when available
2. **Geographic Expertise**: Prioritize agents with local destination knowledge
3. **Service Integration**: Select agents that can handle end-to-end travel services
4. **Real-time Capability**: Choose agents with access to live pricing and availability

## Available Travel Team
<<TEAM_MEMBERS_DESCRIPTION>>

## Travel Plan Generation Standards

- **Geographic Logic**: Organize itinerary by logical geographic flow
- **Time Optimization**: Account for transportation time, queues, business hours
- **Budget Tracking**: Provide detailed cost breakdown and running totals
- **Contingency Planning**: Include weather alternatives and backup plans
- **Cultural Sensitivity**: Respect local customs and etiquette
- **Safety Considerations**: Include emergency contacts and safety tips

## Output Format for Travel Plans

Output JSON format with travel-optimized structure:

```ts
interface TravelPlan {
  thought: string;                    // 旅游规划思路分析
  title: string;                     // 行程标题
  destination_analysis: string;       // 目的地深度分析
  budget_breakdown: BudgetItem[];     // 预算明细
  new_agents_needed: TravelAgent[];   // 专业旅游智能体需求
  itinerary_steps: TravelStep[];      // 优化后的行程步骤
}

interface TravelAgent {
  name: string;                      // 如"LocalGuide", "HotelBooker"
  specialization: string;            // 专业领域
  coverage_area: string;             // 服务区域
  required_tools: string[];          // 必需的旅游工具
}

interface TravelStep {
  day: number;
  time_slot: string;
  activity: string;
  location: string;
  duration: string;
  cost_estimate: number;
  booking_required: boolean;
  notes: string;
}
```

## Travel-Specific Constraints

- **Seasonal Awareness**: Consider weather, peak seasons, local holidays
- **Transportation Logic**: Ensure efficient routing and timing
- **Booking Dependencies**: Account for advance booking requirements
- **Local Integration**: Include local transportation and dining options
- **Emergency Planning**: Provide contingency plans for weather/closures
```

#### **实现专用travel_planner节点**
```python
# src/workflow/travel_planner.py
async def travel_planner_node(state: State) -> Command[Literal["travel_publisher", "__end__"]]:
    """专用旅游规划器节点"""
    
    # 旅游规划启动日志
    travel_start_log = generate_chinese_log(
        "travel_planner_start",
        "🗺️ 旅游规划器启动，开始分析旅游需求并生成专业行程",
        destination=extract_destination(state.get("USER_QUERY", "")),
        budget=extract_budget(state.get("USER_QUERY", "")),
        duration=extract_duration(state.get("USER_QUERY", "")),
        travel_preferences=extract_travel_preferences(state.get("USER_QUERY", ""))
    )
    logger.info(f"中文日志: {travel_start_log['data']['message']}")

    # 使用旅游专用提示词
    messages = apply_prompt_template("travel_planner", state)
    
    # 使用推理型LLM增强旅游分析能力
    llm = get_llm_by_type("reasoning")
    
    # 旅游信息增强搜索
    if state.get("search_before_planning", True):  # 旅游规划默认启用搜索
        destination = extract_destination(state.get("USER_QUERY", ""))
        travel_query = f"{destination} 旅游攻略 景点推荐 交通住宿"
        
        search_log = generate_chinese_log(
            "travel_search_enhancement",
            f"🔍 正在搜索{destination}的旅游信息以增强规划质量",
            search_query=travel_query,
            search_type="travel_enhancement"
        )
        logger.info(f"中文日志: {search_log['data']['message']}")
        
        travel_info = await tavily_tool.ainvoke({"query": travel_query})
        
        # 整合旅游信息到规划上下文
        travel_context = format_travel_search_results(travel_info)
        enhanced_messages = deepcopy(messages)
        enhanced_messages[-1]["content"] += f"\n\n# 旅游信息增强\n\n{travel_context}"
        messages = enhanced_messages

    try:
        # 旅游规划生成
        response = await llm.ainvoke(messages)
        content = clean_response_tags(response.content)
        
        # 验证旅游计划格式
        travel_plan = json.loads(content)
        validate_travel_plan(travel_plan)  # 旅游计划专用验证
        
        # 旅游规划成功日志
        plan_success_log = generate_chinese_log(
            "travel_plan_generated",
            f"✅ 旅游计划生成成功，包含{len(travel_plan.get('itinerary_steps', []))}个行程步骤",
            itinerary_days=max([step.get('day', 1) for step in travel_plan.get('itinerary_steps', [])], default=1),
            total_budget=sum([step.get('cost_estimate', 0) for step in travel_plan.get('itinerary_steps', [])]),
            new_agents_count=len(travel_plan.get('new_agents_needed', []))
        )
        logger.info(f"中文日志: {plan_success_log['data']['message']}")
        
    except json.JSONDecodeError as e:
        logger.error(f"旅游规划JSON解析失败: {e}")
        goto = "__end__"
    except Exception as e:
        logger.error(f"旅游规划生成错误: {e}")
        goto = "__end__"

    return Command(
        update={
            "messages": [{"content": content, "tool": "travel_planner", "role": "assistant"}],
            "agent_name": "travel_planner",
            "full_plan": content,
            "travel_context": extract_travel_context(state, travel_plan)
        },
        goto="travel_publisher"
    )

def extract_destination(query: str) -> str:
    """从用户查询中提取目的地信息"""
    # 使用正则或NLP技术提取地名
    pass

def extract_budget(query: str) -> Optional[int]:
    """从用户查询中提取预算信息"""
    # 提取数字和货币信息
    pass

def extract_duration(query: str) -> Optional[int]:
    """从用户查询中提取旅行天数"""
    # 提取时间相关信息
    pass

def validate_travel_plan(plan: dict) -> bool:
    """验证旅游计划的完整性和合理性"""
    required_fields = ["thought", "title", "destination_analysis", "itinerary_steps"]
    for field in required_fields:
        if field not in plan:
            raise ValueError(f"旅游计划缺少必需字段: {field}")
    
    # 验证行程步骤的逻辑性
    steps = plan.get("itinerary_steps", [])
    if not steps:
        raise ValueError("旅游计划必须包含具体的行程步骤")
    
    return True
```

### 3. **定制Strategy B: 增强现有Planner**

#### **扩展planner.md增加旅游专业知识**
```markdown
# ENHANCED TRAVEL PLANNING CAPABILITIES

## Travel Domain Expertise
When analyzing travel-related requests, apply specialized travel planning logic:

### Travel Task Classification
1. **Simple Travel Info**: Basic destination facts, weather queries, visa requirements
2. **Complex Travel Planning**: Multi-day itineraries, budget optimization, logistics coordination
3. **Specialized Travel Services**: Booking assistance, local guide services, emergency support

### Travel Agent Selection Priority
When travel-related tasks are detected:
1. **Prioritize Existing Travel Agents**: Check for TravelPlanner, LocalGuide, HotelBooker
2. **Geographic Specialization**: Prefer agents with destination-specific knowledge
3. **Service Integration**: Select agents that handle end-to-end travel services
4. **Tool Compatibility**: Ensure agents have access to maps, booking, weather tools

### Travel Plan Generation Standards
- **Geographic Flow**: Organize activities by logical location sequence
- **Time Optimization**: Account for transportation, queues, business hours
- **Budget Management**: Provide detailed cost breakdown and alternatives
- **Weather Contingency**: Include backup plans for weather disruptions
- **Cultural Integration**: Respect local customs and peak times
- **Safety Planning**: Include emergency contacts and safety considerations

### Travel-Specific New Agent Design
When designing travel agents, ensure:
- **Location Agnostic**: Design for any destination worldwide
- **Service Integration**: Capable of handling multiple travel services
- **Real-time Capability**: Access to live pricing and availability
- **Cultural Awareness**: Understanding of local customs and practices

### Enhanced Travel Examples:

**Input**: "计划3天北京游，预算3000元，喜欢历史文化"
**Analysis**: 
- Destination: 北京 (Beijing)
- Duration: 3天 (3 days)  
- Budget: 3000元 (3000 RMB)
- Preference: 历史文化 (Historical & Cultural)
- Task Type: Complex Travel Planning

**Output**: Generate TravelPlanner agent with:
- Beijing historical site expertise
- Budget optimization for 3000 RMB
- Cultural experience integration
- 3-day itinerary structuring
```

#### **旅游规划增强函数**
```python
# src/workflow/travel_enhanced_planner.py
def enhance_planner_for_travel(state: State) -> State:
    """为旅游任务增强规划器能力"""
    
    if is_travel_related(state.get("USER_QUERY", "")):
        # 注入旅游专业上下文
        travel_context = {
            "travel_mode": True,
            "destination": extract_destination(state.get("USER_QUERY", "")),
            "travel_type": classify_travel_type(state.get("USER_QUERY", "")),
            "budget_range": extract_budget_range(state.get("USER_QUERY", "")),
            "duration": extract_duration(state.get("USER_QUERY", "")),
            "preferences": extract_preferences(state.get("USER_QUERY", ""))
        }
        
        # 增强团队成员描述
        enhanced_team = add_travel_agent_descriptions(state.get("TEAM_MEMBERS", ""))
        
        # 增强工具描述
        enhanced_tools = add_travel_tool_descriptions(state.get("TOOLS", ""))
        
        state.update({
            "travel_context": travel_context,
            "TEAM_MEMBERS": enhanced_team,
            "TOOLS": enhanced_tools,
            "search_before_planning": True  # 旅游任务默认启用搜索
        })
    
    return state

def is_travel_related(query: str) -> bool:
    """判断是否为旅游相关查询"""
    travel_keywords = [
        "旅游", "旅行", "行程", "景点", "酒店", "机票", "攻略",
        "travel", "trip", "itinerary", "destination", "hotel", "flight"
    ]
    return any(keyword in query.lower() for keyword in travel_keywords)

async def travel_aware_planner_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """旅游感知的增强规划器节点"""
    
    # 旅游任务检测和增强
    if is_travel_related(state.get("USER_QUERY", "")):
        state = enhance_planner_for_travel(state)
        
        # 记录旅游增强日志
        travel_enhancement_log = generate_chinese_log(
            "planner_travel_enhancement",
            "🧳 检测到旅游任务，启用旅游专业增强模式",
            travel_destination=state["travel_context"].get("destination"),
            travel_type=state["travel_context"].get("travel_type"),
            enhanced_capabilities=["地理优化", "预算管理", "实时信息", "文化整合"]
        )
        logger.info(f"中文日志: {travel_enhancement_log['data']['message']}")
    
    # 调用增强后的标准规划流程
    return await planner_node(state)
```

### 4. **旅游工具链集成**

#### **专业旅游工具配置**
```python
# src/tools/travel_toolkit.py
TRAVEL_SPECIALIZED_TOOLS = {
    "geographic_tools": [
        "maps_direction_transit_integrated",  # 综合交通规划
        "maps_distance",                      # 距离计算
        "maps_geo",                          # 地理编码
        "maps_places_search"                 # 地点搜索
    ],
    "booking_tools": [
        "searchFlightItineraries",           # 航班搜索
        "hotel_search_and_booking",          # 酒店预订
        "restaurant_reservations",           # 餐厅预订
        "attraction_ticket_booking"          # 景点门票
    ],
    "information_tools": [
        "weather_forecast_travel",           # 旅游天气
        "currency_converter",                # 汇率转换
        "visa_requirements_check",           # 签证查询
        "local_events_finder",               # 当地活动
        "safety_advisory_check"              # 安全建议
    ],
    "optimization_tools": [
        "route_optimizer",                   # 路线优化
        "budget_calculator",                 # 预算计算
        "time_slot_optimizer",               # 时间安排优化
        "crowd_forecast"                     # 人流预测
    ]
}

def get_travel_tools_for_task(travel_type: str, destination: str) -> List[str]:
    """根据旅游任务类型和目的地选择合适的工具"""
    
    base_tools = TRAVEL_SPECIALIZED_TOOLS["geographic_tools"]
    
    if travel_type == "cultural_tourism":
        base_tools.extend([
            "local_events_finder",
            "attraction_ticket_booking", 
            "cultural_guide_service"
        ])
    elif travel_type == "adventure_tourism":
        base_tools.extend([
            "weather_forecast_travel",
            "safety_advisory_check",
            "outdoor_activity_booking"
        ])
    elif travel_type == "business_travel":
        base_tools.extend([
            "hotel_search_and_booking",
            "searchFlightItineraries",
            "conference_venue_finder"
        ])
    
    # 根据目的地添加特定工具
    if is_international_destination(destination):
        base_tools.extend([
            "visa_requirements_check",
            "currency_converter",
            "international_sim_card"
        ])
    
    return base_tools
```

### 5. **实现示例：完整旅游规划工作流**

#### **创建travel_workflow.py**
```python
# src/workflow/travel_workflow.py
from typing import Literal
from src.interface.agent import State
from langgraph.types import Command

async def travel_coordinator_node(state: State) -> Command[Literal["travel_planner", "__end__"]]:
    """旅游专用协调器"""
    
    messages = apply_prompt_template("travel_coordinator", state)
    response = await get_llm_by_type("reasoning").ainvoke(messages)
    content = clean_response_tags(response.content)
    
    if "travel_planning_needed" in content:
        goto = "travel_planner"
    else:
        goto = "__end__"
    
    return Command(goto=goto, ...)

async def travel_planner_node(state: State) -> Command[Literal["travel_publisher", "__end__"]]:
    """旅游专用规划器"""
    
    # 注入旅游上下文增强
    state = enhance_planner_for_travel(state)
    
    # 使用旅游专用提示词和推理LLM
    messages = apply_prompt_template("travel_planner", state)
    llm = get_llm_by_type("reasoning")
    
    # 旅游信息搜索增强
    if state.get("search_before_planning", True):
        travel_info = await gather_travel_information(state)
        messages = inject_travel_context(messages, travel_info)
    
    # 生成旅游计划
    response = await llm.ainvoke(messages)
    content = clean_response_tags(response.content)
    
    # 旅游计划验证和优化
    travel_plan = json.loads(content)
    optimized_plan = optimize_travel_plan(travel_plan, state)
    
    return Command(
        update={
            "full_plan": json.dumps(optimized_plan),
            "travel_context": extract_travel_context(state, optimized_plan)
        },
        goto="travel_publisher"
    )

async def travel_publisher_node(state: State) -> Command:
    """旅游任务分发器"""
    
    plan = json.loads(state["full_plan"])
    steps = plan.get("itinerary_steps", [])
    
    # 根据旅游步骤特点进行智能分发
    current_step = get_current_travel_step(state, steps)
    
    if current_step["type"] == "booking":
        next_agent = "travel_booker"
    elif current_step["type"] == "navigation":
        next_agent = "travel_navigator" 
    elif current_step["type"] == "local_guide":
        next_agent = "local_guide"
    else:
        next_agent = "travel_executor"
    
    return Command(goto=next_agent, ...)

def build_travel_workflow():
    """构建完整的旅游工作流"""
    workflow = AgentWorkflow()
    
    # 旅游专用节点链
    workflow.add_node("travel_coordinator", travel_coordinator_node)
    workflow.add_node("travel_planner", travel_planner_node)
    workflow.add_node("travel_publisher", travel_publisher_node)
    workflow.add_node("travel_booker", travel_booker_node)
    workflow.add_node("travel_navigator", travel_navigator_node)
    workflow.add_node("local_guide", local_guide_node)
    workflow.add_node("travel_reporter", travel_reporter_node)
    
    # 旅游专用路由逻辑
    workflow.set_start("travel_coordinator")
    workflow.add_conditional_edge("travel_coordinator", travel_coordinator_router)
    workflow.add_conditional_edge("travel_planner", travel_planner_router)
    workflow.add_conditional_edge("travel_publisher", travel_publisher_router)
    
    return workflow.compile()
```

---

## 🛠️ 最佳实践与优化建议

### 1. **Planner设计最佳实践**

#### **提示词设计原则**
```markdown
# 高质量Planner提示词设计要点

## 1. 结构化思维引导
- 明确分析步骤：需求理解 → 能力评估 → 设计决策 → 计划生成
- 提供决策框架：何时复用现有智能体 vs 何时设计新智能体
- 包含验证检查：计划合理性、资源可行性、时间逻辑

## 2. 领域专业知识注入
- 行业最佳实践：旅游行程优化、项目管理标准
- 约束条件处理：预算、时间、技能、资源限制
- 质量标准定义：成功标准、交付要求、验收条件

## 3. 输出格式严格控制
- JSON Schema定义：确保结构化输出
- 必需字段验证：防止关键信息缺失
- 数据类型检查：确保类型一致性

## 4. 错误处理和容错设计
- 输入异常处理：不完整或模糊的需求
- 输出格式错误：JSON解析失败的降级策略
- 逻辑冲突检测：不可行计划的识别和修正
```

#### **性能优化策略**
```python
# Planner性能优化技术

# 1. 智能缓存策略
@lru_cache(maxsize=500)
def get_agent_capabilities_summary(team_members: str) -> str:
    """缓存智能体能力摘要，避免重复解析"""
    return parse_and_summarize_capabilities(team_members)

# 2. 分层规划策略
async def hierarchical_planning(complex_task: str) -> PlanWithAgents:
    """对复杂任务进行分层规划"""
    
    # 第一层：高级任务分解
    high_level_plan = await generate_high_level_plan(complex_task)
    
    # 第二层：详细步骤规划
    detailed_steps = []
    for high_level_step in high_level_plan.steps:
        detailed_sub_steps = await generate_detailed_steps(high_level_step)
        detailed_steps.extend(detailed_sub_steps)
    
    return PlanWithAgents(
        thought=high_level_plan.thought,
        title=high_level_plan.title,
        new_agents_needed=high_level_plan.new_agents_needed,
        steps=detailed_steps
    )

# 3. 增量规划优化
async def incremental_planning_optimization(initial_plan: PlanWithAgents, feedback: str) -> PlanWithAgents:
    """基于反馈进行增量优化"""
    
    optimization_prompt = f"""
    Original Plan: {initial_plan}
    Feedback: {feedback}
    
    Please optimize the plan based on the feedback while maintaining core objectives.
    """
    
    optimized_plan = await llm.ainvoke(optimization_prompt)
    return optimized_plan

# 4. 并行能力评估
async def parallel_agent_evaluation(task: str, available_agents: List[Agent]) -> List[AgentMatch]:
    """并行评估多个智能体的任务匹配度"""
    
    evaluation_tasks = [
        evaluate_agent_task_match(agent, task) 
        for agent in available_agents
    ]
    
    match_scores = await asyncio.gather(*evaluation_tasks)
    return sorted(match_scores, key=lambda x: x.score, reverse=True)
```

### 2. **领域定制指南**

#### **垂直领域Planner定制框架**
```python
# 通用领域定制框架
class DomainSpecificPlanner:
    """领域专用规划器基类"""
    
    def __init__(self, domain: str, domain_knowledge: DomainKnowledge):
        self.domain = domain
        self.domain_knowledge = domain_knowledge
        self.specialized_prompt = self.load_domain_prompt()
        self.domain_tools = self.load_domain_tools()
        self.domain_agents = self.load_domain_agents()
    
    async def domain_aware_planning(self, state: State) -> Command:
        """领域感知的规划处理"""
        
        # 1. 领域任务检测
        is_domain_task = self.detect_domain_task(state.get("USER_QUERY", ""))
        
        if is_domain_task:
            # 2. 注入领域知识
            state = self.inject_domain_knowledge(state)
            
            # 3. 增强领域工具
            state = self.enhance_domain_tools(state)
            
            # 4. 使用专业提示词
            messages = apply_prompt_template(self.specialized_prompt, state)
            
            # 5. 领域优化的LLM配置
            llm = self.get_domain_optimized_llm()
            
        else:
            # 使用通用规划流程
            messages = apply_prompt_template("planner", state)
            llm = get_llm_by_type(AGENT_LLM_MAP["planner"])
        
        # 执行规划
        response = await llm.ainvoke(messages)
        content = clean_response_tags(response.content)
        
        # 领域特定验证
        if is_domain_task:
            content = self.validate_domain_plan(content)
        
        return Command(
            update={"full_plan": content, "agent_name": f"{self.domain}_planner"},
            goto="publisher"
        )

# 旅游领域规划器实现
class TravelPlanner(DomainSpecificPlanner):
    """旅游专用规划器"""
    
    def __init__(self):
        super().__init__(
            domain="travel",
            domain_knowledge=TravelKnowledge()
        )
    
    def detect_domain_task(self, query: str) -> bool:
        travel_indicators = ["旅游", "旅行", "行程", "景点", "酒店", "机票"]
        return any(indicator in query for indicator in travel_indicators)
    
    def inject_domain_knowledge(self, state: State) -> State:
        travel_context = {
            "seasonal_factors": self.domain_knowledge.get_seasonal_info(),
            "popular_destinations": self.domain_knowledge.get_destinations(),
            "travel_constraints": self.domain_knowledge.get_constraints(),
            "optimization_priorities": ["cost", "time", "experience", "safety"]
        }
        state["travel_context"] = travel_context
        return state
    
    def validate_domain_plan(self, plan_content: str) -> str:
        """验证旅游计划的专业性"""
        plan = json.loads(plan_content)
        
        # 检查地理逻辑
        if not self.validate_geographic_flow(plan.get("steps", [])):
            raise ValueError("行程地理流程不合理")
        
        # 检查时间安排
        if not self.validate_time_allocation(plan.get("steps", [])):
            raise ValueError("时间安排不现实")
        
        # 检查预算合理性
        if not self.validate_budget_logic(plan.get("steps", [])):
            raise ValueError("预算分配不合理")
        
        return plan_content

# 医疗领域规划器实现
class MedicalPlanner(DomainSpecificPlanner):
    """医疗专用规划器"""
    
    def detect_domain_task(self, query: str) -> bool:
        medical_indicators = ["诊断", "治疗", "医疗", "健康", "症状", "药物"]
        return any(indicator in query for indicator in medical_indicators)
    
    def get_domain_optimized_llm(self):
        # 医疗领域需要更高精度的reasoning LLM
        return get_llm_by_type("reasoning_pro")

# 教育领域规划器实现  
class EducationPlanner(DomainSpecificPlanner):
    """教育专用规划器"""
    
    def detect_domain_task(self, query: str) -> bool:
        education_indicators = ["学习", "教学", "课程", "培训", "考试", "作业"]
        return any(indicator in query for indicator in education_indicators)
```

### 3. **质量控制与监控**

#### **规划质量评估系统**
```python
# 规划质量评估框架
class PlanQualityAssessment:
    """规划质量评估系统"""
    
    def __init__(self):
        self.metrics = {
            "completeness": CompletennessMetric(),
            "feasibility": FeasibilityMetric(), 
            "efficiency": EfficiencyMetric(),
            "coherence": CoherenceMetric()
        }
    
    async def assess_plan_quality(self, plan: PlanWithAgents, context: State) -> QualityReport:
        """综合评估规划质量"""
        
        results = {}
        for metric_name, metric in self.metrics.items():
            score = await metric.evaluate(plan, context)
            results[metric_name] = score
        
        overall_score = self.calculate_overall_score(results)
        suggestions = self.generate_improvement_suggestions(results)
        
        return QualityReport(
            overall_score=overall_score,
            metric_scores=results,
            suggestions=suggestions,
            approval_status=overall_score >= 0.8
        )

class CompletennessMetric:
    """完整性评估"""
    
    async def evaluate(self, plan: PlanWithAgents, context: State) -> float:
        required_elements = ["thought", "title", "steps"]
        missing_elements = [elem for elem in required_elements if not plan.get(elem)]
        
        # 步骤完整性检查
        steps = plan.get("steps", [])
        has_reporter = any(step["agent_name"] == "reporter" for step in steps)
        
        completeness_score = 1.0
        completeness_score -= len(missing_elements) * 0.2
        if not has_reporter:
            completeness_score -= 0.3
        
        return max(0.0, completeness_score)

class FeasibilityMetric:
    """可行性评估"""
    
    async def evaluate(self, plan: PlanWithAgents, context: State) -> float:
        steps = plan.get("steps", [])
        available_agents = context.get("TEAM_MEMBERS", "")
        
        # 检查智能体可用性
        agent_usage = {}
        for step in steps:
            agent_name = step["agent_name"]
            agent_usage[agent_name] = agent_usage.get(agent_name, 0) + 1
        
        # 除reporter外，其他智能体只能使用一次
        violations = 0
        for agent, count in agent_usage.items():
            if agent != "reporter" and count > 1:
                violations += 1
        
        feasibility_score = 1.0 - (violations * 0.25)
        return max(0.0, feasibility_score)

# 实时监控系统
class PlannerMonitoringSystem:
    """规划器监控系统"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_system = AlertSystem()
        self.performance_tracker = PerformanceTracker()
    
    async def monitor_planning_session(self, session_id: str, state: State) -> None:
        """监控规划会话"""
        
        start_time = time.time()
        
        try:
            # 记录规划开始
            self.metrics_collector.record_planning_start(session_id, state)
            
            # 执行规划
            result = await planner_node(state)
            
            # 记录规划完成
            duration = time.time() - start_time
            self.metrics_collector.record_planning_complete(
                session_id, result, duration
            )
            
            # 质量评估
            if result.get("full_plan"):
                plan = json.loads(result["full_plan"])
                quality_report = await self.assess_plan_quality(plan, state)
                
                # 低质量规划告警
                if quality_report.overall_score < 0.6:
                    await self.alert_system.send_low_quality_alert(
                        session_id, quality_report
                    )
            
        except Exception as e:
            # 记录规划错误
            self.metrics_collector.record_planning_error(session_id, str(e))
            await self.alert_system.send_error_alert(session_id, e)
    
    def get_performance_dashboard(self) -> Dict:
        """获取性能仪表板数据"""
        return {
            "success_rate": self.performance_tracker.get_success_rate(),
            "avg_planning_time": self.performance_tracker.get_avg_duration(),
            "quality_trends": self.performance_tracker.get_quality_trends(),
            "error_patterns": self.performance_tracker.get_error_patterns()
        }
```

---

## 📊 总结

### 核心价值
1. **智能规划**: 将自然语言需求转化为结构化执行计划
2. **资源优化**: 智能选择和组合现有智能体资源
3. **动态扩展**: 识别能力缺口并设计新智能体
4. **质量保证**: 多维度验证和优化规划方案

### 旅游定制要点
1. **领域专业化**: 创建travel_planner.md和专用节点
2. **地理智能**: 整合地图、交通、位置优化能力
3. **动态信息**: 结合实时价格、天气、可用性
4. **体验优化**: 平衡成本、时间、体验质量

### 技术特性
- **异步规划**: 支持高并发的规划请求
- **多模式支持**: 深度思考+搜索增强+优化模式
- **格式严控**: JSON Schema确保输出一致性
- **质量监控**: 实时评估和持续优化

### 扩展能力
- **垂直领域**: 支持医疗、教育、金融等专业规划
- **国际化**: 多语言和跨文化规划支持
- **智能优化**: 机器学习驱动的规划改进
- **协作规划**: 多规划器协作处理复杂任务

Planner Agent作为Cooragent系统的"智慧中枢"，其设计质量直接决定了整个多智能体协作的效率和成功率。通过专业化定制和持续优化，可以显著提升特定领域的智能服务水平。 