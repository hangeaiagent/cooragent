#!/bin/bash

# =============================================================================
# Cooragent服务状态检查脚本
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置参数
MAIN_PORT=8000
NETLIFY_PORT=8888

echo -e "${CYAN}"
echo "======================================================"
echo "🚀 Cooragent服务状态检查"
echo "======================================================"
echo -e "${NC}"

# 检查主服务器
echo -e "${BLUE}[检查主服务器]${NC}"
if lsof -ti :$MAIN_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 主服务器 (端口 $MAIN_PORT)${NC} - 运行中"
    
    # 获取进程信息
    main_pid=$(lsof -ti :$MAIN_PORT | head -1)
    if [ -n "$main_pid" ]; then
        process_info=$(ps -p $main_pid -o pid,etime,comm --no-headers 2>/dev/null)
        echo "   📊 进程信息: $process_info"
    fi
    
    echo "   🌐 Web界面: http://localhost:$MAIN_PORT/"
    echo "   📋 API文档: http://localhost:$MAIN_PORT/docs"
    echo "   💚 健康检查: http://localhost:$MAIN_PORT/health"
    
    # 测试健康检查
    if curl -s "http://localhost:$MAIN_PORT/health" > /dev/null 2>&1; then
        echo -e "   ${GREEN}🩺 健康状态: 正常${NC}"
    else
        echo -e "   ${YELLOW}🩺 健康状态: 响应异常${NC}"
    fi
else
    echo -e "${RED}❌ 主服务器 (端口 $MAIN_PORT)${NC} - 未运行"
fi

echo ""

# 检查Netlify服务器
echo -e "${BLUE}[检查Netlify服务器]${NC}"
if lsof -ti :$NETLIFY_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Netlify服务器 (端口 $NETLIFY_PORT)${NC} - 运行中"
    echo "   🌐 Netlify界面: http://localhost:$NETLIFY_PORT/"
else
    echo -e "${YELLOW}⚪ Netlify服务器 (端口 $NETLIFY_PORT)${NC} - 未运行"
fi

echo ""

# 显示管理命令
echo -e "${CYAN}======== 管理命令 ========${NC}"
echo "🔄 重启服务: ./sh/restart.sh"
echo "📊 查看状态: ./sh/status.sh"
echo "📋 查看主服务器日志: tail -f logs/server.log"
echo "🔴 停止主服务器: pkill -f 'generator_cli.py'"
echo "🌐 打开Web界面: open http://localhost:8000"

echo "" 