# Agent Factory 智能体工厂详细分析说明

## 📋 概述

`Agent Factory`是Cooragent系统中的**智能体动态创建引擎**，负责根据用户需求分析和生成专业化智能体。它是系统**自适应扩展能力**的核心组件，能够在运行时动态创建新的智能体来满足特定领域或复杂任务的需求。

---

## 🎯 核心功能与职责

### 1. **需求分析与智能体设计 (Requirement Analysis & Agent Design)**
- **领域识别**: 分析用户需求，识别所需的专业领域和能力
- **架构设计**: 基于需求设计智能体的角色、能力和工具配置
- **通用性保证**: 确保创建的智能体具有可重用性和通用性
- **配置生成**: 生成完整的智能体JSON配置

### 2. **工具链智能选择 (Intelligent Tool Selection)**
- **需求匹配**: 根据智能体能力需求选择合适的工具
- **权限控制**: 确保只选择必要且可用的工具
- **MCP集成**: 支持选择和集成MCP协议工具
- **工具验证**: 验证选定工具的可用性和兼容性

### 3. **提示词工程 (Prompt Engineering)**
- **专业化设计**: 为每个智能体创建专业化的提示词模板
- **行为规范**: 定义智能体的工作流程和行为准则
- **语言一致性**: 确保提示词语言与用户输入语言一致
- **最佳实践**: 整合领域最佳实践到提示词中

### 4. **LLM类型适配 (LLM Type Adaptation)**
- **任务复杂度评估**: 根据任务复杂度选择合适的LLM类型
- **性能优化**: 为不同类型任务选择最优的模型配置
- **多模态支持**: 支持文本、代码、推理、视觉等不同模态的LLM
- **成本效益**: 在性能和成本之间找到最佳平衡

### 5. **智能体注册与集成 (Agent Registration & Integration)**
- **动态注册**: 将新创建的智能体注册到系统中
- **配置持久化**: 将智能体配置保存到store目录
- **团队集成**: 将新智能体集成到现有的团队协作体系
- **版本管理**: 支持智能体的版本控制和更新

---

## 🏗️ 代码结构与实现分析

### 1. **核心实现文件结构**

#### **src/prompts/agent_factory.md** - 智能体创建指令
```markdown
# Role: Agent Builder
You are `AgentFactory`, a master AI agent builder.

# PRIMARY DIRECTIVE
Your SOLE purpose is to generate a complete JSON configuration for a NEW agent 
based on specifications found in the user's input.

# CRITICAL RULES
1. DO NOT USE YOUR OWN NAME: agent_name MUST NOT be "agent_factory"
2. SOURCE OF TRUTH: agent_name MUST match the name in [new_agents_needed:]
3. NO yfinance TOOL: Strictly forbidden from selecting yfinance tool
4. TOOL SELECTION IS CRITICAL: Only select DIRECTLY ESSENTIAL tools

# Core Workflow
1. Identify Task from User Input
2. Formulate Thought
3. Determine LLM Type
4. Select Necessary Tools
5. Construct Agent's Prompt
6. Generate Final JSON Output

# Output Format
interface AgentBuilder {
  agent_name: string;
  agent_description: string;
  thought: string;
  llm_type: string;
  selected_tools: Tool[];
  prompt: string;
}
```

#### **src/prompts/agent_factory_planner.md** - 智能体规划指令
```markdown
# Role: AI Agent Architect
You are a top-tier AI Agent Architect, specializing in designing highly modular, 
reusable, and general-purpose agents.

# Design Philosophy
- Generality and Reusability: Every agent must be general-purpose
- Parameter-driven: Specific details are runtime parameters, not core definition
- Language Consistency: Match user's input language

# Workflow
1. Think & Analyze: Identify capability gap
2. Evaluate Existing Team: Check if existing agents suffice
3. Design New Agent: Create general-purpose agent if needed
4. Generate Execution Plan: Create agent_factory step

# Output Format
{
  "thought": "Analysis and reasoning",
  "new_agents_needed": [...],
  "steps": [{"agent_name": "agent_factory", ...}]
}
```

### 2. **主要实现文件**

#### **src/workflow/coor_task.py: agent_factory_node()** (主工作流实现)
```python
async def agent_factory_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """智能体工厂节点 - 主工作流版本"""
    
    # === 第一阶段：初始化和日志记录 ===
    logger.info("Agent Factory Start to work in %s workmode", state["workflow_mode"])
    
    factory_start_log = generate_chinese_log(
        "agent_factory_start",
        "🏭 智能体工厂启动，开始分析智能体创建需求",
        workflow_mode=state["workflow_mode"],
        user_id=state.get("user_id", "unknown"),
        workflow_id=state.get("workflow_id", "unknown")
    )
    
    # === 第二阶段：状态管理和提示词应用 ===
    if state["workflow_mode"] == "launch":
        # 恢复系统节点状态
        cache.restore_system_node(state["workflow_id"], AGENT_FACTORY, state["user_id"])
        
        # 应用智能体工厂提示词模板
        messages = apply_prompt_template("agent_factory", state)
        
        # === 第三阶段：LLM调用和智能体规格生成 ===
        agent_spec = await (
            get_llm_by_type(AGENT_LLM_MAP["agent_factory"])  # "basic"
            .with_structured_output(AgentBuilder)
            .ainvoke(messages)
        )
        
        # === 第四阶段：工具验证和选择 ===
        tools = []
        validated_tools = []
        
        for tool in agent_spec["selected_tools"]:
            if agent_manager.available_tools.get(tool["name"]):
                tools.append(agent_manager.available_tools[tool["name"]])
                validated_tools.append(tool["name"])
            else:
                logger.warning("Tool (%s) is not available", tool["name"])
        
        # === 第五阶段：智能体创建和注册 ===
        await agent_manager._create_agent_by_prebuilt(
            user_id=state["user_id"],
            name=agent_spec["agent_name"],
            nick_name=agent_spec["agent_name"],
            llm_type=agent_spec["llm_type"],
            tools=tools,
            prompt=agent_spec["prompt"],
            description=agent_spec["agent_description"],
        )
        
        # === 第六阶段：团队更新和状态返回 ===
        state["TEAM_MEMBERS"].append(agent_spec["agent_name"])
        
        return Command(
            update={
                "messages": [{
                    "content": f"New agent {agent_spec['agent_name']} created successfully.",
                    "tool": "agent_factory",
                    "role": "assistant",
                }],
                "new_agent_name": agent_spec["agent_name"],
                "agent_name": "agent_factory",
            },
            goto="publisher",
        )
    else:
        # 非launch模式处理逻辑
        return Command(goto="publisher", update={"agent_name": "agent_factory"})
```

#### **src/workflow/agent_factory.py: agent_factory_node()** (简化工作流实现)
```python
async def agent_factory_node(state: State) -> Command[Literal["publisher", "__end__"]]:
    """智能体工厂节点 - 简化版本（专用于agent_factory工作流）"""
    
    # 1. 直接应用提示词模板
    messages = apply_prompt_template("agent_factory", state)
    
    # 2. 调用LLM生成智能体规格
    agent_spec = await (
        get_llm_by_type(AGENT_LLM_MAP["agent_factory"])
        .with_structured_output(AgentBuilder)
        .ainvoke(messages)
    )
    
    # 3. 工具验证和选择
    tools = []
    for tool in agent_spec["selected_tools"]:
        if agent_manager.available_tools.get(tool["name"]):
            tools.append(agent_manager.available_tools[tool["name"]])
        else:
            logger.warning("Tool (%s) is not available", tool["name"])
    
    # 4. 创建智能体
    await agent_manager._create_agent_by_prebuilt(
        user_id=state["user_id"],
        name=agent_spec["agent_name"],
        nick_name=agent_spec["agent_name"],
        llm_type=agent_spec["llm_type"],
        tools=tools,
        prompt=agent_spec["prompt"],
        description=agent_spec["agent_description"],
    )
    
    # 5. 更新团队成员并结束
    state["TEAM_MEMBERS"].append(agent_spec["agent_name"])
    
    return Command(
        update={
            "messages": [{
                "content": f"New agent {agent_spec['agent_name']} created.",
                "tool": "agent_factory",
                "role": "assistant",
            }],
            "new_agent_name": agent_spec["agent_name"],
            "agent_name": "agent_factory",
        },
        goto="__end__",  # 简化版直接结束
    )
```

### 3. **数据结构与接口定义**

#### **AgentBuilder接口** (src/interface/serializer.py)
```python
class AgentBuilder(TypedDict):
    """智能体构建器数据结构"""
    
    agent_name: str              # 智能体唯一标识名称
    agent_description: str       # 智能体功能描述 (一句话概括)
    thought: str                 # 设计思路和推理过程
    llm_type: str               # LLM类型: "basic"|"reasoning"|"vision"|"code"
    selected_tools: list[AgentTool]  # 选择的工具列表
    prompt: str                  # 智能体执行提示词

class AgentTool(TypedDict):
    """工具配置数据结构"""
    
    name: str                    # 工具名称 (必须在available_tools中存在)
    description: str             # 工具功能描述

class NewAgent(TypedDict):
    """新智能体需求描述"""
    
    name: str                    # 智能体名称 (PascalCase)
    role: str                    # 角色定义 (通用性描述)
    capabilities: list[str]      # 能力列表 (具体技能描述)
    contribution: str            # 贡献价值 (长期价值说明)
```

### 4. **工作流集成与调用链路**

#### **完整调用流程**
```python
# 1. 工作流启动判断
if task_type == TaskType.AGENT_FACTORY:
    graph = agent_factory_graph()    # 使用简化版工作流
else:
    graph = build_graph()           # 使用完整版工作流

# 2. 工作流图构建
def agent_factory_graph():
    workflow = AgentWorkflow()
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("planner", planner_node)           # 使用agent_factory_planner.md
    workflow.add_node("publisher", publisher_node)       # 专用publisher (只能选择agent_factory)
    workflow.add_node("agent_factory", agent_factory_node)
    workflow.set_start("coordinator")
    return workflow.compile()

# 3. 执行序列
"""
用户输入 → Coordinator(分析) → Planner(规划新智能体) → Publisher(调度) → Agent_Factory(创建) → 结束
                    ↓                    ↓                     ↓               ↓
              简单回复/复杂任务      生成new_agents_needed     选择agent_factory    实际创建智能体
"""
```

---

## 🔧 Agent Factory使用功能详细说明

### 1. **触发条件与使用场景**

#### **自动触发场景**
```python
# 场景1: Planner识别需要新智能体
planner_output = {
    "thought": "现有团队缺乏专业的数据分析能力",
    "new_agents_needed": [{
        "name": "DataAnalyst",
        "role": "专业数据分析师",
        "capabilities": ["数据清洗", "统计分析", "可视化"],
        "contribution": "提供专业的数据洞察能力"
    }],
    "steps": [{
        "agent_name": "agent_factory",
        "title": "创建数据分析师智能体",
        "description": "使用agent_factory创建专业的数据分析智能体"
    }]
}

# 场景2: 用户明确请求创建新智能体
user_input = "我需要一个专门处理客户服务的智能体"
# → Coordinator判断为复杂任务 → Planner设计新智能体 → Agent Factory创建
```

#### **手动触发场景**
```bash
# CLI直接调用agent_factory工作流
python cli.py run-l --task-type agent_factory --message "创建旅游规划智能体"
```

### 2. **智能体创建流程详解**

#### **第一步：需求分析与解构**
```python
def analyze_user_requirement(user_input: str) -> dict:
    """
    需求分析过程：
    1. 领域识别：旅游、金融、教育、编程等
    2. 能力需求：搜索、计算、创作、分析等
    3. 工具需求：API调用、数据处理、文件操作等
    4. 复杂度评估：简单查询 vs 复杂规划
    """
    
    analysis = {
        "domain": "travel",                    # 领域识别
        "core_capability": "itinerary_planning", # 核心能力
        "required_tools": ["maps", "weather", "booking"], # 工具需求
        "complexity": "reasoning",             # 复杂度评估
        "language": "zh-CN"                   # 语言环境
    }
    return analysis
```

#### **第二步：智能体架构设计**
```python
def design_agent_architecture(analysis: dict) -> AgentBuilder:
    """
    架构设计过程：
    1. 角色定位：明确智能体的专业身份
    2. 能力映射：将需求转化为具体能力
    3. 工具选择：选择必要且可用的工具
    4. 提示词设计：创建专业化的行为指南
    """
    
    return {
        "agent_name": "TravelPlanner",
        "agent_description": "专业的旅游行程规划智能体，提供个性化的旅游方案设计",
        "thought": "用户需要旅游规划能力，整合地图、天气、预订等多源信息...",
        "llm_type": "reasoning",               # 推理型LLM适合复杂规划
        "selected_tools": [
            {
                "name": "tavily_tool",
                "description": "搜索旅游信息和景点资料"
            },
            {
                "name": "python_repl_tool", 
                "description": "计算预算和优化行程路线"
            }
        ],
        "prompt": "# Role: 专业旅游规划师\n你是一个专业的旅游规划智能体..."
    }
```

#### **第三步：工具链验证与绑定**
```python
async def validate_and_bind_tools(selected_tools: list[AgentTool]) -> list:
    """
    工具验证过程：
    1. 可用性检查：验证工具是否在available_tools中
    2. 权限验证：确认工具使用权限
    3. 依赖检查：验证工具依赖是否满足
    4. 冲突检测：检查工具间是否存在冲突
    """
    
    validated_tools = []
    for tool_config in selected_tools:
        tool_name = tool_config["name"]
        
        # 检查工具可用性
        if tool_name in agent_manager.available_tools:
            tool_instance = agent_manager.available_tools[tool_name]
            validated_tools.append(tool_instance)
            logger.info(f"Tool {tool_name} validated and bound")
        else:
            logger.warning(f"Tool {tool_name} not available, skipping")
    
    return validated_tools
```

#### **第四步：智能体注册与持久化**
```python
async def register_and_persist_agent(agent_spec: AgentBuilder, tools: list):
    """
    注册与持久化过程：
    1. 创建Agent对象：构建完整的智能体配置
    2. 保存到store：持久化到store/agents/{name}.json
    3. 运行时注册：添加到available_agents
    4. 团队集成：更新TEAM_MEMBERS列表
    """
    
    # 创建Agent对象
    agent = Agent(
        user_id=user_id,
        agent_name=agent_spec["agent_name"],
        nick_name=agent_spec["agent_name"],
        description=agent_spec["agent_description"],
        llm_type=agent_spec["llm_type"],
        selected_tools=[Tool(name=t.name, description=t.description) for t in tools],
        prompt=agent_spec["prompt"]
    )
    
    # 持久化保存
    await agent_manager._save_agent(agent, flush=True)
    
    # 运行时注册
    agent_manager.available_agents[agent.agent_name] = agent
    
    # 团队集成
    state["TEAM_MEMBERS"].append(agent.agent_name)
```

### 3. **LLM类型选择策略**

#### **LLM类型映射表**
```python
# src/llm/agents.py: AGENT_LLM_MAP
LLM_SELECTION_STRATEGY = {
    "basic": {
        "适用场景": ["简单查询", "信息检索", "文本生成"],
        "特点": ["响应快速", "成本较低", "适合标准任务"],
        "示例智能体": ["客服助手", "信息查询员", "内容编辑"]
    },
    "reasoning": {
        "适用场景": ["复杂推理", "多步规划", "逻辑分析"],
        "特点": ["深度思考", "逻辑严密", "适合复杂任务"],
        "示例智能体": ["投资分析师", "旅游规划师", "项目经理"]
    },
    "code": {
        "适用场景": ["编程任务", "代码生成", "技术分析"],
        "特点": ["代码专精", "技术理解", "编程最佳实践"],
        "示例智能体": ["软件工程师", "数据科学家", "算法专家"]
    },
    "vision": {
        "适用场景": ["图像分析", "视觉理解", "多模态任务"],
        "特点": ["视觉感知", "图文结合", "多模态处理"],
        "示例智能体": ["图像分析师", "设计师", "医疗影像专家"]
    }
}

def select_llm_type(task_complexity: str, domain: str, capabilities: list[str]) -> str:
    """LLM类型智能选择算法"""
    
    # 代码相关任务
    if any(keyword in capabilities for keyword in ["编程", "代码", "算法", "数据分析"]):
        return "code"
    
    # 视觉相关任务
    if any(keyword in capabilities for keyword in ["图像", "视觉", "识别", "多模态"]):
        return "vision"
    
    # 复杂推理任务
    if task_complexity in ["complex", "multi-step"] or len(capabilities) > 3:
        return "reasoning"
    
    # 默认基础类型
    return "basic"
```

### 4. **错误处理与容错机制**

#### **多层次错误处理**
```python
async def agent_factory_with_error_handling(state: State):
    """带完整错误处理的agent_factory实现"""
    
    try:
        # === 提示词应用阶段 ===
        messages = apply_prompt_template("agent_factory", state)
        
        # === LLM调用阶段 ===
        agent_spec = await (
            get_llm_by_type(AGENT_LLM_MAP["agent_factory"])
            .with_structured_output(AgentBuilder)
            .ainvoke(messages)
        )
        
        # === 配置验证阶段 ===
        if not agent_spec.get("agent_name"):
            raise ValueError("Agent name is required")
        
        if agent_spec["agent_name"] == "agent_factory":
            raise ValueError("Agent name cannot be 'agent_factory'")
        
        # === 工具验证阶段 ===
        tools = []
        failed_tools = []
        
        for tool_config in agent_spec["selected_tools"]:
            if agent_manager.available_tools.get(tool_config["name"]):
                tools.append(agent_manager.available_tools[tool_config["name"]])
            else:
                failed_tools.append(tool_config["name"])
        
        if failed_tools:
            logger.warning(f"Tools not available: {failed_tools}")
        
        if not tools:
            raise ValueError("No valid tools selected for agent")
        
        # === 智能体创建阶段 ===
        await agent_manager._create_agent_by_prebuilt(
            user_id=state["user_id"],
            name=agent_spec["agent_name"],
            nick_name=agent_spec["agent_name"],
            llm_type=agent_spec["llm_type"],
            tools=tools,
            prompt=agent_spec["prompt"],
            description=agent_spec["agent_description"],
        )
        
        return create_success_response(agent_spec)
        
    except ValueError as e:
        logger.error(f"Configuration error in agent factory: {e}")
        return create_error_response(f"配置错误: {e}")
        
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        return create_error_response(f"缺少必要字段: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in agent factory: {e}")
        return create_error_response(f"智能体创建失败: {e}")

def create_success_response(agent_spec: AgentBuilder):
    """创建成功响应"""
    return Command(
        update={
            "messages": [{
                "content": f"✅ 智能体 {agent_spec['agent_name']} 创建成功!",
                "tool": "agent_factory",
                "role": "assistant",
            }],
            "new_agent_name": agent_spec["agent_name"],
            "agent_name": "agent_factory",
        },
        goto="publisher",
    )

def create_error_response(error_message: str):
    """创建错误响应"""
    return Command(
        update={
            "messages": [{
                "content": f"❌ 智能体创建失败: {error_message}",
                "tool": "agent_factory",
                "role": "assistant",
            }],
            "agent_name": "agent_factory",
            "error": error_message,
        },
        goto="__end__",
    )
```

---

## 🎯 旅游智能体定制化实现方案

### 1. **旅游领域Agent Factory增强策略**

#### **创建旅游专用Agent Factory**
```python
# src/prompts/travel_agent_factory.md
"""
---
CURRENT_TIME: <<CURRENT_TIME>>
---
# Role: 旅游智能体专家构建师

You are `TravelAgentFactory`, a specialized AI agent builder focused on creating 
sophisticated travel and tourism agents. Your expertise lies in understanding travel 
domain requirements and building agents with comprehensive travel capabilities.

# 旅游领域专业知识库
## 核心能力域
- **行程规划**: 路线优化、时间安排、景点串联
- **预算管理**: 成本控制、价格比较、优惠发现  
- **地理智能**: 地图导航、交通规划、地理约束
- **文化适应**: 本地习俗、语言支持、文化体验
- **风险管理**: 安全评估、天气应对、应急预案
- **个性化**: 偏好匹配、群体协调、特殊需求

## 专业工具生态
### 地理与导航工具
- `maps_direction_transit_integrated`: 综合交通路线规划
- `geographic_poi_search`: 地理兴趣点搜索
- `distance_time_calculator`: 距离时间计算器

### 预订与价格工具  
- `hotel_search_and_booking`: 酒店搜索预订服务
- `flight_search_comparison`: 航班搜索比价系统
- `attraction_ticket_booking`: 景点门票预订平台

### 信息与决策工具
- `weather_forecast_travel`: 旅游专用天气预报
- `local_events_finder`: 当地活动事件发现
- `currency_converter_realtime`: 实时汇率转换
- `visa_requirements_checker`: 签证要求查询

### 内容与体验工具
- `restaurant_recommendations`: 餐厅推荐系统
- `cultural_guide_generator`: 文化指南生成器
- `photo_spot_identifier`: 拍照点识别推荐

# 旅游智能体设计模式

## 模式1: 综合规划师 (Comprehensive Planner)
- **适用场景**: 完整旅行规划、多目的地行程
- **核心工具**: 地图导航 + 预订服务 + 天气信息
- **LLM类型**: reasoning (需要复杂的逻辑推理)

## 模式2: 专业顾问 (Specialized Consultant)  
- **适用场景**: 特定领域咨询(美食、文化、摄影)
- **核心工具**: 领域专用工具 + 搜索引擎
- **LLM类型**: basic (领域知识应用)

## 模式3: 实时助手 (Real-time Assistant)
- **适用场景**: 旅行中的实时支持和问题解决
- **核心工具**: 实时信息 + 应急服务 + 通讯工具
- **LLM类型**: basic (快速响应)

# 提示词模板增强
针对旅游智能体，提示词需要包含：

## 地理空间意识
"你具备强大的地理空间推理能力，能够：
- 理解地理位置关系和空间距离
- 考虑交通方式和时间成本
- 识别地理和气候约束条件"

## 文化敏感性
"你具备跨文化理解能力，能够：
- 尊重当地文化习俗和传统
- 提供文化背景和历史介绍  
- 识别和避免文化冲突"

## 预算优化思维
"你具备预算优化能力，能够：
- 在预算约束下最大化旅行体验
- 发现优惠和省钱机会
- 平衡成本与体验质量"

# 输出要求
严格按照AgentBuilder接口输出，但增加旅游专用字段：

```ts
interface TravelAgentBuilder extends AgentBuilder {
  agent_name: string;
  agent_description: string;
  thought: string;
  llm_type: "basic" | "reasoning" | "vision";
  selected_tools: TravelTool[];
  prompt: string;
  
  // 旅游专用扩展字段
  travel_domain: "planning" | "consulting" | "assistance";
  geographic_scope: "local" | "domestic" | "international";
  specialization: string[];  // ["budget", "luxury", "adventure", "culture", "family"]
  language_support: string[]; // ["zh-CN", "en-US", "ja-JP"]
}
```
"""
```

#### **旅游工具选择增强逻辑**
```python
# src/workflow/travel_agent_factory.py

TRAVEL_TOOL_CATEGORIES = {
    "geography": [
        "maps_direction_transit_integrated",
        "geographic_poi_search", 
        "distance_time_calculator",
        "elevation_terrain_analyzer"
    ],
    "booking": [
        "hotel_search_and_booking",
        "flight_search_comparison",
        "attraction_ticket_booking",
        "car_rental_service"
    ],
    "information": [
        "weather_forecast_travel",
        "local_events_finder", 
        "currency_converter_realtime",
        "visa_requirements_checker"
    ],
    "experience": [
        "restaurant_recommendations",
        "cultural_guide_generator",
        "photo_spot_identifier",
        "local_transport_guide"
    ]
}

class TravelAgentFactory:
    """旅游智能体专用工厂"""
    
    def __init__(self):
        self.tool_selector = TravelToolSelector()
        self.prompt_generator = TravelPromptGenerator()
        self.llm_optimizer = TravelLLMOptimizer()
    
    async def create_travel_agent(self, requirement: TravelAgentRequirement) -> AgentBuilder:
        """创建旅游专用智能体"""
        
        # 1. 分析旅游需求类型
        travel_type = self.analyze_travel_type(requirement)
        
        # 2. 智能选择工具组合
        selected_tools = self.tool_selector.select_optimal_tools(
            travel_type=travel_type,
            geographic_scope=requirement.geographic_scope,
            budget_level=requirement.budget_level,
            traveler_profile=requirement.traveler_profile
        )
        
        # 3. 生成专业化提示词
        prompt = self.prompt_generator.generate_travel_prompt(
            agent_role=requirement.role,
            specialization=requirement.specialization,
            cultural_context=requirement.cultural_context,
            service_level=requirement.service_level
        )
        
        # 4. 优化LLM选择
        llm_type = self.llm_optimizer.select_optimal_llm(
            complexity=requirement.task_complexity,
            real_time_needs=requirement.real_time_needs,
            reasoning_depth=requirement.reasoning_depth
        )
        
        return AgentBuilder(
            agent_name=requirement.agent_name,
            agent_description=requirement.description,
            thought=f"基于{travel_type}需求，设计专业旅游智能体，整合{len(selected_tools)}个专用工具",
            llm_type=llm_type,
            selected_tools=selected_tools,
            prompt=prompt
        )

class TravelToolSelector:
    """旅游工具智能选择器"""
    
    def select_optimal_tools(self, travel_type: str, geographic_scope: str, 
                           budget_level: str, traveler_profile: dict) -> list[AgentTool]:
        """基于需求智能选择工具组合"""
        
        tools = []
        
        # 基础工具（所有旅游智能体必备）
        tools.extend([
            AgentTool(name="tavily_tool", description="搜索旅游信息和实时资讯"),
            AgentTool(name="python_repl_tool", description="执行计算和数据分析")
        ])
        
        # 地理工具（根据地理范围选择）
        if geographic_scope in ["domestic", "international"]:
            tools.extend([
                AgentTool(name="maps_direction_transit_integrated", description="综合交通导航规划"),
                AgentTool(name="distance_time_calculator", description="距离时间计算")
            ])
        
        # 预订工具（根据预算等级选择）
        if budget_level in ["medium", "high"]:
            tools.extend([
                AgentTool(name="hotel_search_and_booking", description="酒店搜索预订"),
                AgentTool(name="flight_search_comparison", description="航班比价预订")
            ])
        
        # 专业工具（根据旅行者画像选择）
        if traveler_profile.get("food_lover"):
            tools.append(AgentTool(name="restaurant_recommendations", description="餐厅推荐"))
        
        if traveler_profile.get("culture_seeker"):
            tools.append(AgentTool(name="cultural_guide_generator", description="文化导览"))
        
        if traveler_profile.get("photographer"):
            tools.append(AgentTool(name="photo_spot_identifier", description="摄影点推荐"))
        
        return tools

class TravelPromptGenerator:
    """旅游提示词生成器"""
    
    def generate_travel_prompt(self, agent_role: str, specialization: list[str],
                             cultural_context: str, service_level: str) -> str:
        """生成旅游专用提示词"""
        
        base_prompt = f"""
# Role: {agent_role}
你是一个专业的{agent_role}，具备丰富的旅游行业经验和深厚的专业知识。

# 专业能力
你的核心专长包括：{', '.join(specialization)}

# 地理和文化意识
- **地理智能**: 你具备强大的地理空间推理能力，能够理解位置关系、交通连接和地理约束
- **文化敏感**: 你深度理解{cultural_context}的文化背景，尊重当地习俗并能提供文化洞察
- **时间管理**: 你能够合理安排行程时间，考虑交通、排队、休息等实际因素

# 服务标准
你的服务水准为{service_level}，这意味着：
- 提供详细、准确、实用的旅游建议
- 考虑用户的预算、时间、偏好等个性化需求
- 主动识别和规避潜在的旅行风险
- 提供backup方案和应急建议

# 工作流程
1. **需求分析**: 仔细分析用户的旅行需求、约束条件和偏好
2. **信息收集**: 使用搜索工具获取最新、准确的旅游信息
3. **方案设计**: 基于收集的信息设计个性化的旅行方案
4. **优化调整**: 考虑实际约束，优化方案的可行性和体验
5. **详细输出**: 提供结构化、可执行的旅行计划

# 输出格式
请始终以结构化的方式输出，包括：
- **行程概览**: 总体安排和亮点
- **详细计划**: 按天分解的具体安排
- **预算估算**: 各项费用的详细分解
- **注意事项**: 重要提醒和应急信息
- **备选方案**: 天气或其他因素的替代选择

# 质量标准
- **准确性**: 所有信息必须准确、最新
- **实用性**: 提供可实际执行的具体建议
- **个性化**: 充分考虑用户的个人情况和偏好
- **完整性**: 考虑旅行的各个方面，不遗漏重要细节
"""
        
        return base_prompt
```

### 2. **具体实现案例：创建专业旅游规划师**

#### **案例需求**
```python
# 用户需求: 创建专业的北京三日游规划智能体
user_requirement = {
    "agent_name": "BeijingTravelExpert",
    "role": "北京三日游专业规划师", 
    "capabilities": [
        "景点路线优化",
        "交通方案设计", 
        "美食推荐",
        "文化体验规划",
        "预算控制"
    ],
    "geographic_scope": "Beijing",
    "target_traveler": "文化爱好者、美食探索者",
    "budget_range": "2000-5000 RMB",
    "special_requirements": ["避开人流高峰", "包含传统文化体验"]
}
```

#### **Agent Factory生成配置**
```json
{
  "agent_name": "BeijingTravelExpert",
  "agent_description": "专业的北京文化旅游规划智能体，提供深度文化体验和美食探索的个性化三日游方案",
  "thought": "用户需要专业的北京旅游规划能力。北京作为历史文化名城，需要深度的文化理解和本地知识。考虑到用户偏好文化体验和美食，需要整合地图导航、餐厅推荐、文化导览等工具。预算控制和人流避开需要数据分析能力。",
  "llm_type": "reasoning",
  "selected_tools": [
    {
      "name": "tavily_tool",
      "description": "搜索北京最新旅游信息、活动资讯和实时状况"
    },
    {
      "name": "maps_direction_transit_integrated", 
      "description": "北京地铁、公交、步行路线综合规划"
    },
    {
      "name": "restaurant_recommendations",
      "description": "北京特色美食和餐厅推荐系统"
    },
    {
      "name": "cultural_guide_generator",
      "description": "北京历史文化景点深度导览生成"
    },
    {
      "name": "python_repl_tool",
      "description": "预算计算、路线优化和数据分析"
    },
    {
      "name": "weather_forecast_travel",
      "description": "北京天气预报，优化室内外活动安排"
    }
  ],
  "prompt": "# Role: 北京文化旅游专家\n你是一位深谙北京历史文化的专业旅游规划师，专注于为游客设计深度的文化体验和美食探索之旅。你具备丰富的北京本地知识，了解各个景点的历史背景、最佳游览时间、以及如何避开人流高峰。\n\n# 专业能力\n- **文化深度**: 深入了解北京的历史文化，能够讲述景点背后的故事\n- **路线优化**: 基于地理位置和时间安排，设计最优的游览路线\n- **美食专长**: 熟知北京传统美食和现代创新餐厅\n- **人流分析**: 掌握各景点的人流规律，帮助游客避开拥挤时段\n- **预算管理**: 精确控制旅行成本，在预算内最大化体验价值\n\n# 工作流程\n1. **需求分析**: 了解游客的时间安排、预算范围、兴趣偏好和特殊要求\n2. **信息搜集**: 查询最新的景点信息、天气状况、活动资讯\n3. **路线设计**: 使用地图工具规划最优的交通路线和时间安排\n4. **文化整合**: 为每个景点准备文化背景介绍和深度体验建议\n5. **美食规划**: 推荐沿途的特色餐厅和小吃，融入行程安排\n6. **预算优化**: 计算详细费用，提供不同价位的选择方案\n7. **应急预案**: 考虑天气等因素，准备备选方案\n\n# 输出标准\n## 行程概览\n- 三日行程主题和亮点总结\n- 每日核心体验和时间分配\n- 总体预算范围和主要支出项目\n\n## 详细计划 \n- **第一天**: 故宫、天安门广场文化深度游\n- **第二天**: 长城体验 + 胡同文化探索\n- **第三天**: 颐和园、圆明园历史文化游\n\n## 美食推荐\n- 每餐具体餐厅推荐和招牌菜\n- 特色小吃体验地点和时间\n- 预算分配和性价比分析\n\n## 文化解读\n- 每个景点的历史背景和文化意义\n- 最佳拍照点和游览顺序\n- 深度体验建议和注意事项\n\n## 实用信息\n- 详细交通路线和用时\n- 门票价格和预订建议  \n- 最佳游览时间和避峰策略\n- 天气应对和备选方案\n\n# 服务承诺\n- 提供准确、最新的旅游信息\n- 确保行程的可执行性和时间合理性\n- 在预算约束内最大化文化体验价值\n- 贴心考虑游客的体力和兴趣分布\n- 提供7x24小时可参考的详细指南"
}
```

### 3. **旅游Agent Factory完整部署方案**

#### **第一步：创建旅游专用配置**
```python
# config/travel_mcp.json - 旅游专用MCP工具配置
{
  "mcpServers": {
    "maps-service": {
      "command": "python",
      "args": ["src/tools/travel/maps_server.py"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "${GOOGLE_MAPS_API_KEY}",
        "BAIDU_MAPS_API_KEY": "${BAIDU_MAPS_API_KEY}"
      },
      "transport": "stdio"
    },
    "booking-service": {
      "command": "node", 
      "args": ["src/tools/travel/booking_server.js"],
      "env": {
        "BOOKING_API_KEY": "${BOOKING_API_KEY}",
        "AIRBNB_API_KEY": "${AIRBNB_API_KEY}"
      },
      "transport": "stdio"
    },
    "weather-service": {
      "url": "http://localhost:8081/sse",
      "transport": "sse"
    },
    "cultural-guide": {
      "command": "python",
      "args": ["src/tools/travel/cultural_server.py"],
      "env": {
        "WIKI_API_KEY": "${WIKI_API_KEY}"
      },
      "transport": "stdio"
    }
  }
}
```

#### **第二步：创建旅游工具管理器**
```python
# src/tools/travel/travel_tool_manager.py

class TravelToolManager:
    """旅游专用工具管理器"""
    
    def __init__(self):
        self.travel_tools = {}
        self.tool_categories = TRAVEL_TOOL_CATEGORIES
        
    async def load_travel_tools(self):
        """加载旅游专用工具"""
        
        # 加载MCP旅游工具
        travel_mcp_config = self._load_travel_mcp_config()
        travel_mcp_client = MultiServerMCPClient(travel_mcp_config)
        travel_mcp_tools = await travel_mcp_client.get_tools()
        
        for tool in travel_mcp_tools:
            self.travel_tools[tool.name] = tool
        
        # 集成到主工具管理器
        agent_manager.available_tools.update(self.travel_tools)
        
        logger.info(f"Loaded {len(travel_mcp_tools)} travel-specific tools")
    
    def get_tools_for_travel_type(self, travel_type: str) -> list[str]:
        """根据旅游类型获取推荐工具"""
        
        tool_recommendations = {
            "cultural_tourism": [
                "cultural_guide_generator",
                "historical_site_info", 
                "local_customs_guide"
            ],
            "adventure_tourism": [
                "weather_forecast_travel",
                "terrain_analyzer",
                "emergency_contact_service"
            ],
            "business_tourism": [
                "hotel_search_and_booking",
                "flight_search_comparison", 
                "conference_venue_finder"
            ],
            "family_tourism": [
                "family_friendly_activities",
                "restaurant_recommendations",
                "safety_zone_identifier"
            ]
        }
        
        return tool_recommendations.get(travel_type, [])
```

#### **第三步：创建旅游Agent Factory工作流**
```python
# src/workflow/travel_factory_workflow.py

def create_travel_agent_factory_graph():
    """创建旅游智能体工厂专用工作流"""
    
    workflow = AgentWorkflow()
    
    # 使用旅游专用节点
    workflow.add_node("travel_coordinator", travel_coordinator_node)
    workflow.add_node("travel_planner", travel_planner_node)  
    workflow.add_node("travel_publisher", travel_publisher_node)
    workflow.add_node("travel_agent_factory", travel_agent_factory_node)
    
    # 工作流连接
    workflow.add_edge("travel_coordinator", "travel_planner")
    workflow.add_edge("travel_planner", "travel_publisher") 
    workflow.add_edge("travel_publisher", "travel_agent_factory")
    workflow.add_edge("travel_agent_factory", "__end__")
    
    workflow.set_start("travel_coordinator")
    
    return workflow.compile()

async def travel_agent_factory_node(state: State):
    """旅游智能体工厂节点"""
    
    # 1. 应用旅游专用提示词
    messages = apply_prompt_template("travel_agent_factory", state)
    
    # 2. 使用推理型LLM（旅游规划需要复杂推理）
    agent_spec = await (
        get_llm_by_type("reasoning")
        .with_structured_output(TravelAgentBuilder)
        .ainvoke(messages)
    )
    
    # 3. 验证旅游工具可用性
    travel_tool_manager = TravelToolManager()
    verified_tools = await travel_tool_manager.verify_travel_tools(
        agent_spec["selected_tools"]
    )
    
    # 4. 创建旅游智能体
    await agent_manager._create_agent_by_prebuilt(
        user_id=state["user_id"],
        name=agent_spec["agent_name"],
        nick_name=agent_spec["agent_name"],
        llm_type=agent_spec["llm_type"],
        tools=verified_tools,
        prompt=agent_spec["prompt"],
        description=agent_spec["agent_description"],
    )
    
    # 5. 记录旅游智能体创建日志
    travel_agent_log = {
        "agent_name": agent_spec["agent_name"],
        "travel_domain": agent_spec.get("travel_domain", "general"),
        "geographic_scope": agent_spec.get("geographic_scope", "unknown"),
        "tools_count": len(verified_tools),
        "creation_time": datetime.now().isoformat()
    }
    
    logger.info(f"Travel agent created: {travel_agent_log}")
    
    return Command(
        update={
            "messages": [{
                "content": f"🌍 旅游智能体 {agent_spec['agent_name']} 创建成功！\n"
                          f"专业领域: {agent_spec.get('travel_domain', '通用旅游')}\n"
                          f"地理范围: {agent_spec.get('geographic_scope', '全球')}\n"
                          f"集成工具: {len(verified_tools)}个专业旅游工具",
                "tool": "travel_agent_factory",
                "role": "assistant",
            }],
            "new_agent_name": agent_spec["agent_name"],
            "agent_name": "travel_agent_factory",
            "travel_agent_info": travel_agent_log,
        },
        goto="__end__",
    )
```

#### **第四步：集成到主系统**
```python
# src/workflow/process.py - 修改主工作流选择逻辑

async def run_agent_workflow(
    user_id: str,
    task_type: str,
    user_input_messages: list,
    ...
):
    """扩展的工作流启动逻辑"""
    
    # 现有逻辑
    if task_type == TaskType.AGENT_FACTORY:
        graph = agent_factory_graph()
    elif task_type == TaskType.TRAVEL_AGENT_FACTORY:  # 新增
        graph = create_travel_agent_factory_graph()
    else:
        graph = build_graph()
    
    # 如果是旅游相关任务，自动切换到旅游工厂
    if is_travel_related_task(user_input_messages):
        logger.info("Detected travel-related task, switching to travel agent factory")
        graph = create_travel_agent_factory_graph()
    
    # 其余逻辑保持不变...

def is_travel_related_task(messages: list) -> bool:
    """检测是否为旅游相关任务"""
    
    travel_keywords = [
        "旅游", "旅行", "行程", "景点", "酒店", "机票", 
        "tourism", "travel", "itinerary", "hotel", "flight",
        "导游", "攻略", "路线", "预订"
    ]
    
    user_input = " ".join([msg.get("content", "") for msg in messages])
    
    return any(keyword in user_input.lower() for keyword in travel_keywords)
```

---

## 📊 总结与最佳实践

### 核心价值
1. **动态扩展**: 运行时创建专业化智能体，无需重启系统
2. **需求适配**: 根据具体需求精确设计智能体配置
3. **工具整合**: 智能选择和集成最优的工具组合
4. **质量保证**: 通过结构化输出确保配置的完整性和一致性

### Agent Factory设计要点
1. **通用性优先**: 设计可重用的通用智能体，避免一次性解决方案
2. **工具精选**: 严格选择必要工具，避免工具冗余和复杂性
3. **提示词专业化**: 为每个智能体创建专业化的行为指南
4. **错误容错**: 完善的错误处理和容错机制

### 旅游智能体定制要点
1. **领域深度**: 深入理解旅游行业的专业需求和痛点
2. **地理感知**: 强化地理空间推理和文化敏感性
3. **工具生态**: 构建完整的旅游专用工具生态系统
4. **个性化**: 支持不同类型旅行者的个性化需求

### 技术特性
- **结构化输出**: 通过TypedDict确保配置的类型安全
- **模块化设计**: 支持不同领域的专业化扩展
- **异步处理**: 高效的异步智能体创建流程
- **可观测性**: 完整的日志记录和监控机制

### 扩展能力
- **多领域支持**: 支持医疗、教育、金融等各个专业领域
- **多语言适配**: 支持不同语言环境的智能体创建
- **插件架构**: 支持第三方工具和能力的插件化集成
- **版本管理**: 支持智能体的版本控制和升级

Agent Factory作为Cooragent系统的"智能体孵化器"，其设计质量直接决定了系统的扩展能力和适应性。通过专业化的需求分析、工具选择和提示词工程，能够创建出高质量的专业智能体，为用户提供精准的领域服务。 