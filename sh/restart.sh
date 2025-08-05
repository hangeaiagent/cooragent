#!/bin/bash

# =============================================================================
# Cooragent本地开发环境重启脚本
# 功能：检查端口占用、关闭相关进程、重新启动服务
# 作者：Cooragent Team
# 日期：2024-07-24
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置参数
MAIN_PORT=8000
NETLIFY_PORT=8888

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 打印banner
print_banner() {
    echo -e "${CYAN}"
    echo "======================================================"
    echo "🤖 Cooragent本地开发环境重启脚本"
    echo "======================================================"
    echo -e "${NC}"
}

# 检查并关闭端口占用
check_and_kill_port() {
    local port=$1
    local port_name=$2
    
    log_step "检查端口 $port ($port_name) 的占用情况..."
    
    # 查找占用端口的进程
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        log_warning "发现端口 $port 被以下进程占用："
        echo "$pids" | while read pid; do
            if [ -n "$pid" ]; then
                local process_info=$(ps -p $pid -o pid,ppid,comm --no-headers 2>/dev/null)
                if [ -n "$process_info" ]; then
                    echo "  PID: $pid - $process_info"
                fi
            fi
        done
        
        log_step "正在关闭端口 $port 上的进程..."
        echo "$pids" | while read pid; do
            if [ -n "$pid" ]; then
                kill -9 $pid 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_success "已终止进程 PID: $pid"
                else
                    log_error "无法终止进程 PID: $pid"
                fi
            fi
        done
        
        # 等待进程完全关闭
        sleep 2
        log_success "端口 $port 已释放"
    else
        log_success "端口 $port 未被占用"
    fi
}

# 关闭Cooragent相关进程
kill_cooragent_processes() {
    log_step "查找并关闭Cooragent相关进程..."
    
    # 查找generator_cli.py相关进程
    local generator_pids=$(pgrep -f "generator_cli.py" 2>/dev/null)
    if [ -n "$generator_pids" ]; then
        log_warning "发现generator_cli.py进程，正在关闭..."
        echo "$generator_pids" | while read pid; do
            if [ -n "$pid" ]; then
                kill -9 $pid 2>/dev/null
                log_success "已终止generator_cli.py进程 PID: $pid"
            fi
        done
    fi
    
    # 查找netlify dev相关进程
    local netlify_pids=$(pgrep -f "netlify dev" 2>/dev/null)
    if [ -n "$netlify_pids" ]; then
        log_warning "发现netlify dev进程，正在关闭..."
        echo "$netlify_pids" | while read pid; do
            if [ -n "$pid" ]; then
                kill -9 $pid 2>/dev/null
                log_success "已终止netlify dev进程 PID: $pid"
            fi
        done
    fi
    
    # 等待进程完全关闭
    sleep 2
}

# 检查环境
check_environment() {
    log_step "检查运行环境..."
    
    # 检查Python
    if ! command -v python &> /dev/null; then
        log_error "未找到python命令"
        return 1
    fi
    
    # 检查项目文件
    if [ ! -f "generator_cli.py" ]; then
        log_error "未找到generator_cli.py文件，请确保在项目根目录执行"
        return 1
    fi
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在"
        if [ -f ".env.example" ]; then
            log_info "发现.env.example文件，正在复制为.env..."
            cp .env.example .env
            log_success "已复制.env.example为.env"
            log_warning "请编辑.env文件并配置API密钥"
        fi
    else
        log_success "找到.env文件"
    fi
    
    # 检查依赖
    if ! python -c "import dotenv" 2>/dev/null; then
        log_warning "缺少关键依赖，正在安装..."
        pip install -e . || {
            log_error "依赖安装失败，请手动运行: pip install -e ."
            return 1
        }
        log_success "依赖安装完成"
    else
        log_success "环境检查通过"
    fi
    
    return 0
}

# 启动主服务器
start_main_server() {
    log_step "启动Cooragent主服务器 (端口:$MAIN_PORT)..."
    
    # 启动服务器
    log_info "执行命令: python generator_cli.py server --host 0.0.0.0 --port $MAIN_PORT"
    
    # 确保日志目录存在
    mkdir -p logs
    
    # 在后台启动服务器
    nohup python generator_cli.py server --host 0.0.0.0 --port $MAIN_PORT > logs/server.log 2>&1 &
    local server_pid=$!
    
    # 等待服务器启动
    log_info "等待服务器启动..."
    sleep 5
    
    # 检查服务器是否启动成功
    if kill -0 $server_pid 2>/dev/null; then
        log_success "主服务器启动成功 (PID: $server_pid)"
        
        # 测试端口是否可访问
        sleep 3
        if lsof -ti :$MAIN_PORT > /dev/null 2>&1; then
            log_success "服务器端口检查通过"
            log_info "🌐 Web界面: http://localhost:$MAIN_PORT/"
            log_info "📋 API文档: http://localhost:$MAIN_PORT/docs"
            log_info "💚 健康检查: http://localhost:$MAIN_PORT/health"
        else
            log_warning "端口检查失败，但进程仍在运行"
        fi
        
        return 0
    else
        log_error "主服务器启动失败"
        # 输出错误日志
        if [ -f "logs/server.log" ]; then
            log_error "错误日志："
            tail -10 logs/server.log
        fi
        return 1
    fi
}

# 显示运行状态
show_status() {
    log_step "显示服务状态..."
    
    echo ""
    echo -e "${CYAN}======== 服务状态 ========${NC}"
    
    # 检查主服务器
    if lsof -ti :$MAIN_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 主服务器 (端口 $MAIN_PORT)${NC} - 运行中"
        echo "   🌐 Web界面: http://localhost:$MAIN_PORT/"
        echo "   📋 API文档: http://localhost:$MAIN_PORT/docs"
        echo "   💚 健康检查: http://localhost:$MAIN_PORT/health"
    else
        echo -e "${RED}❌ 主服务器 (端口 $MAIN_PORT)${NC} - 未运行"
    fi
    
    # 检查Netlify服务器
    if lsof -ti :$NETLIFY_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Netlify服务器 (端口 $NETLIFY_PORT)${NC} - 运行中"
        echo "   🌐 Netlify界面: http://localhost:$NETLIFY_PORT/"
    else
        echo -e "${YELLOW}⚪ Netlify服务器 (端口 $NETLIFY_PORT)${NC} - 未运行"
    fi
    
    echo ""
    echo -e "${CYAN}======== 管理命令 ========${NC}"
    echo "📊 查看主服务器日志: tail -f logs/server.log"
    echo "🔴 停止主服务器: pkill -f 'generator_cli.py'"
    echo "🔄 重启服务: ./sh/restart.sh"
    
    # 显示当前进程
    local running_pids=$(pgrep -f "generator_cli.py" 2>/dev/null)
    if [ -n "$running_pids" ]; then
        echo ""
        echo -e "${CYAN}======== 运行中的进程 ========${NC}"
        echo "$running_pids" | while read pid; do
            if [ -n "$pid" ]; then
                local process_info=$(ps -p $pid -o pid,ppid,etime,comm --no-headers 2>/dev/null)
                if [ -n "$process_info" ]; then
                    echo "PID: $process_info"
                fi
            fi
        done
    fi
    
    echo ""
}

# 主函数
main() {
    print_banner
    
    log_info "开始Cooragent本地环境重启流程..."
    
    # 1. 检查并关闭端口占用
    check_and_kill_port $MAIN_PORT "Cooragent主服务器"
    check_and_kill_port $NETLIFY_PORT "Netlify开发服务器"
    
    # 2. 关闭Cooragent相关进程
    kill_cooragent_processes
    
    # 3. 检查环境
    if ! check_environment; then
        log_error "环境检查失败，请手动检查环境配置"
        exit 1
    fi
    
    # 4. 启动主服务器
    if ! start_main_server; then
        log_error "主服务器启动失败"
        echo ""
        echo -e "${YELLOW}💡 手动启动建议：${NC}"
        echo "1. 确保已激活conda环境: conda activate cooragent"
        echo "2. 安装依赖: pip install -e ."
        echo "3. 启动服务器: python generator_cli.py server --port 8000"
        exit 1
    fi
    
    # 5. 显示状态
    show_status
    
    log_success "🎉 Cooragent本地环境重启完成！"
    
    # 6. 提示用户
    echo ""
    echo -e "${YELLOW}💡 使用提示：${NC}"
    echo "- 服务器已在后台运行"
    echo "- 访问 http://localhost:8000 使用Cooragent代码生成器"
    echo "- 使用 tail -f logs/server.log 查看实时日志"
    echo "- 使用 pkill -f 'generator_cli.py' 停止服务器"
    echo ""
}

# 执行主函数
main "$@" 