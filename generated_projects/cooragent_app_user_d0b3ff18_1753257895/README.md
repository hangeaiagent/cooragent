# 多智能体协作应用

基于 [Cooragent](https://github.com/LeapLabTHU/cooragent) 架构的定制化多智能体应用

## 项目信息

- **生成时间**: 2025-07-23T16:04:55.279747
- **用户需求**: workflow completed...
- **生成的智能体**: researcher, coder, reporter
- **使用的工具**: crawl_tool, bash_tool, python_repl_tool, tavily_tool

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

{
  "content": "您的任务描述",
  "user_id": "用户ID（可选）",
  "mode": "production"
}
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


### researcher

- **描述**: This agent specializes in research tasks by utilizing search engines and web crawling. It can search for information using keywords, crawl specific URLs to extract content, and synthesize findings into comprehensive reports. The agent excels at gathering information from multiple sources, verifying relevance and credibility, and presenting structured conclusions based on collected data.
- **LLM类型**: LLMType.BASIC  
- **工具**: tavily_tool, crawl_tool


### coder

- **描述**: This agent specializes in software engineering tasks using Python and bash scripting. It can analyze requirements, implement efficient solutions, and provide clear documentation. The agent excels at data analysis, algorithm implementation, system resource management, and environment queries. It follows best practices, handles edge cases, and integrates Python with bash when needed for comprehensive problem-solving.
- **LLM类型**: LLMType.CODE  
- **工具**: python_repl_tool, bash_tool


### reporter

- **描述**: This agent specializes in creating clear, comprehensive reports based solely on provided information and verifiable facts. It presents data objectively, organizes information logically, and highlights key findings using professional language. The agent structures reports with executive summaries, detailed analysis, and actionable conclusions while maintaining strict data integrity and never fabricating information.
- **LLM类型**: LLMType.BASIC  
- **工具**: 


## 工具能力

本应用集成了以下工具:

🕷️ **网页爬虫**: 爬取网页内容，提取结构化信息
⚡ **Shell工具**: 执行系统命令，进行文件操作
🐍 **Python执行器**: 执行Python代码，进行数据分析和计算
🔍 **搜索工具**: 使用Tavily进行网络搜索，获取最新信息

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
response = requests.post("http://localhost:8000/api/task", json={
    "content": "分析最新的AI发展趋势，生成一份详细报告",
    "user_id": "demo_user"
})

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
