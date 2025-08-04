#!/bin/bash

# Cooragent 代码生成器启动脚本
# 自动检查环境并启动服务

echo "🤖 Cooragent 代码生成器 启动脚本"
echo "=================================="
echo ""

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python，请安装Python 3.12+"
    exit 1
fi

# 使用python3优先
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✅ Python环境: $($PYTHON_CMD --version)"

# 检查工作目录
if [ ! -f "generator_cli.py" ]; then
    echo "❌ 错误: 请在Cooragent项目根目录下运行此脚本"
    echo "💡 提示: cd到包含generator_cli.py的目录"
    exit 1
fi

echo "✅ 工作目录正确"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 建议在虚拟环境中运行"
    echo "💡 提示: 创建虚拟环境:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # macOS/Linux"
    echo "   venv\\Scripts\\activate     # Windows"
else
    echo "✅ 虚拟环境: $VIRTUAL_ENV"
fi

# 创建必要目录
echo ""
echo "📁 创建必要目录..."
mkdir -p logs generated_projects

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件"
    if [ -f ".env.example" ]; then
        echo "💡 提示: 请复制.env.example为.env并配置API密钥"
        echo "   cp .env.example .env"
    else
        echo "💡 提示: 请创建.env文件并配置必要的API密钥"
    fi
    echo ""
fi

# 检查pip安装
echo "📦 检查包管理器..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "❌ 错误: pip未正确安装"
    exit 1
fi

echo "✅ pip可用"

# 安装项目依赖
echo ""
echo "🔄 安装/更新项目依赖..."
echo "💡 这可能需要几分钟时间，请耐心等待..."

# 首先安装基础依赖
echo "   正在安装基础依赖..."
$PYTHON_CMD -m pip install --upgrade pip

# 使用pyproject.toml安装项目依赖
if [ -f "pyproject.toml" ]; then
    echo "   正在从pyproject.toml安装项目依赖..."
    $PYTHON_CMD -m pip install -e .
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，尝试备用方案..."
        
        # 备用方案：手动安装关键依赖
        echo "   正在安装关键依赖..."
        $PYTHON_CMD -m pip install fastapi>=0.110.0 uvicorn>=0.27.1 langchain>=0.3.0 langgraph>=0.3.5 httpx>=0.28.1 python-dotenv>=1.0.1 aiofiles>=24.1.0 rich>=14.0.0
        
        if [ $? -ne 0 ]; then
            echo "❌ 关键依赖安装失败，请检查网络连接或手动安装"
            echo "💡 手动安装命令:"
            echo "   pip install fastapi uvicorn langchain langgraph httpx python-dotenv aiofiles rich"
            exit 1
        fi
    fi
else
    echo "⚠️  未找到pyproject.toml文件，尝试安装基础依赖..."
    $PYTHON_CMD -m pip install fastapi uvicorn langchain langgraph httpx python-dotenv aiofiles rich
fi

echo "✅ 依赖包安装完成"

# 验证关键模块
echo ""
echo "🔍 验证关键模块..."
for module in fastapi uvicorn langchain; do
    if $PYTHON_CMD -c "import $module" &> /dev/null; then
        echo "✅ $module 可用"
    else
        echo "❌ $module 不可用，请检查安装"
        exit 1
    fi
done

# 检查端口占用
echo ""
echo "🔌 检查端口占用..."
if command -v lsof &> /dev/null; then
    if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  端口8888已被占用"
        echo "💡 选项1: 关闭占用端口的程序"
        echo "💡 选项2: 修改端口配置"
        
        read -p "是否继续启动? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "👋 启动已取消"
            exit 1
        fi
    else
        echo "✅ 端口8888可用"
    fi
else
    echo "⚠️  无法检查端口占用 (lsof不可用)"
fi

echo ""
echo "🚀 启动Cooragent代码生成器..."
echo "=================================="
echo "📱 Web界面: http://localhost:8888"
echo "📋 API文档: http://localhost:8888/docs"
echo "❤️  健康检查: http://localhost:8888/health"
echo "📊 任务管理: http://localhost:8888/api/tasks"
echo "💡 需求示例: http://localhost:8888/api/generate/examples"
echo ""
echo "🔧 基于Cooragent三层智能分析架构:"
echo "   协调器 → 规划器 → 智能体工厂 → 代码生成"
echo ""
echo "📝 详细日志: logs/generator.log"
echo "🔍 中文日志: grep '中文日志' logs/generator.log"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="
echo ""

# 启动服务
$PYTHON_CMD generator_cli.py 