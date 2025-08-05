#!/usr/bin/env python3
"""
管理员工具：创建标准旅游智能体

用于初始化和创建所有标准旅游智能体模板。
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量避免API密钥问题
os.environ.setdefault('TAVILY_API_KEY', 'test_key_for_template_creation')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_standard_travel_agents():
    """管理员工具：创建标准旅游智能体"""
    
    print("🏗️ 开始创建标准旅游智能体...")
    
    try:
        # 延迟导入，避免启动时的依赖问题
        from src.manager.agents import AgentManager
        from src.manager.travel_agent_templates import TravelAgentTemplateManager
        from src.utils.path_utils import get_project_root
        
        # 初始化AgentManager
        print("📋 初始化AgentManager...")
        
        tools_dir = get_project_root() / "store" / "tools"
        agents_dir = get_project_root() / "store" / "agents"
        prompts_dir = get_project_root() / "store" / "prompts"
        
        # 确保目录存在
        for directory in [tools_dir, agents_dir, prompts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        agent_manager = AgentManager(tools_dir, agents_dir, prompts_dir)
        await agent_manager.initialize(user_agent_flag=False)
        
        print(f"✅ AgentManager初始化完成，当前可用智能体: {len(agent_manager.available_agents)} 个")
        
        # 创建旅游智能体模板管理器
        print("🏖️ 创建旅游智能体模板管理器...")
        travel_template_manager = TravelAgentTemplateManager(agent_manager)
        
        # 列出将要创建的模板
        all_templates = travel_template_manager.list_all_templates()
        print(f"📋 准备创建 {len(all_templates)} 个旅游智能体:")
        
        for template_id, template in all_templates.items():
            print(f"   - {template_id}: {template['nick_name']}")
        
        # 执行创建
        print("\n🚀 开始创建标准旅游智能体...")
        results = await travel_template_manager.create_standard_travel_agents()
        
        # 统计结果
        success_count = sum(1 for result in results.values() if result is True)
        existing_count = sum(1 for result in results.values() if result == "already_exists")
        failed_count = sum(1 for result in results.values() if result is False)
        
        print("\n📊 创建结果统计:")
        print(f"   ✅ 成功创建: {success_count} 个")
        print(f"   ⚠️ 已存在: {existing_count} 个")
        print(f"   ❌ 创建失败: {failed_count} 个")
        
        # 详细结果
        print("\n📋 详细创建结果:")
        for template_id, result in results.items():
            template = all_templates[template_id]
            if result is True:
                status = "✅ 成功创建"
            elif result == "already_exists":
                status = "⚠️ 已存在"
            else:
                status = "❌ 创建失败"
            
            print(f"   {status} {template_id}: {template['nick_name']}")
        
        # 验证创建结果
        print("\n🔍 验证创建结果...")
        
        # 重新加载智能体列表
        updated_agent_manager = AgentManager(tools_dir, agents_dir, prompts_dir)
        await updated_agent_manager.initialize(user_agent_flag=False)
        
        default_agents = await updated_agent_manager._list_default_agents()
        travel_agents = [agent for agent in default_agents 
                        if agent.agent_name in all_templates.keys()]
        
        print(f"✅ 验证完成，共找到 {len(travel_agents)} 个旅游智能体:")
        for agent in travel_agents:
            tools_count = len(agent.selected_tools)
            print(f"   - {agent.agent_name} ({agent.nick_name}): {tools_count} 个工具")
        
        # 生成报告
        total_agents = len(updated_agent_manager.available_agents)
        success_rate = ((success_count + existing_count) / len(results)) * 100
        
        print(f"\n🎉 旅游智能体创建完成!")
        print(f"   - 创建成功率: {success_rate:.1f}%")
        print(f"   - 旅游智能体总数: {len(travel_agents)}")
        print(f"   - 系统智能体总数: {total_agents}")
        
        # 保存创建报告
        report_file = get_project_root() / "store" / "travel_agents_creation_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("旅游智能体创建报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"创建时间: {asyncio.get_event_loop().time()}\n")
            f.write(f"模板总数: {len(all_templates)}\n")
            f.write(f"成功创建: {success_count}\n")
            f.write(f"已存在: {existing_count}\n")
            f.write(f"创建失败: {failed_count}\n")
            f.write(f"成功率: {success_rate:.1f}%\n\n")
            
            f.write("详细结果:\n")
            for template_id, result in results.items():
                template = all_templates[template_id]
                f.write(f"- {template_id}: {template['nick_name']} - {result}\n")
        
        print(f"📄 创建报告已保存到: {report_file}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保所有依赖已正确安装")
        return False
    except Exception as e:
        print(f"❌ 创建过程中出现错误: {e}")
        logger.exception("创建失败")
        return False

async def list_existing_agents():
    """列出现有的智能体"""
    
    print("📋 列出现有智能体...")
    
    try:
        from src.manager.agents import AgentManager
        from src.utils.path_utils import get_project_root
        
        tools_dir = get_project_root() / "store" / "tools"
        agents_dir = get_project_root() / "store" / "agents"
        prompts_dir = get_project_root() / "store" / "prompts"
        
        agent_manager = AgentManager(tools_dir, agents_dir, prompts_dir)
        await agent_manager.initialize(user_agent_flag=False)
        
        all_agents = list(agent_manager.available_agents.values())
        default_agents = await agent_manager._list_default_agents()
        
        print(f"📊 智能体统计:")
        print(f"   - 总智能体数: {len(all_agents)}")
        print(f"   - 共享智能体数: {len(default_agents)}")
        
        print(f"\n📋 共享智能体列表:")
        for agent in default_agents:
            tools_count = len(agent.selected_tools)
            print(f"   - {agent.agent_name} ({agent.nick_name}): {tools_count} 个工具")
        
        return True
        
    except Exception as e:
        print(f"❌ 列出智能体时出现错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🏖️  旅游智能体创建工具")
    print("=" * 80)
    
    import argparse
    parser = argparse.ArgumentParser(description="旅游智能体管理工具")
    parser.add_argument("--action", choices=["create", "list"], default="create",
                       help="执行的操作：create=创建智能体，list=列出现有智能体")
    
    args = parser.parse_args()
    
    async def main():
        if args.action == "create":
            success = await create_standard_travel_agents()
        elif args.action == "list":
            success = await list_existing_agents()
        else:
            print("❌ 未知操作")
            success = False
        
        print("\n" + "=" * 80)
        if success:
            print("✅ 操作完成成功")
        else:
            print("❌ 操作未能完成")
        print("=" * 80)
    
    # 运行主程序
    asyncio.run(main()) 