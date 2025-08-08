#!/bin/bash

# 新版本旅游多智能体系统启动脚本（带后台日志）
# 修复了前后端接口调用逻辑，支持后台运行和日志监控

echo "🚀 启动旅游多智能体系统（后台日志版本）"
echo "================================================"

# 1. 设置工作目录
cd /Users/a1/work/cooragent

# 2. 停止现有服务
echo "🛑 停止现有服务..."
# 停止8000端口的后台进程
lsof -ti:8000 | xargs -r kill -9 2>/dev/null
# 停止8888端口的前端进程
lsof -ti:8888 | xargs -r kill -9 2>/dev/null
# 停止generator_cli相关进程
ps aux | grep "generator_cli.py" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 3

echo "✅ 已停止现有服务"

# 3. 准备日志目录
echo "📁 准备日志目录..."
mkdir -p logs
mkdir -p logs/backend
mkdir -p logs/frontend

# 清空或创建日志文件
> logs/backend/generator.log
> logs/backend/server.log
> logs/frontend/python_server.log
echo "✅ 日志目录准备完成"

# 4. 激活conda环境
echo "🐍 激活conda环境..."
# 尝试不同的conda初始化路径
CONDA_PATHS=(
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    "/opt/miniconda3/etc/profile.d/conda.sh"
    "/opt/anaconda3/etc/profile.d/conda.sh"
)

CONDA_INITIALIZED=false
for conda_path in "${CONDA_PATHS[@]}"; do
    if [ -f "$conda_path" ]; then
        source "$conda_path"
        CONDA_INITIALIZED=true
        break
    fi
done

if [ "$CONDA_INITIALIZED" = false ]; then
    echo "⚠️  未找到conda，尝试直接使用系统Python..."
    # 检查是否有cooragent环境
    if command -v python3 &> /dev/null; then
        echo "✅ 使用系统Python3"
    else
        echo "❌ 未找到Python环境"
        exit 1
    fi
else
    # 尝试激活cooragent环境
    if conda activate cooragent 2>/dev/null; then
        echo "✅ conda环境已激活 (cooragent)"
    else
        echo "⚠️  cooragent环境不存在，使用base环境"
        conda activate base
    fi
fi

# 5. 设置环境变量
echo "⚙️ 设置环境变量..."
export PYTHONPATH="/Users/a1/work/cooragent/src:/Users/a1/work/cooragent"
export PYTHONUNBUFFERED=1
echo "✅ 环境变量设置完成"

# 6. 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，请配置API密钥"
    exit 1
fi
echo "✅ .env文件检查通过"

# 7. 启动后台API服务器（端口8000）
echo "🖥️ 启动后台API服务器（端口8000）..."
nohup python generator_cli.py server --host 0.0.0.0 --port 8000 > logs/backend/generator.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后台API服务器已启动 (PID: $BACKEND_PID)"

# 8. 等待后台服务启动
echo "⏳ 等待后台服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后台服务启动成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 后台服务启动超时"
        exit 1
    fi
    sleep 1
done

# 9. 启动前端服务器（端口8888）
echo "🌐 启动前端服务器（端口8888）..."

# 使用Python HTTP服务器启动前端（更简单稳定）
nohup python3 -m http.server 8888 > logs/frontend/python_server.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服务器已启动 (PID: $FRONTEND_PID)"

# 10. 等待前端服务启动
echo "⏳ 等待前端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8888 > /dev/null 2>&1; then
        echo "✅ 前端服务启动成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 前端服务启动超时"
        exit 1
    fi
    sleep 1
done

# 11. 保存进程信息
echo "💾 保存进程信息..."
cat > logs/service_pids.txt << EOF
# 服务进程信息 - $(date)
BACKEND_PID=$BACKEND_PID
FRONTEND_PID=$FRONTEND_PID

# 服务地址
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8888

# 日志文件
BACKEND_LOG=logs/backend/generator.log
FRONTEND_LOG=logs/frontend/python_server.log
EOF

# 12. 显示启动信息
echo "================================================"
echo "🎉 旅游多智能体系统启动完成！"
echo ""
echo "📡 服务地址："
echo "   • 前端界面: http://localhost:8888"
echo "   • 后台API:  http://localhost:8000"
echo "   • API文档:  http://localhost:8000/docs"
echo "   • 健康检查: http://localhost:8000/health"
echo ""
echo "📋 进程信息："
echo "   • 后台进程ID: $BACKEND_PID"
echo "   • 前端进程ID: $FRONTEND_PID"
echo ""
echo "📜 日志监控："
echo "   • 后台日志: tail -f logs/backend/generator.log"
echo "   • 前端日志: tail -f logs/frontend/python_server.log"
echo ""
echo "🛑 停止服务："
echo "   • 停止后台: kill $BACKEND_PID"
echo "   • 停止前端: kill $FRONTEND_PID"
echo "   • 或运行:   ./stop_services.sh"
echo ""
echo "================================================"

# 13. 询问是否显示日志
read -p "是否要显示实时日志? (y/N): " show_logs
if [[ $show_logs =~ ^[Yy]$ ]]; then
    echo "📊 显示实时日志（Ctrl+C退出）..."
    echo "================================================"
    # 同时显示前后端日志
    tail -f logs/backend/generator.log logs/frontend/python_server.log
else
    echo "✅ 服务已在后台运行，可通过以下命令查看日志："
    echo "   tail -f logs/backend/generator.log"
    echo "   tail -f logs/frontend/python_server.log"
fi