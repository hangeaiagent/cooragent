# Web一句话生成多智能体产品代码技术方案

## 项目概述

基于现有Cooragent系统，构建一个Web界面，让用户能够通过"一句话输入需求"完成多智能体产品代码的生成。用户输入自然语言描述后，系统自动分析、规划、创建智能体协作方案，并实时展示执行过程和结果。

## 一、现有系统分析

### 1.1 核心入口点

#### 主要代码入口
- **CLI入口**: `cli.py` - 命令行交互界面
- **Web服务入口**: `src/service/server.py::Server` - FastAPI服务类
- **工作流执行入口**: `src/workflow/process.py::run_agent_workflow()` - 核心业务逻辑
- **智能体管理入口**: `src/manager/agents.py::AgentManager` - 智能体统一管理

#### 工作流执行链路
```
用户输入 → coordinator(分类) → planner(规划) → publisher(分发) → agent_proxy(执行) → reporter(汇总)
```

### 1.2 现有API接口

基于`tests/test_app.py`分析，当前已有接口：

```typescript
// 核心工作流接口
POST /v1/workflow
{
  "user_id": string,
  "lang": "en" | "zh",
  "messages": [{"role": "user", "content": string}],
  "debug": boolean,
  "deep_thinking_mode": boolean,
  "search_before_planning": boolean,
  "task_type": "agent_workflow" | "agent_factory",
  "coor_agents": string[]
}

// 智能体管理接口
POST /v1/list_agents        // 列出用户智能体
GET  /v1/list_default_agents // 列出默认智能体
GET  /v1/list_default_tools  // 列出可用工具
POST /v1/edit_agent         // 编辑智能体
```

### 1.3 调试和跟踪机制

#### 实时监控
- **流式响应**: 支持Server-Sent Events实时推送执行状态
- **WebSocket支持**: `src/tools/websocket_manager.py`提供实时通信
- **工具追踪**: `src/service/tool_tracker.py`追踪工具使用状态
- **会话管理**: `src/service/session.py`管理用户会话

#### 调试能力
- **调试模式**: 通过`debug: true`启用详细日志
- **事件流**: 实时推送各种事件（工作流开始、智能体执行、工具使用等）
- **错误处理**: 完整的异常捕获和错误反馈机制

## 二、Web界面架构设计

### 2.1 技术栈选择

#### 前端技术栈
```typescript
核心框架: React 18 + TypeScript
状态管理: Zustand / Jotai (轻量级状态管理)
UI组件库: Ant Design / Chakra UI
实时通信: EventSource (SSE) + WebSocket
构建工具: Vite
样式方案: Tailwind CSS + CSS Modules
图表可视化: D3.js / Recharts
代码展示: Monaco Editor / Prism.js
```

#### 后端扩展
```python
Web框架: FastAPI (现有)
实时通信: WebSocket + SSE
文件服务: 静态文件托管
API文档: OpenAPI/Swagger (自动生成)
```

### 2.2 前端界面设计

#### 主界面布局
```
┌─────────────────────────────────────────────────────────┐
│                    Cooragent Web 界面                    │
├─────────────────────────────────────────────────────────┤
│  输入区域                                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  一句话描述您的需求...                            │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │    │
│  │  │ 生成代码 │ │ 高级选项 │ │ 示例模板 │          │    │
│  │  └─────────┘ └─────────┘ └─────────┘          │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  执行状态区域                                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │  🔄 智能体协作进度                                │    │
│  │  ├─ ✅ coordinator: 需求分类完成                  │    │
│  │  ├─ 🔄 planner: 正在制定执行计划...              │    │
│  │  ├─ ⏳ publisher: 等待执行                       │    │
│  │  └─ ⏳ agents: 准备就绪                          │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  结果展示区域                                            │
│  ┌─────────────┬─────────────┬─────────────┐           │
│  │ 生成的智能体 │ 执行过程日志 │ 最终报告结果 │           │
│  │            │            │            │           │
│  │ [智能体列表] │ [实时日志]  │ [Markdown]  │           │
│  │            │            │            │           │
│  └─────────────┴─────────────┴─────────────┘           │
└─────────────────────────────────────────────────────────┘
```

#### 核心功能组件

1. **智能输入组件** (`SmartInput`)
   - 支持自然语言输入
   - 实时输入建议和补全
   - 示例模板选择
   - 高级参数配置

2. **执行状态组件** (`ExecutionStatus`)
   - 实时显示工作流执行进度
   - 智能体协作可视化
   - 执行时间统计
   - 错误状态展示

3. **结果展示组件** (`ResultDisplay`)
   - 生成的智能体展示和编辑
   - 执行过程日志查看
   - 最终报告渲染
   - 代码高亮显示

4. **智能体管理组件** (`AgentManager`)
   - 智能体列表和详情
   - 智能体编辑和调试
   - 工具配置管理
   - 性能监控

### 2.3 数据流设计

#### 状态管理结构
```typescript
interface AppState {
  // 用户输入状态
  input: {
    content: string;
    options: WorkflowOptions;
    templates: Template[];
  };
  
  // 执行状态
  execution: {
    status: 'idle' | 'running' | 'completed' | 'error';
    currentStep: string;
    progress: number;
    startTime: Date;
    events: ExecutionEvent[];
  };
  
  // 结果状态
  results: {
    agents: Agent[];
    logs: LogEntry[];
    report: string;
    generatedCode: CodeFile[];
  };
  
  // UI状态
  ui: {
    activeTab: string;
    sidebarOpen: boolean;
    settingsOpen: boolean;
  };
}
```

#### 实时数据流
```typescript
// SSE事件处理
const useWorkflowExecution = () => {
  const [state, setState] = useStore();
  
  const executeWorkflow = async (input: string) => {
    const eventSource = new EventSource('/api/v1/workflow/stream');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.event) {
        case 'start_of_workflow':
          setState(prev => ({
            ...prev,
            execution: { ...prev.execution, status: 'running' }
          }));
          break;
          
        case 'start_of_agent':
          setState(prev => ({
            ...prev,
            execution: { 
              ...prev.execution, 
              currentStep: data.data.agent_name 
            }
          }));
          break;
          
        case 'messages':
          setState(prev => ({
            ...prev,
            results: {
              ...prev.results,
              logs: [...prev.results.logs, data.data]
            }
          }));
          break;
          
        case 'new_agent_created':
          setState(prev => ({
            ...prev,
            results: {
              ...prev.results,
              agents: [...prev.results.agents, data.data.agent_obj]
            }
          }));
          break;
      }
    };
  };
};
```

## 三、后端API扩展设计

### 3.1 新增API接口

基于现有`src/service/server.py`，需要新增以下接口：

```python
# src/service/app.py (新增FastAPI应用主入口)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI(title="Cooragent Web API", version="1.0.0")

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="web/dist"), name="static")

# 新增接口

@app.post("/api/v1/workflow/stream")
async def stream_workflow(request: AgentRequest):
    """流式执行工作流"""
    async def event_generator():
        async for event in Server._run_agent_workflow(request):
            yield {
                "event": "message",
                "data": json.dumps(event)
            }
    
    return EventSourceResponse(event_generator())

@app.websocket("/api/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket连接"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, user_id)

@app.get("/api/v1/templates")
async def get_templates():
    """获取示例模板"""
    return [
        {
            "id": "stock_analysis",
            "name": "股票分析智能体",
            "description": "创建股票分析专家，分析股票趋势并提供投资建议",
            "template": "创建一个股票分析专家agent，分析{stock_name}股票走势，提供买入卖出建议"
        },
        {
            "id": "travel_planner", 
            "name": "旅游规划智能体",
            "description": "创建旅游规划专家，制定详细的旅游行程",
            "template": "创建一个旅游规划专家agent，为{destination}制定{days}天的旅游行程"
        }
    ]

@app.get("/api/v1/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    return workflow_cache.get_workflow_status(workflow_id)

@app.post("/api/v1/workflow/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """取消工作流执行"""
    # 实现工作流取消逻辑
    pass

@app.get("/api/v1/agents/{agent_name}/code")
async def get_agent_code(agent_name: str):
    """获取智能体生成的代码"""
    agent = agent_manager.available_agents.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_name": agent_name,
        "prompt": agent.prompt,
        "tools": [tool.model_dump() for tool in agent.selected_tools],
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### 3.2 增强现有Server类

```python
# src/service/server.py (增强)
class Server:
    # ... 现有方法 ...
    
    @staticmethod
    async def _get_workflow_templates():
        """获取工作流模板"""
        templates_dir = get_project_root() / "templates"
        templates = []
        
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    templates.append(template)
        
        return templates
    
    @staticmethod
    async def _get_execution_metrics(workflow_id: str):
        """获取执行指标"""
        workflow = workflow_cache.get_workflow(workflow_id)
        if not workflow:
            return None
            
        return {
            "workflow_id": workflow_id,
            "total_agents": len(workflow.get("agents", [])),
            "execution_time": workflow.get("execution_time", 0),
            "success_rate": workflow.get("success_rate", 0),
            "tool_usage": workflow.get("tool_usage", {})
        }
    
    @staticmethod 
    async def _generate_workflow_report(workflow_id: str):
        """生成工作流报告"""
        workflow = workflow_cache.get_workflow(workflow_id)
        if not workflow:
            return None
            
        # 使用reporter智能体生成报告
        reporter_prompt = f"""
        基于以下工作流执行结果生成详细报告：
        
        工作流ID: {workflow_id}
        执行时间: {workflow.get('execution_time', 'Unknown')}
        创建的智能体: {len(workflow.get('agents', []))}
        执行步骤: {len(workflow.get('steps', []))}
        
        请生成包含执行摘要、关键发现、生成的智能体清单和建议改进的完整报告。
        """
        
        # 调用reporter生成报告
        from src.llm.llm import get_llm_by_type
        llm = get_llm_by_type("basic")
        response = await llm.ainvoke([{"role": "user", "content": reporter_prompt}])
        
        return response.content
```

## 四、前端实现方案

### 4.1 项目结构

```
web/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/          # 通用组件
│   │   ├── SmartInput/     # 智能输入组件
│   │   ├── ExecutionStatus/ # 执行状态组件
│   │   ├── ResultDisplay/  # 结果展示组件
│   │   └── AgentManager/   # 智能体管理组件
│   ├── hooks/              # 自定义Hooks
│   │   ├── useWorkflow.ts  # 工作流Hook
│   │   ├── useAgent.ts     # 智能体Hook
│   │   └── useWebSocket.ts # WebSocket Hook
│   ├── stores/             # 状态管理
│   │   ├── appStore.ts     # 应用状态
│   │   ├── workflowStore.ts # 工作流状态
│   │   └── agentStore.ts   # 智能体状态
│   ├── services/           # API服务
│   │   ├── api.ts          # API客户端
│   │   ├── websocket.ts    # WebSocket客户端
│   │   └── sse.ts          # SSE客户端
│   ├── types/              # 类型定义
│   │   ├── workflow.ts     # 工作流类型
│   │   ├── agent.ts        # 智能体类型
│   │   └── api.ts          # API类型
│   ├── utils/              # 工具函数
│   │   ├── formatters.ts   # 格式化工具
│   │   └── validators.ts   # 验证工具
│   ├── App.tsx             # 主应用组件
│   ├── main.tsx            # 应用入口
│   └── style.css           # 全局样式
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 4.2 核心组件实现

#### SmartInput组件
```typescript
// src/components/SmartInput/SmartInput.tsx
import React, { useState, useCallback } from 'react';
import { Input, Button, Select, Card } from 'antd';
import { useWorkflowStore } from '../../stores/workflowStore';
import { useTemplates } from '../../hooks/useTemplates';

const SmartInput: React.FC = () => {
  const [input, setInput] = useState('');
  const [options, setOptions] = useState({
    debug: false,
    deepThinking: true,
    searchBeforePlanning: false
  });
  
  const { executeWorkflow, isExecuting } = useWorkflowStore();
  const { templates, loading: templatesLoading } = useTemplates();
  
  const handleSubmit = useCallback(async () => {
    if (!input.trim()) return;
    
    await executeWorkflow({
      content: input,
      options: {
        debug: options.debug,
        deep_thinking_mode: options.deepThinking,
        search_before_planning: options.searchBeforePlanning,
        task_type: 'agent_workflow'
      }
    });
  }, [input, options, executeWorkflow]);
  
  const handleTemplateSelect = useCallback((templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setInput(template.template);
    }
  }, [templates]);
  
  return (
    <Card title="一句话生成多智能体" className="smart-input">
      <div className="input-area">
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="请描述您的需求，例如：创建一个股票分析专家，分析小米股票趋势并提供投资建议..."
          rows={4}
          maxLength={1000}
          showCount
        />
        
        <div className="controls">
          <div className="templates">
            <Select
              placeholder="选择示例模板"
              style={{ width: 200 }}
              loading={templatesLoading}
              onChange={handleTemplateSelect}
            >
              {templates.map(template => (
                <Select.Option key={template.id} value={template.id}>
                  {template.name}
                </Select.Option>
              ))}
            </Select>
          </div>
          
          <div className="options">
            {/* 高级选项配置 */}
          </div>
          
          <Button
            type="primary"
            size="large"
            loading={isExecuting}
            onClick={handleSubmit}
            disabled={!input.trim()}
          >
            生成智能体代码
          </Button>
        </div>
      </div>
    </Card>
  );
};
```

#### ExecutionStatus组件
```typescript
// src/components/ExecutionStatus/ExecutionStatus.tsx
import React from 'react';
import { Card, Progress, Steps, Tag, Timeline } from 'antd';
import { useWorkflowStore } from '../../stores/workflowStore';

const ExecutionStatus: React.FC = () => {
  const { 
    execution: { status, currentStep, progress, events, startTime },
    isExecuting 
  } = useWorkflowStore();
  
  const getStepStatus = (stepName: string) => {
    if (stepName === currentStep) return 'process';
    if (events.some(e => e.agent_name === stepName && e.event === 'completed')) {
      return 'finish';
    }
    return 'wait';
  };
  
  const steps = [
    { title: 'Coordinator', description: '需求分析和分类' },
    { title: 'Planner', description: '制定执行计划' },
    { title: 'Publisher', description: '任务分发' },
    { title: 'Agents', description: '智能体协作执行' },
    { title: 'Reporter', description: '生成最终报告' }
  ];
  
  return (
    <Card title="执行状态" className="execution-status">
      {isExecuting && (
        <div className="progress-area">
          <Progress 
            percent={progress} 
            status={status === 'error' ? 'exception' : 'active'}
            format={() => `${Math.round(progress)}%`}
          />
          <div className="current-step">
            当前执行: <Tag color="processing">{currentStep}</Tag>
          </div>
        </div>
      )}
      
      <Steps 
        direction="vertical" 
        size="small"
        items={steps.map((step, index) => ({
          ...step,
          status: getStepStatus(step.title.toLowerCase())
        }))}
      />
      
      <div className="events-timeline">
        <Timeline>
          {events.slice(-10).map((event, index) => (
            <Timeline.Item 
              key={index}
              color={event.event === 'error' ? 'red' : 'blue'}
            >
              <div className="event-content">
                <div className="event-title">{event.agent_name}</div>
                <div className="event-description">{event.description}</div>
                <div className="event-time">{new Date(event.timestamp).toLocaleTimeString()}</div>
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </div>
    </Card>
  );
};
```

#### ResultDisplay组件
```typescript
// src/components/ResultDisplay/ResultDisplay.tsx
import React, { useState } from 'react';
import { Card, Tabs, Table, Button, Modal } from 'antd';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useWorkflowStore } from '../../stores/workflowStore';
import ReactMarkdown from 'react-markdown';

const ResultDisplay: React.FC = () => {
  const { results: { agents, logs, report, generatedCode } } = useWorkflowStore();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [codeModalVisible, setCodeModalVisible] = useState(false);
  
  const agentColumns = [
    { title: '智能体名称', dataIndex: 'agent_name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description' },
    { title: 'LLM类型', dataIndex: 'llm_type', key: 'llm_type' },
    { title: '工具数量', dataIndex: 'selected_tools', key: 'tools', 
      render: (tools: any[]) => tools?.length || 0 },
    {
      title: '操作',
      key: 'action',
      render: (_, agent: Agent) => (
        <div>
          <Button 
            size="small" 
            onClick={() => {
              setSelectedAgent(agent);
              setCodeModalVisible(true);
            }}
          >
            查看代码
          </Button>
          <Button size="small" style={{ marginLeft: 8 }}>
            编辑
          </Button>
        </div>
      )
    }
  ];
  
  const tabItems = [
    {
      key: 'agents',
      label: `生成的智能体 (${agents.length})`,
      children: (
        <Table 
          dataSource={agents}
          columns={agentColumns}
          rowKey="agent_name"
          size="small"
        />
      )
    },
    {
      key: 'logs',
      label: '执行日志',
      children: (
        <div className="logs-container">
          {logs.map((log, index) => (
            <div key={index} className="log-entry">
              <span className="log-time">{log.timestamp}</span>
              <span className="log-agent">[{log.agent_name}]</span>
              <span className="log-content">{log.content}</span>
            </div>
          ))}
        </div>
      )
    },
    {
      key: 'report',
      label: '最终报告',
      children: (
        <div className="report-container">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>
      )
    }
  ];
  
  return (
    <>
      <Card title="执行结果" className="result-display">
        <Tabs items={tabItems} />
      </Card>
      
      <Modal
        title={`智能体代码: ${selectedAgent?.agent_name}`}
        open={codeModalVisible}
        onCancel={() => setCodeModalVisible(false)}
        width={800}
        footer={null}
      >
        {selectedAgent && (
          <div className="agent-code">
            <h4>提示词:</h4>
            <SyntaxHighlighter language="markdown" style={vscDarkPlus}>
              {selectedAgent.prompt}
            </SyntaxHighlighter>
            
            <h4>工具配置:</h4>
            <SyntaxHighlighter language="json" style={vscDarkPlus}>
              {JSON.stringify(selectedAgent.selected_tools, null, 2)}
            </SyntaxHighlighter>
          </div>
        )}
      </Modal>
    </>
  );
};
```

### 4.3 状态管理实现

```typescript
// src/stores/workflowStore.ts
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { api } from '../services/api';
import { SSEClient } from '../services/sse';

interface WorkflowState {
  // 执行状态
  execution: {
    status: 'idle' | 'running' | 'completed' | 'error';
    currentStep: string;
    progress: number;
    startTime: Date | null;
    events: ExecutionEvent[];
    workflowId: string | null;
  };
  
  // 结果数据
  results: {
    agents: Agent[];
    logs: LogEntry[];
    report: string;
    generatedCode: CodeFile[];
  };
  
  // 计算属性
  isExecuting: boolean;
  
  // 操作方法
  executeWorkflow: (input: WorkflowInput) => Promise<void>;
  cancelWorkflow: () => Promise<void>;
  resetResults: () => void;
}

export const useWorkflowStore = create<WorkflowState>()(
  subscribeWithSelector((set, get) => ({
    execution: {
      status: 'idle',
      currentStep: '',
      progress: 0,
      startTime: null,
      events: [],
      workflowId: null
    },
    
    results: {
      agents: [],
      logs: [],
      report: '',
      generatedCode: []
    },
    
    get isExecuting() {
      return get().execution.status === 'running';
    },
    
    executeWorkflow: async (input) => {
      const userId = 'web_user_' + Date.now();
      
      // 重置状态
      set(state => ({
        ...state,
        execution: {
          ...state.execution,
          status: 'running',
          startTime: new Date(),
          progress: 0,
          events: []
        },
        results: {
          agents: [],
          logs: [],
          report: '',
          generatedCode: []
        }
      }));
      
      try {
        // 创建SSE连接
        const sseClient = new SSEClient('/api/v1/workflow/stream');
        
        // 监听事件
        sseClient.onMessage((event) => {
          const data = JSON.parse(event.data);
          
          set(state => {
            const newState = { ...state };
            
            switch (data.event) {
              case 'start_of_workflow':
                newState.execution.workflowId = data.data.workflow_id;
                break;
                
              case 'start_of_agent':
                newState.execution.currentStep = data.data.agent_name;
                newState.execution.progress = Math.min(newState.execution.progress + 20, 90);
                break;
                
              case 'messages':
                newState.results.logs.push({
                  timestamp: new Date().toISOString(),
                  agent_name: data.agent_name,
                  content: data.data.delta.content,
                  type: 'message'
                });
                break;
                
              case 'new_agent_created':
                const agentData = JSON.parse(data.data.agent_obj);
                newState.results.agents.push(agentData);
                break;
                
              case 'workflow_completed':
                newState.execution.status = 'completed';
                newState.execution.progress = 100;
                newState.results.report = data.data.report;
                break;
                
              case 'error':
                newState.execution.status = 'error';
                break;
            }
            
            newState.execution.events.push({
              ...data,
              timestamp: new Date().toISOString()
            });
            
            return newState;
          });
        });
        
        // 发送请求
        await sseClient.connect({
          user_id: userId,
          lang: 'zh',
          messages: [{ role: 'user', content: input.content }],
          debug: input.options.debug,
          deep_thinking_mode: input.options.deep_thinking_mode,
          search_before_planning: input.options.search_before_planning,
          task_type: input.options.task_type,
          coor_agents: []
        });
        
      } catch (error) {
        set(state => ({
          ...state,
          execution: {
            ...state.execution,
            status: 'error'
          }
        }));
        throw error;
      }
    },
    
    cancelWorkflow: async () => {
      const { workflowId } = get().execution;
      if (workflowId) {
        await api.post(`/workflow/${workflowId}/cancel`);
      }
      
      set(state => ({
        ...state,
        execution: {
          ...state.execution,
          status: 'idle'
        }
      }));
    },
    
    resetResults: () => {
      set(state => ({
        ...state,
        execution: {
          status: 'idle',
          currentStep: '',
          progress: 0,
          startTime: null,
          events: [],
          workflowId: null
        },
        results: {
          agents: [],
          logs: [],
          report: '',
          generatedCode: []
        }
      }));
    }
  }))
);
```

## 五、部署和集成方案

### 5.1 开发环境启动

```bash
# 后端启动
cd cooragent
uv run src/service/app.py --port 8001

# 前端启动
cd web
npm install
npm run dev  # 默认端口3000
```

### 5.2 生产环境部署

#### Docker部署方案
```dockerfile
# Dockerfile.web
FROM node:18-alpine as builder

WORKDIR /app
COPY web/package*.json ./
RUN npm ci

COPY web/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
```

#### Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  cooragent-backend:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DEBUG=False
      - USE_BROWSER=True
    volumes:
      - ./store:/app/store
      - ./.env:/app/.env
    
  cooragent-frontend:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "80:80"
    depends_on:
      - cooragent-backend
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:8001

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### 5.3 Nginx配置

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    
    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://cooragent-backend:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
    
    # WebSocket代理
    location /ws/ {
        proxy_pass http://cooragent-backend:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 六、调试和监控方案

### 6.1 调试工具

#### 前端调试
```typescript
// src/utils/debug.ts
export class DebugLogger {
  private static instance: DebugLogger;
  private logs: LogEntry[] = [];
  
  static getInstance() {
    if (!this.instance) {
      this.instance = new DebugLogger();
    }
    return this.instance;
  }
  
  log(level: 'info' | 'warn' | 'error', message: string, data?: any) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };
    
    this.logs.push(entry);
    console.log(`[${level.toUpperCase()}] ${message}`, data);
    
    // 发送到后端日志收集
    if (process.env.NODE_ENV === 'production') {
      this.sendToServer(entry);
    }
  }
  
  private async sendToServer(entry: LogEntry) {
    try {
      await fetch('/api/v1/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      console.error('Failed to send log to server:', error);
    }
  }
}

// 使用示例
const debug = DebugLogger.getInstance();
debug.log('info', 'Workflow started', { workflowId, input });
```

#### 后端调试增强
```python
# src/utils/debug.py
import logging
import json
from datetime import datetime
from typing import Any, Dict

class WorkflowDebugger:
    """工作流调试器"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.logger = logging.getLogger(f"workflow.{workflow_id}")
        self.events = []
        
    def log_event(self, event_type: str, agent_name: str, data: Any):
        """记录事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": self.workflow_id,
            "event_type": event_type,
            "agent_name": agent_name,
            "data": data
        }
        
        self.events.append(event)
        self.logger.info(f"[{event_type}] {agent_name}: {json.dumps(data)}")
        
        # 发送到前端
        from src.tools.websocket_manager import websocket_manager
        asyncio.create_task(
            websocket_manager.send_to_user(
                user_id=self.workflow_id.split(':')[0],
                message={
                    "type": "debug_event",
                    "event": event
                }
            )
        )
    
    def get_execution_timeline(self) -> List[Dict]:
        """获取执行时间线"""
        return self.events
    
    def export_debug_report(self) -> str:
        """导出调试报告"""
        report = {
            "workflow_id": self.workflow_id,
            "total_events": len(self.events),
            "timeline": self.events,
            "generated_at": datetime.now().isoformat()
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
```

### 6.2 性能监控

```typescript
// src/hooks/usePerformanceMonitor.ts
import { useEffect, useRef } from 'react';

export const usePerformanceMonitor = () => {
  const metricsRef = useRef({
    startTime: 0,
    endTime: 0,
    apiCalls: 0,
    errors: 0
  });
  
  const startMonitoring = () => {
    metricsRef.current.startTime = performance.now();
  };
  
  const stopMonitoring = () => {
    metricsRef.current.endTime = performance.now();
    
    const metrics = {
      ...metricsRef.current,
      duration: metricsRef.current.endTime - metricsRef.current.startTime
    };
    
    // 发送性能数据
    fetch('/api/v1/metrics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metrics)
    });
  };
  
  return { startMonitoring, stopMonitoring };
};
```

### 6.3 错误处理和恢复

```typescript
// src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // 发送错误报告
    fetch('/api/v1/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString()
      })
    });
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="页面出现错误"
          subTitle="抱歉，页面遇到了一些问题。请尝试刷新页面或联系技术支持。"
          extra={[
            <Button 
              type="primary" 
              key="refresh"
              onClick={() => window.location.reload()}
            >
              刷新页面
            </Button>,
            <Button 
              key="report"
              onClick={() => {
                // 发送详细错误报告
                console.error('Detailed error:', this.state.error);
              }}
            >
              报告问题
            </Button>
          ]}
        />
      );
    }
    
    return this.props.children;
  }
}
```

## 七、开发实施计划

### 7.1 第一阶段（1-2周）：基础架构
- [ ] 创建FastAPI应用主入口 (`src/service/app.py`)
- [ ] 实现基础API接口（健康检查、模板获取等）
- [ ] 搭建前端项目结构和基础组件
- [ ] 实现基本的状态管理和API客户端
- [ ] 完成基础的输入和展示界面

### 7.2 第二阶段（2-3周）：核心功能
- [ ] 实现流式API接口和SSE支持
- [ ] 完成智能输入组件和选项配置
- [ ] 实现实时执行状态展示
- [ ] 完成结果展示和代码查看功能
- [ ] 集成WebSocket实时通信

### 7.3 第三阶段（1-2周）：增强功能
- [ ] 实现智能体管理和编辑功能
- [ ] 添加调试和监控工具
- [ ] 完善错误处理和用户体验
- [ ] 性能优化和界面美化
- [ ] 完成单元测试和集成测试

### 7.4 第四阶段（1周）：部署和文档
- [ ] 配置生产环境部署
- [ ] 编写使用文档和API文档
- [ ] 性能测试和安全检查
- [ ] 最终用户测试和反馈收集

## 八、总结

这个技术方案基于现有的Cooragent系统，通过以下关键技术实现Web界面：

1. **后端扩展**: 基于现有FastAPI服务，增加流式API和WebSocket支持
2. **前端架构**: React + TypeScript + Ant Design构建现代化界面
3. **实时通信**: SSE + WebSocket实现执行过程的实时反馈
4. **状态管理**: Zustand提供简洁高效的状态管理
5. **调试监控**: 完整的调试工具和性能监控体系

通过这个方案，用户可以通过Web界面"一句话输入需求"，系统自动分析、创建智能体协作方案，并实时展示执行过程和最终结果，大大降低了多智能体系统的使用门槛。 