#!/bin/bash

# Cooragent Netlify开发服务器启动脚本
# 基于 docs/07本地开发环境启动命令0724.md
# 这是一个可选的辅助服务，用于前端开发和静态文件服务

echo "🎨 启动Cooragent Netlify开发服务器..."
echo "========================================"

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js"
    echo "💡 请安装Node.js: brew install node"
    exit 1
fi

if ! command -v npx &> /dev/null; then
    echo "❌ 错误: 未找到npx"
    echo "💡 npx通常随Node.js一起安装"
    exit 1
fi

echo "✅ Node.js环境: $(node --version)"
echo "✅ NPX可用: $(npx --version)"

# 检查conda环境
if command -v conda &> /dev/null; then
    # 获取conda初始化脚本路径
    CONDA_BASE=$(conda info --base)
    if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    fi
    
    # 激活cooragent环境（如果存在）
    if conda env list | grep -q "cooragent"; then
        echo "🐍 激活cooragent环境..."
        conda activate cooragent
    else
        echo "⚠️  未找到cooragent环境，使用当前环境"
    fi
else
    echo "ℹ️  未找到conda，使用当前Python环境"
fi

# 检查端口占用
echo "🔌 检查端口占用..."
if command -v lsof &> /dev/null; then
    if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  端口8888已被占用"
        echo "💡 请先关闭占用端口的应用或更改端口"
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
    echo "ℹ️  无法检查端口占用状态 (lsof不可用)"
fi

echo ""
echo "🌐 启动Netlify开发服务器..."
echo "========================================"
echo "📱 静态服务: http://localhost:8888/"
echo "🔧 用途: 前端开发和静态文件服务"
echo "💡 注意: 主要功能通过8000端口的主服务器提供"
echo ""
echo "⚠️  确保主服务器已在8000端口启动:"
echo "   ./start_local_dev.sh"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动Netlify开发服务器 (按照文档中的命令)
echo "🚀 启动Netlify开发服务器..."
npx netlify dev --port 8888 