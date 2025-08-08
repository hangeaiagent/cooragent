#!/bin/bash

# 停止旅游多智能体系统服务脚本

echo "🛑 停止旅游多智能体系统服务"
echo "================================================"

# 1. 读取保存的进程信息
if [ -f "logs/service_pids.txt" ]; then
    source logs/service_pids.txt
    
    # 停止后台进程
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔚 停止后台API服务器 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        sleep 2
        kill -9 $BACKEND_PID 2>/dev/null
        echo "✅ 后台API服务器已停止"
    fi
    
    # 停止前端进程
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🔚 停止前端服务器 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
        sleep 2
        kill -9 $FRONTEND_PID 2>/dev/null
        echo "✅ 前端服务器已停止"
    fi
else
    echo "⚠️  未找到进程信息文件，尝试通过端口强制停止..."
fi

# 2. 强制停止端口占用进程
echo "🔍 检查并停止端口占用进程..."

# 停止8000端口进程
PID_8000=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$PID_8000" ]; then
    echo "🔚 停止8000端口进程: $PID_8000"
    kill -9 $PID_8000 2>/dev/null
fi

# 停止8888端口进程
PID_8888=$(lsof -ti:8888 2>/dev/null)
if [ ! -z "$PID_8888" ]; then
    echo "🔚 停止8888端口进程: $PID_8888"
    kill -9 $PID_8888 2>/dev/null
fi

# 停止generator_cli相关进程
GENERATOR_PIDS=$(ps aux | grep "generator_cli.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$GENERATOR_PIDS" ]; then
    echo "🔚 停止generator_cli进程: $GENERATOR_PIDS"
    echo $GENERATOR_PIDS | xargs kill -9 2>/dev/null
fi

# 停止netlify dev进程
NETLIFY_PIDS=$(ps aux | grep "netlify dev" | grep -v grep | awk '{print $2}')
if [ ! -z "$NETLIFY_PIDS" ]; then
    echo "🔚 停止netlify dev进程: $NETLIFY_PIDS"
    echo $NETLIFY_PIDS | xargs kill -9 2>/dev/null
fi

# 3. 清理进程信息文件
if [ -f "logs/service_pids.txt" ]; then
    rm logs/service_pids.txt
    echo "🗑️  已清理进程信息文件"
fi

# 4. 验证停止结果
echo "📊 验证服务停止状态..."
if lsof -i:8000 > /dev/null 2>&1; then
    echo "❌ 端口8000仍被占用"
else
    echo "✅ 端口8000已释放"
fi

if lsof -i:8888 > /dev/null 2>&1; then
    echo "❌ 端口8888仍被占用"
else
    echo "✅ 端口8888已释放"
fi

echo "================================================"
echo "✅ 服务停止完成"