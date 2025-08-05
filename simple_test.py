#!/usr/bin/env python3
"""
简单的代码生成器验证脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 首先加载环境变量
from dotenv import load_dotenv
load_dotenv()

def main():
    """主测试函数"""
    print("🤖 Cooragent代码生成器基础验证")
    print("=" * 50)
    
    # 验证环境变量
    print("🔧 检查环境变量...")
    required_vars = ['BASIC_API_KEY', 'TAVILY_API_KEY', 'CODE_API_KEY']
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: 已配置")
        else:
            print(f"❌ {var}: 未配置")
    
    # 验证目录结构
    print("\n📁 检查项目结构...")
    required_dirs = [
        'src/generator',
        'src/api', 
        'src/utils',
        'src/workflow',
        'src/manager'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}: 存在")
        else:
            print(f"❌ {dir_path}: 不存在")
    
    # 验证关键文件
    print("\n📄 检查关键文件...")
    required_files = [
        'src/generator/cooragent_generator.py',
        'src/generator/template_renderer.py',
        'src/generator/config_generator.py',
        'src/api/generator_api.py',
        'generator_cli.py'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}: 存在")
        else:
            print(f"❌ {file_path}: 不存在")
    
    # 测试CLI工具
    print("\n⚡ 测试CLI工具...")
    try:
        # 测试帮助命令
        import subprocess
        result = subprocess.run([sys.executable, 'generator_cli.py', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CLI工具基础功能正常")
        else:
            print(f"❌ CLI工具执行失败: {result.stderr}")
    except Exception as e:
        print(f"❌ CLI工具测试失败: {e}")
    
    print("\n🎉 基础验证完成！")
    print("\n📋 下一步操作:")
    print("  1. 启动Web服务器:")
    print("     python generator_cli.py server --port 8080")
    print("  2. 浏览器访问:")
    print("     http://localhost:8080")
    print("  3. 或者直接生成项目:")
    print("     python generator_cli.py generate \"创建一个数据分析工具\"")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        sys.exit(1) 