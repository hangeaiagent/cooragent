#!/bin/bash

# AI智能助手首页启动脚本
# 使用方法：./start_homepage.sh

echo "🚀 启动AI智能助手平台..."
echo "=================================================="

# 检查端口8888是否被占用
if lsof -i :8888 >/dev/null 2>&1; then
    echo "⚠️  端口8888已被占用，正在关闭相关进程..."
    lsof -ti:8888 | xargs kill -9 >/dev/null 2>&1
    sleep 2
fi

# 检查是否安装了netlify-cli
if ! command -v netlify &> /dev/null; then
    echo "📦 正在安装 Netlify CLI..."
    npm install -g netlify-cli
fi

# 显示项目信息
echo ""
echo "📋 项目信息："
echo "   名称: AI智能助手平台"
echo "   版本: v1.0.0"
echo "   端口: 8888"
echo "   技术: React + PWA"
echo ""

# 启动开发服务器
echo "🌐 启动开发服务器..."
echo "=================================================="
echo ""
echo "🎯 访问地址："
echo "   主页: http://localhost:8888"
echo "   旅游规划: http://localhost:8888/travel_planner_frontend.html"
echo ""
echo "💡 功能特色："
echo "   ✅ 现代化UI设计"
echo "   ✅ PWA支持（离线缓存）"
echo "   ✅ 响应式布局"
echo "   ✅ 旅游智能体集成"
echo "   🔄 商用分析智能体（即将推出）"
echo "   🔄 知识学习智能体（即将推出）"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================================="

# 启动Netlify开发服务器
npx netlify dev --port 8888