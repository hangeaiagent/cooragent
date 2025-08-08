#!/bin/bash

# 旅游多智能体系统重启脚本（清空日志版本）
# 用途：停止现有服务，清空日志，重新启动服务

echo "🔄 旅游多智能体系统重启（清空日志版本）"
echo "================================================"

# 1. 停止现有服务
echo "🛑 停止现有服务..."
ps aux | grep "generator_cli.py" | grep -v grep | awk '{print $2}' | xargs -r kill -9
sleep 2

# 2. 清空日志文件
echo "🧹 清空日志文件..."
if [ -f "logs/generator.log" ]; then
    > logs/generator.log
    echo "✅ 已清空 logs/generator.log"
else
    mkdir -p logs
    touch logs/generator.log
    echo "✅ 已创建 logs/generator.log"
fi

# 3. 激活conda环境
echo "🐍 激活conda环境..."
conda activate cooragent

# 4. 设置环境变量
echo "⚙️ 设置环境变量..."
export PYTHONPATH="/Users/a1/work/cooragent/src:/Users/a1/work/cooragent"

# 5. 启动服务
echo "🚀 启动旅游多智能体服务..."
echo "================================================"
python generator_cli.py server --host 0.0.0.0 --port 8000