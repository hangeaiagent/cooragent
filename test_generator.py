#!/usr/bin/env python3
"""
简单的代码生成器功能验证脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 首先加载环境变量
from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from src.generator.cooragent_generator import CooragentProjectGenerator
        print("✅ CooragentProjectGenerator 导入成功")
    except Exception as e:
        print(f"❌ CooragentProjectGenerator 导入失败: {e}")
        return False
    
    try:
        from src.generator.template_renderer import TemplateRenderer
        print("✅ TemplateRenderer 导入成功")
    except Exception as e:
        print(f"❌ TemplateRenderer 导入失败: {e}")
        return False
    
    try:
        from src.generator.config_generator import ConfigGenerator
        print("✅ ConfigGenerator 导入成功")
    except Exception as e:
        print(f"❌ ConfigGenerator 导入失败: {e}")
        return False
    
    try:
        from src.api.generator_api import GeneratorServer
        print("✅ GeneratorServer 导入成功")
    except Exception as e:
        print(f"❌ GeneratorServer 导入失败: {e}")
        return False
    
    try:
        from src.utils.file_cleaner import FileCleanupManager
        print("✅ FileCleanupManager 导入成功")
    except Exception as e:
        print(f"❌ FileCleanupManager 导入失败: {e}")
        return False
    
    return True

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")
    
    try:
        from src.generator.cooragent_generator import CooragentProjectGenerator
        
        # 创建生成器实例
        generator = CooragentProjectGenerator("test_output")
        print("✅ 代码生成器实例创建成功")
        
        # 测试组件映射
        components = generator.core_components
        if "interface" in components and "workflow" in components:
            print("✅ 核心组件映射配置正确")
        else:
            print("❌ 核心组件映射配置错误")
            return False
        
        # 测试工具映射
        tool_mapping = generator.tool_mapping
        if "tavily_tool" in tool_mapping and "python_repl_tool" in tool_mapping:
            print("✅ 工具映射配置正确")
        else:
            print("❌ 工具映射配置错误")
            return False
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False
    
    return True

async def test_template_rendering():
    """测试模板渲染"""
    print("\n🧪 测试模板渲染...")
    
    try:
        from src.generator.template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        
        # 创建测试配置
        test_config = {
            "agents": [],
            "tools": ["tavily_tool", "python_repl_tool"],
            "project_info": {
                "user_input": "测试项目",
                "generated_at": "2025-01-01T00:00:00",
                "user_id": "test_user"
            }
        }
        
        # 测试Dockerfile渲染
        dockerfile_content = await renderer.render_dockerfile(test_config)
        if "FROM python:3.12-slim" in dockerfile_content:
            print("✅ Dockerfile 模板渲染成功")
        else:
            print("❌ Dockerfile 模板渲染失败")
            return False
        
        print("✅ 模板渲染功能正常")
        
    except Exception as e:
        print(f"❌ 模板渲染测试失败: {e}")
        return False
    
    return True

async def main():
    """主测试函数"""
    print("🤖 Cooragent代码生成器功能验证")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 导入测试失败")
        return False
    
    # 测试基本功能
    if not test_basic_functionality():
        print("\n❌ 基本功能测试失败")
        return False
    
    # 测试模板渲染
    if not await test_template_rendering():
        print("\n❌ 模板渲染测试失败")
        return False
    
    print("\n🎉 所有测试通过！")
    print("✅ 代码生成器已准备就绪")
    print("\n📋 使用说明:")
    print("  1. 启动Web服务器: python generator_cli.py server")
    print("  2. 访问: http://localhost:8000")
    print("  3. 输入需求描述，生成多智能体项目")
    
    return True

if __name__ == "__main__":
    import asyncio
    
    try:
        result = asyncio.run(main())
        if not result:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1) 