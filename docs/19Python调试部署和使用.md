# Python调试部署和使用指南

## 概述

本文档详细记录了Cooragent项目在VS Code中Python调试环境的部署过程、遇到的问题及解决方案，以及正确的调试使用方法。

## 目录

1. [环境要求](#环境要求)
2. [问题诊断与解决](#问题诊断与解决)
3. [VS Code调试配置](#vs-code调试配置)
4. [调试使用方法](#调试使用方法)
5. [故障排除指南](#故障排除指南)
6. [最佳实践](#最佳实践)

---

## 环境要求

### 系统环境
- macOS 21.6.0 (支持其他操作系统)
- Python 3.12.11
- Conda (Miniconda)
- VS Code
- Node.js (部分MCP组件需要)

### Python环境
```bash
# Conda环境
conda env: cooragent
Python路径: /usr/local/Caskroom/miniconda/base/envs/cooragent/bin/python
```

---

## 问题诊断与解决

### 问题1: MCP配置错误导致应用启动失败

#### 错误现象
```
TypeError: _create_sse_session() got an unexpected keyword argument 'env'
ModuleNotFoundError: No module named 'docx'
```

#### 问题原因
1. **SSE连接配置错误**: SSE类型的MCP服务器不支持`env`参数
2. **依赖缺失**: MCP-Doc组件缺少`python-docx`依赖
3. **配置复杂度过高**: 包含了需要真实API密钥的服务

#### 解决方案

**步骤1: 修复SSE配置处理**
```python
# src/manager/mcp.py
if transport_type == "sse":
    sse_config = value.copy()
    # Remove env from SSE config as it's not supported by _create_sse_session
    if "env" in sse_config:
        del sse_config["env"]
    sse_config["transport"] = "sse"
    _mcp_client_config[key] = sse_config
```

**步骤2: 安装缺失依赖**
```bash
pip install python-docx
```

**步骤3: 简化MCP配置**
```json
{
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": [
          "-y",
          "@modelcontextprotocol/server-filesystem",
          "/Users/a1/work/cooragent/generated_projects"
        ]
      }
    }
}
```

### 问题2: VS Code终端启动失败

#### 错误现象
```
The terminal process "/bin/zsh '-l', '-c', 'conda activate cooragent && exec zsh'" terminated with exit code: 1.
CondaError: Run 'conda init' before 'conda activate'
```

#### 问题原因
VS Code使用非交互式shell启动终端时，没有加载用户的`.zshrc`配置文件，导致conda未初始化。

#### 解决方案

**修改VS Code终端配置** (`.vscode/settings.json`):
```json
{
    "terminal.integrated.profiles.osx": {
        "zsh-conda": {
            "path": "/bin/zsh",
            "args": ["-i", "-c", "source ~/.zshrc && conda activate cooragent && exec zsh -i"]
        }
    },
    "terminal.integrated.defaultProfile.osx": "zsh-conda",
    "python.defaultInterpreterPath": "/usr/local/Caskroom/miniconda/base/envs/cooragent/bin/python",
    "python.terminal.activateEnvironment": false
}
```

**关键改进**:
- 使用交互式shell (`-i`) 而不是登录shell (`-l`)
- 显式加载`.zshrc`确保conda初始化
- 设置正确的Python解释器路径

---

## VS Code调试配置

### launch.json配置

创建或更新`.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug CLI: run-l命令",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/cli.py",
            "args": [
                "run-l",
                "--debug",
                "--user-id", "test",
                "--task-type", "agent_workflow",
                "--message", "创建行程设计智能体：根据目的地和用户偏好，推荐景点、给出理由及照片 URL，并设计详细日程。"
            ],
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src:${workspaceFolder}",
                "CONDA_DEFAULT_ENV": "cooragent"
            },
            "python": "/usr/local/Caskroom/miniconda/base/envs/cooragent/bin/python",
            "cwd": "${workspaceFolder}",
            "stopOnEntry": false,
            "debugOptions": [
                "RedirectOutput"
            ]
        },
        {
            "name": "Debug CLI: 通用命令",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/cli.py",
            "args": [],
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src:${workspaceFolder}",
                "CONDA_DEFAULT_ENV": "cooragent"
            },
            "python": "/usr/local/Caskroom/miniconda/base/envs/cooragent/bin/python",
            "cwd": "${workspaceFolder}",
            "stopOnEntry": false
        }
    ]
}
```

### settings.json完整配置

```json
{
    "terminal.integrated.profiles.osx": {
        "zsh-conda": {
            "path": "/bin/zsh",
            "args": ["-i", "-c", "source ~/.zshrc && conda activate cooragent && exec zsh -i"]
        }
    },
    "terminal.integrated.defaultProfile.osx": "zsh-conda",
    "python.defaultInterpreterPath": "/usr/local/Caskroom/miniconda/base/envs/cooragent/bin/python",
    "python.terminal.activateEnvironment": false
}
```

---

## 调试使用方法

### 方法1: 使用VS Code调试功能（推荐）

#### 步骤1: 设置断点
在需要调试的代码行左侧点击，设置红色断点。

常用断点位置：
- `cli.py` 第464行: `async def run_launch` 函数入口
- `src/workflow/coor_task.py`: 工作流执行逻辑
- `src/manager/agents.py`: 智能体管理逻辑

#### 步骤2: 启动调试
1. 按 `Cmd+Shift+D` (macOS) 打开调试面板
2. 在顶部下拉菜单选择 **"Debug CLI: run-l命令"**
3. 点击绿色播放按钮 ▶️ 或按 `F5`

#### 步骤3: 调试操作
- **继续执行**: `F5` 或点击继续按钮
- **单步跳过**: `F10`
- **单步进入**: `F11`
- **单步跳出**: `Shift+F11`
- **停止调试**: `Shift+F5`

#### 步骤4: 查看信息
- **变量窗口**: 查看当前作用域的变量值
- **调用堆栈**: 查看函数调用层次
- **调试控制台**: 执行Python表达式
- **监视窗口**: 添加需要持续监控的表达式

### 方法2: 命令行调试

#### 基本命令行执行
```bash
python cli.py run-l --debug --user-id test --task-type agent_workflow --message "测试消息"
```

#### 使用pdb调试
```bash
python -m pdb cli.py run-l --debug --user-id test --task-type agent_workflow --message "测试消息"
```

#### 使用debugpy远程调试
```bash
python -m debugpy --listen 5678 --wait-for-client cli.py run-l --debug --user-id test --task-type agent_workflow --message "测试消息"
```

### 方法3: 交互式调试

#### 在代码中插入断点
```python
import pdb; pdb.set_trace()  # 在需要调试的位置插入
```

#### 使用breakpoint()函数 (Python 3.7+)
```python
breakpoint()  # 更现代的断点方式
```

---

## 故障排除指南

### 常见问题及解决方案

#### 问题1: 断点不生效
**现象**: 设置断点后程序不停止

**解决方案**:
1. 确认使用VS Code调试功能而非直接运行
2. 检查`launch.json`中的Python路径是否正确
3. 确认`justMyCode`设置为`false`

#### 问题2: 终端环境错误
**现象**: 调试时conda环境未激活

**解决方案**:
1. 检查`.vscode/settings.json`中的终端配置
2. 确认Python解释器路径正确
3. 重启VS Code使配置生效

#### 问题3: 模块导入错误
**现象**: `ModuleNotFoundError`或导入错误

**解决方案**:
1. 检查`PYTHONPATH`环境变量设置
2. 确认conda环境已激活
3. 验证必要的依赖已安装

#### 问题4: MCP工具加载失败
**现象**: MCP相关错误

**解决方案**:
1. 简化`config/mcp.json`配置
2. 检查MCP组件依赖
3. 验证Node.js环境（某些组件需要）

### 环境验证命令

```bash
# 检查conda环境
conda env list
echo $CONDA_DEFAULT_ENV

# 检查Python版本和路径
python --version
which python

# 测试模块导入
python -c "from src.workflow.cache import workflow_cache; print('✅ 模块导入成功')"

# 测试CLI命令基础功能
python cli.py --help
```

---

## 最佳实践

### 1. 开发环境设置

#### 推荐的目录结构
```
cooragent/
├── .vscode/
│   ├── settings.json      # 终端和Python配置
│   └── launch.json        # 调试配置
├── config/
│   └── mcp.json          # 简化的MCP配置
├── src/                  # 源代码
└── cli.py               # 主入口
```

#### 环境变量设置
```bash
export PYTHONPATH="${WORKSPACE}/src:${WORKSPACE}"
export CONDA_DEFAULT_ENV="cooragent"
```

### 2. 调试技巧

#### 有效的断点策略
1. **入口点断点**: 在主要函数入口设置
2. **异常处理断点**: 在try-catch块设置
3. **条件断点**: 只在特定条件下停止
4. **日志断点**: 输出信息而不停止执行

#### 使用调试控制台
```python
# 在调试控制台中执行
len(agent_manager.available_agents)  # 查看智能体数量
state['workflow_id']                 # 查看工作流ID
```

### 3. 性能调试

#### 使用性能分析工具
```python
import cProfile
import pstats

# 性能分析
cProfile.run('your_function()', 'profile_output')
stats = pstats.Stats('profile_output')
stats.sort_stats('cumulative').print_stats(10)
```

#### 内存使用监控
```python
import tracemalloc

tracemalloc.start()
# 你的代码
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

### 4. 团队协作

#### Git配置建议
```bash
# .gitignore中添加
.vscode/settings.json    # 个人配置不同步
*.pyc
__pycache__/
.pytest_cache/
```

#### 文档化调试信息
- 记录关键断点位置
- 文档化常见问题解决方案
- 维护调试配置模板

---

## 附录

### A. 常用调试命令速查

| 功能 | VS Code快捷键 | 命令行 |
|------|---------------|--------|
| 启动调试 | `F5` | `python -m pdb script.py` |
| 设置断点 | 点击行号左侧 | `b linenum` |
| 继续执行 | `F5` | `c` |
| 单步执行 | `F10` | `n` |
| 进入函数 | `F11` | `s` |
| 查看变量 | 变量窗口 | `p variable` |

### B. 相关文档链接

- [VS Code Python调试文档](https://code.visualstudio.com/docs/python/debugging)
- [VS Code终端故障排除](https://code.visualstudio.com/docs/supporting/troubleshoot-terminal-launch)
- [MCP组件配置方法](./12mcp组件配置方法.md)
- [Python pdb调试器文档](https://docs.python.org/3/library/pdb.html)

### C. 版本信息

- **文档版本**: v1.0
- **最后更新**: 2025-07-27
- **适用系统**: Cooragent v1.0+
- **测试环境**: macOS 21.6.0, Python 3.12.11, VS Code

---

## 总结

通过本指南的配置，您应该能够：

1. ✅ **成功配置Python调试环境** - VS Code + Conda + MCP
2. ✅ **解决终端启动问题** - 正确的shell和conda配置
3. ✅ **设置有效的断点调试** - launch.json配置优化
4. ✅ **掌握调试使用方法** - 多种调试方式和技巧
5. ✅ **处理常见问题** - 故障排除和最佳实践

如果遇到新的问题，建议按照本文档的故障排除流程进行诊断，并及时更新本文档以帮助其他开发者。 