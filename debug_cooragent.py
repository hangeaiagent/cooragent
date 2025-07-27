#!/usr/bin/env python3
"""
Cooragent项目Conda环境调试测试文件
基于现有的Conda环境配置进行调试验证
"""

import sys
import os
from pathlib import Path

# 确保项目路径在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_conda_environment():
    """测试Conda环境配置"""
    print("🐍 Conda环境测试")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")
    print(f"CONDA_DEFAULT_ENV: {os.environ.get('CONDA_DEFAULT_ENV', '未设置')}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '未设置')}")
    print()

def test_project_imports():
    """测试项目模块导入"""
    print("📦 Cooragent模块导入测试")
    print("=" * 60)
    
    import_results = {}
    
    # 测试基础调试工具
    try:
        import debugpy
        print("✅ debugpy 导入成功")
        import_results['debugpy'] = True
    except ImportError as e:
        print(f"❌ debugpy 导入失败: {e}")
        import_results['debugpy'] = False
    
    # 测试Web框架
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI & Uvicorn 导入成功")
        import_results['web'] = True
    except ImportError as e:
        print(f"❌ Web框架导入失败: {e}")
        import_results['web'] = False
    
    # 测试项目核心模块
    modules_to_test = [
        ("API服务", "src.api.generator_api", "GeneratorServer"),
        ("工作流协调", "src.workflow.coor_task", "coordinator_node"),
        ("代码生成器", "src.generator.cooragent_generator", "CooragentProjectGenerator"),
        ("提示词模板", "src.prompts.template", "load_prompt_template"),
    ]
    
    for module_name, module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name} 导入成功")
            import_results[module_name] = True
        except ImportError as e:
            print(f"❌ {module_name} 导入失败: {e}")
            import_results[module_name] = False
        except AttributeError as e:
            print(f"⚠️  {module_name} 模块导入成功但缺少类: {e}")
            import_results[module_name] = "partial"
    
    print()
    return import_results

def test_environment_files():
    """测试环境配置文件"""
    print("📋 环境配置文件检查")
    print("=" * 60)
    
    config_files = {
        ".env": "环境变量配置",
        ".env.example": "环境变量示例",
        "generator_cli.py": "CLI入口文件",
        "cli.py": "命令行工具",
        "src/": "源代码目录",
        "config/": "配置文件目录"
    }
    
    for file_path, description in config_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description}: {file_path} (不存在)")
    
    print()

def test_debug_breakpoints():
    """测试调试断点功能"""
    print("🔧 调试断点测试")
    print("=" * 60)
    
    # 创建一些测试数据
    test_data = {
        "project_name": "Cooragent",
        "environment": "conda",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "features": [
            "智能体生成",
            "工作流协调", 
            "代码生成",
            "多模态支持"
        ]
    }
    
    # 在这一行设置断点进行调试
    debug_checkpoint_1 = "第一个调试检查点 - 检查test_data变量"
    
    # 处理数据
    processed_data = {}
    for key, value in test_data.items():
        if isinstance(value, list):
            processed_data[key] = f"列表包含{len(value)}个元素"
        else:
            processed_data[key] = str(value)
    
    # 在这一行设置断点查看处理后的数据
    debug_checkpoint_2 = "第二个调试检查点 - 检查processed_data变量"
    
    print(f"🔍 原始数据: {test_data}")
    print(f"🔍 处理后数据: {processed_data}")
    print(f"🔍 调试点1: {debug_checkpoint_1}")
    print(f"🔍 调试点2: {debug_checkpoint_2}")
    
    return test_data, processed_data

async def test_async_debugging():
    """测试异步函数调试"""
    import asyncio
    
    print("⚡ 异步函数调试测试")
    print("=" * 60)
    
    async def simulate_api_call(endpoint, delay=0.1):
        """模拟API调用"""
        print(f"🌐 调用API: {endpoint}")
        
        # 在这里设置断点观察异步执行
        await asyncio.sleep(delay)
        
        result = {
            "endpoint": endpoint,
            "status": "success",
            "data": f"来自{endpoint}的响应数据"
        }
        
        # 在这里设置断点查看返回结果
        return result
    
    # 测试多个异步调用
    endpoints = ["/api/generate", "/api/status", "/api/health"]
    tasks = [simulate_api_call(endpoint) for endpoint in endpoints]
    
    # 在这里设置断点观察任务列表
    results = await asyncio.gather(*tasks)
    
    print("✅ 异步调用完成:")
    for result in results:
        print(f"  📊 {result}")
    
    return results

def test_generator_cli_simulation():
    """模拟generator_cli.py的调试"""
    print("🚀 Generator CLI模拟调试")
    print("=" * 60)
    
    # 模拟CLI参数
    cli_args = {
        "command": "server",
        "host": "0.0.0.0", 
        "port": 8000,
        "debug": True
    }
    
    # 在这里设置断点检查CLI参数
    debug_point_cli = "CLI参数解析断点"
    
    print(f"🔧 CLI参数: {cli_args}")
    print(f"🔍 调试点: {debug_point_cli}")
    
    # 模拟服务器启动过程
    startup_steps = [
        "解析命令行参数",
        "加载环境配置",
        "初始化FastAPI应用",
        "配置路由和中间件",
        "启动Uvicorn服务器"
    ]
    
    for i, step in enumerate(startup_steps, 1):
        print(f"📋 步骤{i}: {step}")
        # 在每个步骤设置断点观察启动过程
        step_debug = f"启动步骤{i}调试点"
    
    return cli_args, startup_steps

def main():
    """主调试函数"""
    print("🎯 Cooragent Conda环境调试测试启动")
    print("=" * 80)
    
    # 测试Conda环境
    test_conda_environment()
    
    # 测试模块导入
    import_results = test_project_imports()
    
    # 测试配置文件
    test_environment_files()
    
    # 测试调试功能
    debug_data = test_debug_breakpoints()
    
    # 测试CLI模拟
    cli_data = test_generator_cli_simulation()
    
    print("=" * 80)
    print("🎉 Conda环境调试测试完成!")
    print()
    print("💡 Cursor调试使用说明:")
    print("1. 在Cursor中打开此文件 (debug_cooragent.py)")
    print("2. 在需要调试的代码行左侧点击设置断点 (红色圆点)")
    print("3. 按F5启动调试或选择调试配置:")
    print("   - '🐍 Python: 当前文件' - 调试当前文件")
    print("   - '🚀 Cooragent: 启动服务器' - 调试服务器启动")
    print("4. 使用调试控制:")
    print("   - F5: 继续执行")
    print("   - F10: 单步执行(跳过函数)")  
    print("   - F11: 单步执行(进入函数)")
    print("   - Shift+F11: 跳出函数")
    print("   - Shift+F5: 停止调试")
    print("5. 在左侧调试面板查看:")
    print("   - 变量值")
    print("   - 调用堆栈")
    print("   - 断点列表")
    print("6. 在调试控制台执行Python表达式")
    print()
    print("🔧 环境配置信息:")
    print(f"   - Python: {sys.executable}")
    print(f"   - 环境: conda cooragent")
    print(f"   - 项目: {project_root}")
    
    return {
        "environment": "conda_cooragent",
        "import_results": import_results,
        "debug_data": debug_data,
        "cli_data": cli_data
    }

if __name__ == "__main__":
    # 在这一行设置断点开始整个调试流程
    result = main()
    print(f"\n🏆 最终测试结果: {result}")
    
    # 测试异步调试
    print("\n⏳ 启动异步调试测试...")
    import asyncio
    async_result = asyncio.run(test_async_debugging())
    print(f"🏆 异步测试结果: {async_result}") 