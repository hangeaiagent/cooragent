#!/usr/bin/env python3
"""
旅游协调器调试脚本
用于分析后台入口和工作流路由逻辑
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent))

async def debug_travel_coordinator():
    """调试旅游协调器入口和路由逻辑"""
    
    print("🔍 旅游协调器调试分析")
    print("=" * 50)
    
    # 导入必要的模块
    try:
        from src.workflow.coor_task import coordinator_node, build_graph
        from src.workflow.travel_coordinator import TravelCoordinator
        from src.workflow.travel_publisher import travel_publisher_node
        from src.workflow.travel_agent_proxy import travel_agent_proxy_node
        print("✅ 成功导入所有旅游工作流模块")
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return
    
    # 测试用例
    test_cases = [
        {
            "name": "上海到北京旅游规划",
            "query": "我想从上海去北京旅游5天，请制定详细的旅游规划",
            "expected_route": "travel_publisher"
        },
        {
            "name": "杭州景点推荐",
            "query": "推荐杭州的热门景点和美食",
            "expected_route": "travel_publisher"
        },
        {
            "name": "非旅游查询",
            "query": "今天天气怎么样？",
            "expected_route": "planner"
        },
        {
            "name": "酒店预订",
            "query": "帮我预订三亚的海景酒店",
            "expected_route": "travel_publisher"
        }
    ]
    
    print(f"\n📊 开始测试 {len(test_cases)} 个用例")
    print("-" * 30)
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {case['name']}")
        print(f"   查询: {case['query']}")
        
        # 构建测试状态
        state = {
            "user_id": "debug_user",
            "workflow_id": f"debug_{i}_{datetime.now().strftime('%H%M%S')}",
            "workflow_mode": "launch",
            "USER_QUERY": case["query"],
            "messages": [
                {"role": "user", "content": case["query"]}
            ]
        }
        
        try:
            # 测试协调器路由决策
            print("   🔄 执行协调器路由...")
            command = await coordinator_node(state)
            
            actual_route = command.goto
            expected_route = case["expected_route"]
            is_correct = actual_route == expected_route
            
            result = {
                "case": case["name"],
                "query": case["query"],
                "expected_route": expected_route,
                "actual_route": actual_route,
                "is_correct": is_correct,
                "state_updates": command.update if hasattr(command, 'update') else {}
            }
            
            results.append(result)
            
            status_icon = "✅" if is_correct else "❌"
            print(f"   {status_icon} 路由结果: {actual_route}")
            
            if not is_correct:
                print(f"   ⚠️  期望路由: {expected_route}")
            
            # 如果路由到travel_publisher，进一步测试
            if actual_route == "travel_publisher":
                print("   🎯 进一步测试Travel Publisher...")
                
                try:
                    publisher_command = await travel_publisher_node(state)
                    selected_agent = publisher_command.update.get("next", "未选择")
                    print(f"   📍 选择的智能体: {selected_agent}")
                    
                    result["selected_agent"] = selected_agent
                    
                    # 测试Agent Proxy
                    if selected_agent != "未选择":
                        print("   🤖 测试Agent Proxy执行...")
                        
                        proxy_state = state.copy()
                        proxy_state.update(publisher_command.update)
                        
                        try:
                            proxy_command = await travel_agent_proxy_node(proxy_state)
                            proxy_result = proxy_command.update.get("simulation_executed", False)
                            
                            result["proxy_executed"] = proxy_result
                            proxy_icon = "✅" if proxy_result else "⚠️"
                            print(f"   {proxy_icon} Agent Proxy执行: {'成功' if proxy_result else '模拟模式'}")
                            
                        except Exception as proxy_e:
                            print(f"   ❌ Agent Proxy执行失败: {proxy_e}")
                            result["proxy_error"] = str(proxy_e)
                
                except Exception as pub_e:
                    print(f"   ❌ Travel Publisher执行失败: {pub_e}")
                    result["publisher_error"] = str(pub_e)
            
        except Exception as e:
            print(f"   ❌ 协调器执行失败: {e}")
            result = {
                "case": case["name"],
                "query": case["query"],
                "error": str(e),
                "is_correct": False
            }
            results.append(result)
    
    # 生成调试报告
    print("\n" + "=" * 50)
    print("📋 调试报告总结")
    print("=" * 50)
    
    correct_routes = sum(1 for r in results if r.get("is_correct", False))
    total_tests = len(results)
    
    print(f"总测试用例: {total_tests}")
    print(f"正确路由: {correct_routes}")
    print(f"成功率: {correct_routes/total_tests*100:.1f}%")
    
    print("\n📊 详细结果:")
    for result in results:
        status = "✅" if result.get("is_correct", False) else "❌"
        print(f"{status} {result['case']}")
        print(f"   查询: {result['query']}")
        print(f"   路由: {result.get('actual_route', '错误')}")
        
        if "selected_agent" in result:
            print(f"   智能体: {result['selected_agent']}")
        
        if "proxy_executed" in result:
            proxy_status = "✅" if result["proxy_executed"] else "🎭"
            print(f"   执行: {proxy_status}")
        
        if "error" in result:
            print(f"   错误: {result['error']}")
        
        print()
    
    # 保存调试报告
    report_file = Path("debug_travel_coordinator_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "correct_routes": correct_routes,
                "success_rate": correct_routes/total_tests*100
            },
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📄 调试报告已保存到: {report_file}")
    
    return results

async def analyze_backend_entry_points():
    """分析后台入口点"""
    
    print("\n🔍 后台入口点分析")
    print("=" * 50)
    
    entry_points = [
        {
            "name": "Web Server API",
            "file": "generator_cli.py",
            "function": "server",
            "description": "主要的Web服务器入口"
        },
        {
            "name": "Generator API",
            "file": "src/api/generator_api.py", 
            "function": "GeneratorAPI.__init__",
            "description": "API生成器服务"
        },
        {
            "name": "CLI Entry",
            "file": "cli.py",
            "function": "run_launch",
            "description": "命令行入口"
        },
        {
            "name": "Travel Coordinator",
            "file": "src/workflow/travel_coordinator.py",
            "function": "coordinate_travel_request",
            "description": "旅游请求协调入口"
        },
        {
            "name": "Workflow Graph",
            "file": "src/workflow/coor_task.py",
            "function": "build_graph",
            "description": "工作流图构建入口"
        }
    ]
    
    for entry in entry_points:
        print(f"\n📍 {entry['name']}")
        print(f"   文件: {entry['file']}")
        print(f"   函数: {entry['function']}")
        print(f"   描述: {entry['description']}")
        
        # 检查文件是否存在
        file_path = Path(entry['file'])
        if file_path.exists():
            print("   状态: ✅ 文件存在")
        else:
            print("   状态: ❌ 文件不存在")

if __name__ == "__main__":
    print("🚀 启动旅游协调器调试分析")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 运行调试分析
        asyncio.run(debug_travel_coordinator())
        
        # 分析后台入口点
        asyncio.run(analyze_backend_entry_points())
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断调试")
    except Exception as e:
        print(f"\n❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 调试分析完成")