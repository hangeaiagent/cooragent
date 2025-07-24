#!/usr/bin/env python3
"""
Cooragent代码生成器CLI启动脚本
带有详细的中文日志输出，方便跟踪启动和运行过程
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.api.generator_api import GeneratorServer
from src.utils.chinese_names import generate_chinese_log

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/generator.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数 - 启动Cooragent代码生成器"""
    
    # 启动前检查日志
    startup_init_log = generate_chinese_log(
        "generator_startup_init",
        "🚀 Cooragent代码生成器启动初始化",
        startup_time=datetime.now().isoformat(),
        python_version=sys.version.split()[0],
        working_directory=str(Path.cwd())
    )
    logger.info(f"中文日志: {startup_init_log['data']['message']}")
    
    try:
        # 检查必要的目录
        dirs_to_check = ["logs", "generated_projects", "src"]
        for dir_name in dirs_to_check:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # 目录创建日志
                dir_created_log = generate_chinese_log(
                    "directory_created",
                    f"📁 创建必要目录: {dir_name}",
                    directory_name=dir_name,
                    directory_path=str(dir_path.absolute()),
                    creation_status="success"
                )
                logger.info(f"中文日志: {dir_created_log['data']['message']}")
        
        # 服务器初始化日志
        server_init_log = generate_chinese_log(
            "server_initialization",
            "⚙️ 正在初始化GeneratorServer实例",
            server_type="GeneratorServer",
            host="0.0.0.0",
            port=8888,
            initialization_stage="server_creation"
        )
        logger.info(f"中文日志: {server_init_log['data']['message']}")
        
        # 创建服务器实例
        server = GeneratorServer(host="0.0.0.0", port=8888)
        
        # 服务器配置完成日志
        server_config_log = generate_chinese_log(
            "server_configured",
            "✅ GeneratorServer配置完成，准备启动Web服务",
            server_host="0.0.0.0",
            server_port=8888,
            web_interface_url="http://localhost:8888",
            api_docs_url="http://localhost:8888/docs",
            configuration_status="ready"
        )
        logger.info(f"中文日志: {server_config_log['data']['message']}")
        
        # 服务启动日志
        service_start_log = generate_chinese_log(
            "service_starting",
            "🌐 正在启动Cooragent代码生成器Web服务",
            service_type="FastAPI",
            startup_mode="production",
            access_info={
                "web_ui": "http://localhost:8888",
                "api_docs": "http://localhost:8888/docs",
                "health_check": "http://localhost:8888/health"
            }
        )
        logger.info(f"中文日志: {service_start_log['data']['message']}")
        
        print("🤖 Cooragent代码生成器启动中...")
        print("📱 Web界面: http://localhost:8888")
        print("📋 API文档: http://localhost:8888/docs")
        print("❤️  健康检查: http://localhost:8888/health")
        print("📊 任务管理: http://localhost:8888/api/tasks")
        print("💡 需求示例: http://localhost:8888/api/generate/examples")
        print("")
        print("🔧 基于Cooragent三层智能分析架构:")
        print("   协调器 → 规划器 → 智能体工厂 → 代码生成")
        print("")
        print("按 Ctrl+C 停止服务")
        print("-" * 50)
        
        # 启动服务器
        server.run()
        
    except KeyboardInterrupt:
        # 优雅关闭日志
        shutdown_log = generate_chinese_log(
            "service_shutdown",
            "👋 接收到停止信号，正在优雅关闭Cooragent代码生成器",
            shutdown_reason="keyboard_interrupt",
            shutdown_time=datetime.now().isoformat(),
            graceful_shutdown=True
        )
        logger.info(f"中文日志: {shutdown_log['data']['message']}")
        
        print("\n🛑 正在停止Cooragent代码生成器...")
        print("👋 感谢使用，再见！")
        
    except Exception as e:
        # 启动错误日志
        startup_error_log = generate_chinese_log(
            "startup_error",
            f"❌ Cooragent代码生成器启动失败: {str(e)}",
            error_type=type(e).__name__,
            error_message=str(e),
            startup_stage="service_launch",
            error_time=datetime.now().isoformat()
        )
        logger.error(f"中文日志: {startup_error_log['data']['message']}")
        
        print(f"❌ 启动失败: {e}")
        print("💡 请检查:")
        print("   1. 端口8888是否被占用")
        print("   2. 依赖包是否正确安装")
        print("   3. 环境变量是否正确配置")
        
        sys.exit(1)

if __name__ == "__main__":
    main() 