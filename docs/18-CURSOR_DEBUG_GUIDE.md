# Cursor Python调试环境使用指南

## 🎯 环境配置概览

✅ **Python版本**: 3.12.11 (Conda环境)  
✅ **环境名称**: cooragent  
✅ **调试工具**: debugpy 1.8.15  
✅ **Web框架**: FastAPI + Uvicorn  
✅ **配置文件**: .vscode/ 目录完整配置  

## 🔧 配置文件说明

### 1. `.vscode/launch.json` - 调试配置
提供6种调试场景：
- **🐍 Python: 当前文件** - 调试任意Python文件
- **🚀 Cooragent: 启动服务器** - 调试Web服务器启动
- **🧪 Python: 测试当前文件** - 使用pytest调试测试
- **🔬 Python: CLI命令调试** - 调试cli.py命令
- **🌐 Cooragent: API调试** - 调试API接口
- **🎯 Python: 远程调试** - 连接远程调试端口

### 2. `.vscode/settings.json` - 工作区设置
- Python解释器: Conda环境路径
- 代码格式化: Black (120字符行长度)
- 代码检查: Flake8 + Pylint
- 测试框架: pytest
- 终端环境: 自动激活conda环境

### 3. `.vscode/tasks.json` - 快速任务
- **🚀 启动Cooragent服务器**
- **🧪 运行所有测试**
- **🔍 代码质量检查**
- **🎨 格式化代码**
- **🔧 激活Conda环境**
- **⚡ CLI命令测试**

## 🚀 如何使用调试功能

### 方式一：图形界面调试
1. **打开文件**: 在Cursor中打开要调试的Python文件
2. **设置断点**: 在代码行号左侧点击设置红色断点
3. **启动调试**: 按 `F5` 或点击调试面板的启动按钮
4. **选择配置**: 选择适合的调试配置（如"🐍 Python: 当前文件"）

### 方式二：命令面板调试
1. 按 `Cmd+Shift+P` 打开命令面板
2. 输入 "Debug: Start Debugging"
3. 选择调试配置

### 方式三：快速任务
1. 按 `Cmd+Shift+P` 打开命令面板
2. 输入 "Tasks: Run Task"
3. 选择任务（如"🚀 启动Cooragent服务器"）

## 🔍 调试控制说明

### 键盘快捷键
- **F5**: 继续执行
- **F10**: 单步执行（跳过函数调用）
- **F11**: 单步执行（进入函数）
- **Shift+F11**: 跳出当前函数
- **Shift+F5**: 停止调试

### 调试面板功能
- **变量(Variables)**: 查看当前作用域的所有变量
- **监视(Watch)**: 添加表达式监视特定值
- **调用堆栈(Call Stack)**: 查看函数调用链
- **断点(Breakpoints)**: 管理所有断点

## 📁 调试测试文件

### `debug_cooragent.py` - 主要调试测试
```bash
# 运行调试测试
conda activate cooragent
python debug_cooragent.py
```

**测试内容**:
- ✅ Conda环境验证
- ✅ 模块导入测试  
- ✅ 配置文件检查
- ✅ 断点调试演示
- ✅ 异步函数调试
- ✅ CLI模拟调试

## 🌐 Cooragent服务器调试

### 启动服务器调试
1. 选择调试配置: "🚀 Cooragent: 启动服务器"
2. 在 `generator_cli.py` 中设置断点
3. 按F5启动调试
4. 服务器将在调试模式下启动在端口8000

### API接口调试
1. 启动服务器后，访问: http://localhost:8000/docs
2. 在API文件中设置断点
3. 通过Web界面或curl触发API调用
4. 断点将被触发，可以检查请求数据

## 🧪 测试调试

### 运行单个测试文件
1. 打开测试文件
2. 选择调试配置: "🧪 Python: 测试当前文件"
3. 设置断点
4. 按F5开始调试

### 运行所有测试
1. 使用任务: "🧪 运行所有测试"
2. 或者在终端运行: `python -m pytest -v`

## 📝 调试最佳实践

### 1. 断点策略
```python
# 在函数入口设置断点
def important_function(data):
    # 断点位置 - 检查输入参数
    result = process_data(data)
    # 断点位置 - 检查处理结果
    return result
```

### 2. 变量监视
- 添加复杂表达式到监视窗口
- 监视关键对象的属性变化
- 使用条件断点减少不必要的中断

### 3. 日志调试结合
```python
import logging
logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("调试信息")  # 日志记录
    # 断点位置 - 详细检查
    complex_operation()
```

## 🔗 常用调试场景

### 场景1: Web API调试
```bash
# 1. 启动调试服务器
选择: "🚀 Cooragent: 启动服务器"

# 2. 设置API断点
文件: src/api/generator_api.py
位置: @app.post("/api/generate") 函数内

# 3. 触发调试
浏览器: http://localhost:8000/
```

### 场景2: 工作流调试
```bash
# 1. CLI命令调试
选择: "🔬 Python: CLI命令调试"

# 2. 设置工作流断点
文件: src/workflow/coor_task.py
位置: coordinator_node 函数内

# 3. 观察数据流
监视: state 变量的变化
```

### 场景3: 代码生成调试
```bash
# 1. 当前文件调试
选择: "🐍 Python: 当前文件"

# 2. 设置生成器断点
文件: src/generator/cooragent_generator.py
位置: generate_project 方法内

# 3. 跟踪生成过程
监视: 生成进度和文件创建
```

## ⚠️ 故障排除

### 问题1: 调试器无法启动
**解决方案**:
```bash
# 检查Python路径
which python
# 应该显示: /usr/local/Caskroom/miniconda/base/envs/cooragent/bin/python

# 重新激活环境
conda activate cooragent
```

### 问题2: 断点不生效
**解决方案**:
- 确保文件已保存
- 检查Python解释器路径正确
- 重新启动Cursor

### 问题3: 模块导入失败
**解决方案**:
```bash
# 检查PYTHONPATH
echo $PYTHONPATH
# 应该包含: /Users/a1/work/cooragent/src

# 手动设置
export PYTHONPATH="/Users/a1/work/cooragent/src:$PYTHONPATH"
```

## 📞 获取帮助

### 调试信息收集
```bash
# 环境信息
conda info --envs
python --version
pip list | grep debugpy

# 项目信息
ls -la .vscode/
python debug_cooragent.py
```

### 常用资源
- **Cursor文档**: 查看官方调试指南
- **Python debugpy**: https://github.com/microsoft/debugpy
- **FastAPI调试**: https://fastapi.tiangolo.com/tutorial/debugging/

---

## 🎉 开始调试！

现在你的Cursor环境已经完全配置好Python调试功能。选择一个调试配置，设置断点，开始探索Cooragent的代码世界吧！

**快速开始**:
1. 打开 `debug_cooragent.py`
2. 在第134行 `result = main()` 设置断点
3. 按F5选择 "🐍 Python: 当前文件"
4. 享受调试过程！🐛→🐞→✨ 