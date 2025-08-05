#!/usr/bin/env python3
"""
Cooragent代码生成器CLI工具

用于启动代码生成器服务或执行单次代码生成任务
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.api.generator_api import GeneratorServer
from src.generator.cooragent_generator import CooragentProjectGenerator
from src.manager import agent_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def generate_single_project(content: str, user_id: str = None, output_dir: str = "generated_projects"):
    """单次项目生成"""
    logger.info("初始化代码生成器...")
    
    # 初始化agent_manager
    await agent_manager.initialize()
    
    # 创建生成器
    generator = CooragentProjectGenerator(output_dir)
    
    try:
        # 生成项目
        zip_path = await generator.generate_project(content, user_id)
        logger.info(f"✅ 项目生成成功: {zip_path}")
        print(f"\n🎉 代码生成完成！")
        print(f"📦 下载路径: {zip_path}")
        print(f"💡 您可以解压文件并按照README.md中的说明部署运行")
        
        return zip_path
        
    except Exception as e:
        logger.error(f"❌ 项目生成失败: {e}")
        print(f"\n❌ 生成失败: {e}")
        return None


def start_web_server(host: str = "0.0.0.0", port: int = 8000):
    """启动Web服务器"""
    logger.info("启动Cooragent代码生成器Web服务...")
    
    server = GeneratorServer(host=host, port=port)
    server.run()


async def test_generator():
    """测试代码生成器功能"""
    test_cases = [
        {
            "name": "股票分析系统",
            "content": "创建一个股票分析专家智能体，查看小米股票走势，分析相关新闻，预测股价趋势并给出投资建议"
        },
        {
            "name": "数据分析工具",
            "content": "开发一个数据分析助手，支持Python数据处理、统计分析和可视化图表生成"
        }
    ]
    
    logger.info("开始测试代码生成器...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {test_case['name']}")
        print(f"📋 需求: {test_case['content']}")
        
        zip_path = await generate_single_project(
            content=test_case['content'],
            user_id=f"test_user_{i}",
            output_dir="test_output"
        )
        
        if zip_path:
            print(f"✅ 测试用例 {i} 通过")
        else:
            print(f"❌ 测试用例 {i} 失败")
        
        print("-" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Cooragent代码生成器CLI工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动Web服务器 (推荐)
  python generator_cli.py server --port 8000
  
  # 单次生成项目
  python generator_cli.py generate "创建一个股票分析系统"
  
  # 指定用户ID和输出目录
  python generator_cli.py generate "数据分析工具" --user-id demo --output output/
  
  # 运行测试
  python generator_cli.py test
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 服务器启动命令
    server_parser = subparsers.add_parser("server", help="启动Web服务器")
    server_parser.add_argument(
        "--host", default="0.0.0.0", help="服务器主机地址 (默认: 0.0.0.0)"
    )
    server_parser.add_argument(
        "--port", type=int, default=8000, help="服务器端口 (默认: 8000)"
    )
    
    # 单次生成命令
    generate_parser = subparsers.add_parser("generate", help="生成单个项目")
    generate_parser.add_argument("content", help="项目需求描述")
    generate_parser.add_argument(
        "--user-id", help="用户ID (可选)"
    )
    generate_parser.add_argument(
        "--output", default="generated_projects", help="输出目录 (默认: generated_projects)"
    )
    
    # 测试命令
    test_parser = subparsers.add_parser("test", help="运行测试用例")
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "server":
            print(f"""
🤖 Cooragent代码生成器
==========================================

🚀 启动Web服务器...
📱 Web界面: http://{args.host}:{args.port}
📋 API文档: http://{args.host}:{args.port}/docs
⚡ 健康检查: http://{args.host}:{args.port}/health

💡 使用提示:
  - 在Web界面输入需求，一键生成多智能体应用
  - 生成的项目基于Cooragent架构，开箱即用
  - 支持多种工具和智能体类型

按 Ctrl+C 停止服务器
==========================================
            """)
            start_web_server(args.host, args.port)
            
        elif args.command == "generate":
            print(f"""
🤖 Cooragent代码生成器 - 单次生成模式
==========================================

📋 需求描述: {args.content}
👤 用户ID: {args.user_id or '自动生成'}
📁 输出目录: {args.output}

🔄 开始生成...
            """)
            asyncio.run(generate_single_project(
                content=args.content,
                user_id=args.user_id,
                output_dir=args.output
            ))
            
        elif args.command == "test":
            print("""
🧪 Cooragent代码生成器 - 测试模式
==========================================

运行内置测试用例，验证生成器功能...
            """)
            asyncio.run(test_generator())
    
    except KeyboardInterrupt:
        print("\n\n👋 再见！感谢使用Cooragent代码生成器")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 