#!/usr/bin/env python3
"""
Cooragent项目调试测试文件
用于验证Cursor Python调试环境配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_environment():
    """测试Python环境配置"""
    print("🐍 Python环境测试")
    print("=" * 50)
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path[:3]}")  # 显示前3个路径
    print()

def test_imports():
    """测试项目模块导入"""
    print("📦 模块导入测试")
    print("=" * 50)
    
    try:
        # 测试导入调试工具
        import debugpy
        print("✅ debugpy 导入成功")
    except ImportError as e:
        print(f"❌ debugpy 导入失败: {e}")
    
    try:
        # 测试导入项目模块
        from src.api.generator_api import GeneratorServer
        print("✅ GeneratorServer 导入成功")
    except ImportError as e:
        print(f"❌ GeneratorServer 导入失败: {e}")
    
    try:
        from src.workflow.coor_task import coordinator_node
        print("✅ coordinator_node 导入成功")
    except ImportError as e:
        print(f"❌ coordinator_node 导入失败: {e}")
    
    try:
        from src.generator.cooragent_generator import CooragentGenerator
        print("✅ CooragentGenerator 导入成功")
    except ImportError as e:
        print(f"❌ CooragentGenerator 导入失败: {e}")
    
    print()

def test_debug_features():
    """测试调试功能"""
    print("🔧 调试功能测试")
    print("=" * 50)
    
    # 设置一些变量用于调试观察
    test_dict = {
        "name": "Cooragent",
        "version": "1.0.0",
        "features": ["智能体生成", "多模态支持", "工作流协调"]
    }
    
    test_list = [1, 2, 3, 4, 5]
    test_string = "这是一个调试测试字符串"
    
    # 在这里设置断点进行调试
    debug_checkpoint = "设置断点在这一行进行调试"
    
    print(f"✅ 测试字典: {test_dict}")
    print(f"✅ 测试列表: {test_list}")
    print(f"✅ 测试字符串: {test_string}")
    print(f"🔍 调试检查点: {debug_checkpoint}")
    
    return test_dict, test_list, test_string

def test_async_function():
    """测试异步函数调试"""
    import asyncio
    
    async def async_test():
        print("🚀 异步函数测试开始")
        await asyncio.sleep(0.1)  # 设置断点在这里
        result = "异步函数执行完成"
        print(f"✅ {result}")
        return result
    
    print("⏳ 运行异步函数...")
    result = asyncio.run(async_test())
    return result

def main():
    """主函数 - 在这里设置断点开始调试"""
    print("🎯 Cooragent调试测试启动")
    print("=" * 60)
    
    # 测试环境
    test_environment()
    
    # 测试导入
    test_imports()
    
    # 测试调试功能
    debug_data = test_debug_features()
    
    # 测试异步函数
    async_result = test_async_function()
    
    print("=" * 60)
    print("🎉 调试测试完成!")
    print("\n💡 调试使用说明:")
    print("1. 在Cursor中打开此文件")
    print("2. 在代码行左侧点击设置断点")
    print("3. 按F5启动调试或选择'🐍 Python: 当前文件'")
    print("4. 使用F10(单步执行)、F11(进入函数)、F5(继续)")
    print("5. 在调试控制台查看变量值")
    
    return {
        "environment": "OK",
        "imports": "OK", 
        "debug_data": debug_data,
        "async_result": async_result
    }

if __name__ == "__main__":
    # 在这一行设置断点开始调试
    result = main()
    print(f"\n�� 最终结果: {result}") 