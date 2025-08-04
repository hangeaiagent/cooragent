#!/bin/bash

# Cooragent本地开发环境启动脚本
# 基于 docs/07本地开发环境启动命令0724.md

echo "🚀 启动Cooragent本地开发环境..."
echo "=================================="

# 检查conda命令
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到conda命令"
    echo "💡 请先安装Miniconda: brew install miniconda"
    exit 1
fi

echo "✅ Conda环境检查通过"

# 获取conda初始化脚本路径
CONDA_BASE=$(conda info --base)
if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    source "$CONDA_BASE/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    echo "❌ 无法找到conda初始化脚本"
    exit 1
fi

# 检查cooragent环境是否存在
if ! conda env list | grep -q "cooragent"; then
    echo "❌ 未找到cooragent环境"
    echo "💡 请创建环境:"
    echo "   conda create -n cooragent python=3.12 -y -c conda-forge"
    echo "   conda activate cooragent"
    echo "   pip install -e ."
    exit 1
fi

# 激活conda环境
echo "🐍 激活cooragent环境..."
conda activate cooragent

if [ $? -ne 0 ]; then
    echo "❌ 无法激活cooragent环境"
    exit 1
fi

echo "✅ 环境激活成功: $(python --version)"

# 检查项目依赖
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 未找到pyproject.toml文件"
    echo "💡 请确保在项目根目录下运行此脚本"
    exit 1
fi

# 安装/更新项目依赖
echo "📦 检查项目依赖..."
pip install -e . -q

# 检查环境变量文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  未找到.env文件，从.env.example复制..."
        cp .env.example .env
        echo "💡 请编辑.env文件配置API密钥"
    else
        echo "⚠️  未找到.env文件，请手动创建并配置API密钥"
    fi
fi

# 创建必要目录
mkdir -p logs generated_projects

# 函数：关闭占用指定端口的进程
kill_port_process() {
    local port=$1
    local port_name=$2
    
    if command -v lsof &> /dev/null; then
        # 查找占用端口的进程
        local pids=$(lsof -ti :$port 2>/dev/null)
        
        if [ -n "$pids" ]; then
            echo "⚠️  端口$port已被以下进程占用:"
            for pid in $pids; do
                local process_info=$(ps -p $pid -o pid,ppid,command --no-headers 2>/dev/null)
                if [ -n "$process_info" ]; then
                    echo "   PID: $pid - $process_info"
                fi
            done
            
            echo ""
            read -p "🤔 是否要关闭这些进程并启动新服务? (Y/n): " -n 1 -r
            echo ""
            
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                echo "👋 启动已取消"
                exit 1
            else
                echo "🔄 正在关闭占用端口$port的进程..."
                for pid in $pids; do
                    echo "   关闭进程 PID: $pid"
                    kill -TERM $pid 2>/dev/null
                    
                    # 等待进程优雅退出
                    sleep 2
                    
                    # 如果进程还在运行，强制关闭
                    if kill -0 $pid 2>/dev/null; then
                        echo "   强制关闭进程 PID: $pid"
                        kill -KILL $pid 2>/dev/null
                    fi
                done
                
                # 再次检查端口是否已释放
                sleep 1
                local remaining_pids=$(lsof -ti :$port 2>/dev/null)
                if [ -n "$remaining_pids" ]; then
                    echo "❌ 端口$port仍被占用，请手动处理"
                    exit 1
                else
                    echo "✅ 端口$port已释放"
                fi
            fi
        else
            echo "✅ 端口$port可用"
        fi
    else
        echo "ℹ️  无法检查端口占用状态 (lsof不可用)"
    fi
}

# 检查并处理端口占用
echo "🔌 检查端口占用..."
kill_port_process 8000 "主服务器"

# 同时检查8888端口（可选服务）
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "ℹ️  端口8888已被占用（Netlify开发服务器或其他服务）"
fi

echo ""
echo "🌐 启动Cooragent代码生成器Web服务..."
echo "=================================="
echo "📱 Web界面: http://localhost:8000/"
echo "📋 API文档: http://localhost:8000/docs"
echo "❤️  健康检查: http://localhost:8000/health"
echo ""
echo "🔧 基于Cooragent三层智能分析架构:"
echo "   协调器 → 规划器 → 智能体工厂 → 代码生成"
echo ""
echo "📝 详细日志: logs/server.log"
echo "🔍 中文日志: grep '中文日志' logs/server.log"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="
echo ""

# 启动主要Web服务器 (按照文档中的命令)
echo "🚀 启动服务器..."
python generator_cli.py server --host 0.0.0.0 --port 8000 