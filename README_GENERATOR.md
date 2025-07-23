# Cooragent 代码生成器

基于Cooragent架构的多智能体项目代码生成器，实现"一句话生成完整多智能体应用"的功能。

## 🚀 快速开始

### 方式一：Web界面（推荐）

1. **启动服务器**
   ```bash
   python generator_cli.py server --port 8000
   ```

2. **访问Web界面**
   
   打开浏览器访问: http://localhost:8000

3. **生成项目**
   - 在文本框中输入需求描述
   - 点击"生成Cooragent应用"
   - 等待生成完成，下载项目压缩包

### 方式二：命令行

```bash
# 生成单个项目
python generator_cli.py generate "创建一个股票分析系统，能够获取实时股票数据、分析技术指标、爬取相关新闻并生成投资建议报告"

# 指定用户ID和输出目录
python generator_cli.py generate "数据分析工具" --user-id demo --output my_projects/

# 查看帮助
python generator_cli.py --help
```

## 🛠️ 环境要求

- Python 3.12+
- 已配置的Cooragent环境
- 必需的API密钥 (OpenAI, Tavily等)

## 📋 功能特性

### ✅ 已实现功能

- **智能需求分析**: 调用Cooragent工作流分析用户需求
- **自动智能体生成**: 基于需求自动创建合适的智能体
- **组件复用**: 复用Cooragent核心组件保证质量
- **项目定制化**: 生成完整的可部署项目结构
- **Web界面**: 友好的Web交互界面
- **文件管理**: 自动压缩和文件清理机制
- **API接口**: 完整的RESTful API

### 🎯 生成项目特点

- **基于Cooragent**: 复用成熟的多智能体架构
- **开箱即用**: 包含完整的部署配置
- **工具集成**: 根据需求自动选择工具
- **文档完整**: 自动生成详细的使用文档
- **Docker支持**: 包含Docker部署配置

## 📦 生成项目结构

```
generated_project/
├── src/                    # 核心源码 (基于Cooragent)
│   ├── interface/         # 接口定义
│   ├── workflow/          # 工作流引擎
│   ├── manager/           # 智能体管理
│   ├── llm/              # LLM集成
│   ├── tools/            # 工具集合
│   ├── prompts/          # 提示词管理
│   └── service/          # 服务层
├── config/               # 配置文件
├── store/               # 数据存储
├── main.py              # 应用入口
├── requirements.txt     # 依赖清单
├── .env.example        # 环境变量模板
├── Dockerfile          # Docker配置
├── docker-compose.yml  # Docker Compose
├── start.sh            # 启动脚本 (Unix)
├── start.bat           # 启动脚本 (Windows)
└── README.md           # 使用说明
```

## 💡 使用示例

### 示例需求

1. **股票分析系统**
   ```
   创建一个股票分析专家智能体，查看小米股票走势，分析相关新闻，预测股价趋势并给出投资建议
   ```

2. **新闻情感分析**
   ```
   构建一个新闻分析系统，能够搜索最新科技新闻、分析情感倾向并生成摘要报告
   ```

3. **数据分析工具**
   ```
   开发一个数据分析助手，支持Python数据处理、统计分析和可视化图表生成
   ```

4. **研究助手**
   ```
   构建一个研究助手系统，能够搜索学术资料、整理信息并生成研究报告
   ```

### 生成的智能体类型

根据需求自动选择和生成：

- **researcher**: 搜索和信息收集
- **coder**: 代码执行和数据分析
- **reporter**: 报告生成和总结
- **browser**: 浏览器操作和交互
- **agent_factory**: 动态创建新智能体

### 集成的工具

- **tavily_tool**: 网络搜索
- **python_repl_tool**: Python代码执行
- **bash_tool**: 系统命令执行
- **crawl_tool**: 网页爬虫
- **browser_tool**: 浏览器自动化

## 🔧 API接口

### 生成项目

```bash
POST /api/generate
Content-Type: application/json

{
  "content": "您的需求描述",
  "user_id": "用户ID（可选）"
}
```

### 查询状态

```bash
GET /api/generate/{task_id}/status
```

### 下载项目

```bash
GET /api/generate/{task_id}/download
```

### 获取示例

```bash
GET /api/generate/examples
```

## 🧪 测试功能

```bash
# 运行内置测试用例
python generator_cli.py test
```

测试将验证：
- 代码生成器核心功能
- 智能体创建和配置
- 项目文件生成
- 压缩和打包

## 📊 监控和管理

### Web界面功能

- 实时生成状态显示
- 进度条和详细信息
- 示例需求快速选择
- 生成历史记录

### API监控

- 健康检查: `GET /health`
- 任务列表: `GET /api/tasks`
- 文件清理: 自动清理24小时前的文件

## 🔍 故障排除

### 常见问题

1. **生成失败**
   - 检查API密钥配置
   - 确保网络连接正常
   - 查看日志文件

2. **智能体创建失败**
   - 确认Cooragent环境正常
   - 检查agent_manager初始化
   - 验证工具依赖

3. **文件下载失败**
   - 确认任务状态为completed
   - 检查文件是否存在
   - 验证磁盘空间

### 日志查看

```bash
# 启动时查看详细日志
python generator_cli.py server --port 8000 2>&1 | tee generator.log
```

## 🚀 部署生成的项目

1. **解压项目文件**
   ```bash
   unzip cooragent_app_xxx.zip
   cd cooragent_app_xxx
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入API密钥
   ```

4. **启动应用**
   ```bash
   # Unix/Linux/macOS
   ./start.sh
   
   # Windows
   start.bat
   
   # 或直接运行
   python main.py
   ```

## 📈 性能指标

- **生成时间**: 通常30-60秒
- **项目大小**: 压缩包5-15MB
- **并发支持**: 最多5个同时生成
- **成功率**: 95%+ (基于Cooragent稳定性)

## 🔄 更新和维护

### 自动清理

- 24小时后自动删除生成的文件
- 最多保留100个最新生成的项目
- 定期清理日志文件

### 监控建议

- 定期检查磁盘空间
- 监控API调用次数
- 备份重要的生成项目

## 🤝 贡献

本项目基于Cooragent开源项目构建，遵循相同的贡献准则。

## 📄 许可证

与Cooragent项目保持一致的许可证条款。

---

> 💡 **提示**: 生成的项目保持与Cooragent生态的完全兼容，可以随时集成新的工具和智能体。 