#!/usr/bin/env python3
"""
测试简单查询功能
"""

import requests
import time
import json

def test_simple_query():
    """测试简单查询功能"""
    base_url = "http://localhost:8000"
    
    # 测试简单查询
    simple_query = {
        "content": "北京有什么好玩的？",
        "user_id": "test_user_simple"
    }
    
    print("🚀 开始测试简单查询功能...")
    print(f"📝 查询内容: {simple_query['content']}")
    
    try:
        # 1. 发起查询请求
        print("\n1️⃣ 发起简单查询请求...")
        response = requests.post(
            f"{base_url}/api/generate",
            json=simple_query,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ 请求成功，任务ID: {task_id}")
            print(f"📊 初始状态: {result['status']}")
            print(f"💬 消息: {result['message']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
        
        # 2. 轮询任务状态
        print("\n2️⃣ 轮询任务状态...")
        max_attempts = 30  # 最多等待60秒
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(f"{base_url}/api/generate/{task_id}/status")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"📊 进度: {status_data['progress']}% - {status_data['message']}")
                
                if status_data['status'] == 'completed':
                    print("✅ 任务完成！")
                    
                    # 3. 检查是否有旅游规划结果
                    if status_data.get('travel_result'):
                        print("🎉 成功获取简单查询结果！")
                        print(f"📄 结果长度: {len(status_data['travel_result'])} 字符")
                        print(f"📄 结果预览: {status_data['travel_result'][:300]}...")
                        
                        # 保存结果到文件
                        with open(f"simple_query_result_{task_id[:8]}.md", "w", encoding="utf-8") as f:
                            f.write(status_data['travel_result'])
                        print(f"💾 结果已保存到: simple_query_result_{task_id[:8]}.md")
                        
                        return True
                    else:
                        print("⚠️ 没有找到查询结果")
                        print(f"📊 状态数据: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
                        return False
                        
                elif status_data['status'] == 'failed':
                    print(f"❌ 任务失败: {status_data.get('error_details', '未知错误')}")
                    return False
            
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                return False
            
            time.sleep(2)  # 等待2秒
            attempt += 1
        
        print("⏰ 超时，任务未在预期时间内完成")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

def test_health_check():
    """测试健康检查"""
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 服务健康状态: {health_data['status']}")
            print(f"🕐 时间戳: {health_data['timestamp']}")
            print(f"📊 活跃任务: {health_data['active_tasks']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
        return False

def main():
    """主函数"""
    print("🧪 开始简单查询测试...")
    print("=" * 50)
    
    # 1. 健康检查
    print("🔍 执行健康检查...")
    if not test_health_check():
        print("❌ 服务不可用，请确保服务器已启动")
        return
    
    print("\n" + "=" * 50)
    
    # 2. 测试简单查询
    success = test_simple_query()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试成功！简单查询功能正常工作")
    else:
        print("❌ 测试失败！请检查API实现")

if __name__ == "__main__":
    main() 