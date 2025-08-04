import json
import random
from datetime import datetime, timedelta
import re

class AdvancedTravelAgent:
    """
    高级旅游智能体 - 具备个性化行程规划、多模态交互、实时数据处理能力
    """
    
    def __init__(self):
        self.user_preferences = {}
        self.travel_database = {}
        self.current_itinerary = None
        self.weather_conditions = {}
        
        # 初始化旅游数据库
        self._initialize_travel_database()
        
    def _initialize_travel_database(self):
        """初始化旅游数据库"""
        self.travel_database = {
            '北京': {
                'attractions': [
                    {'name': '故宫', 'type': 'culture', 'cost': 60, 'duration': 4},
                    {'name': '长城', 'type': 'culture', 'cost': 45, 'duration': 6},
                    {'name': '天坛', 'type': 'culture', 'cost': 15, 'duration': 3},
                    {'name': '颐和园', 'type': 'culture', 'cost': 30, 'duration': 4},
                    {'name': '国家博物馆', 'type': 'culture', 'cost': 0, 'duration': 3}
                ],
                'hotels': [
                    {'name': '北京王府井希尔顿酒店', 'price_per_night': 800, 'rating': 4.5},
                    {'name': '北京饭店', 'price_per_night': 600, 'rating': 4.2},
                    {'name': '如家快捷酒店', 'price_per_night': 200, 'rating': 3.8}
                ],
                'restaurants': [
                    {'name': '全聚德烤鸭店', 'type': 'food', 'avg_cost': 150},
                    {'name': '东来顺火锅', 'type': 'food', 'avg_cost': 120},
                    {'name': '庆丰包子铺', 'type': 'food', 'avg_cost': 30},
                    {'name': '便宜坊烤鸭店', 'type': 'food', 'avg_cost': 130}
                ],
                'transport': {
                    'from_airport': ['地铁机场快线', '出租车', '网约车'],
                    'local': ['地铁', '公交', '出租车', '共享单车']
                }
            },
            '上海': {
                'attractions': [
                    {'name': '外滩', 'type': 'sightseeing', 'cost': 0, 'duration': 3},
                    {'name': '东方明珠', 'type': 'sightseeing', 'cost': 180, 'duration': 2},
                    {'name': '豫园', 'type': 'culture', 'cost': 40, 'duration': 3},
                    {'name': '上海博物馆', 'type': 'culture', 'cost': 0, 'duration': 3},
                    {'name': '田子坊', 'type': 'sightseeing', 'cost': 0, 'duration': 2}
                ],
                'hotels': [
                    {'name': '上海和平饭店', 'price_per_night': 1200, 'rating': 4.8},
                    {'name': '上海外滩茂悦大酒店', 'price_per_night': 900, 'rating': 4.6},
                    {'name': '汉庭酒店', 'price_per_night': 300, 'rating': 4.0}
                ],
                'restaurants': [
                    {'name': '小南国', 'type': 'food', 'avg_cost': 200},
                    {'name': '南翔小笼包', 'type': 'food', 'avg_cost': 80},
                    {'name': '沈大成', 'type': 'food', 'avg_cost': 50},
                    {'name': '老正兴', 'type': 'food', 'avg_cost': 180}
                ],
                'transport': {
                    'from_airport': ['磁悬浮列车', '地铁', '出租车'],
                    'local': ['地铁', '公交', '出租车']
                }
            }
        }
        print("旅游数据库初始化完成")
    
    def process_user_input(self, input_text):
        """
        处理用户的自然语言输入
        模拟多模态输入处理
        """
        print(f"正在处理用户输入: {input_text}")
        
        # 简单的自然语言处理逻辑
        preferences = {}
        
        # 提取目的地
        if '北京' in input_text:
            preferences['destination'] = '北京'
        elif '上海' in input_text:
            preferences['destination'] = '上海'
        
        # 提取预算信息
        if '预算' in input_text or '钱' in input_text or '元' in input_text:
            budget_match = re.search(r'(\d+)', input_text)
            if budget_match:
                preferences['budget'] = int(budget_match.group(1))
        
        # 提取时间信息
        if '天' in input_text:
            days_match = re.search(r'(\d+)天', input_text)
            if days_match:
                preferences['days'] = int(days_match.group(1))
        
        # 提取兴趣偏好
        interests = []
        if '文化' in input_text or '历史' in input_text:
            interests.append('culture')
        if '美食' in input_text or '吃' in input_text:
            interests.append('food')
        if '风景' in input_text or '景色' in input_text or '观光' in input_text:
            interests.append('sightseeing')
        
        if interests:
            preferences['interests'] = interests
            
        return preferences
    
    def set_user_preferences(self, budget=None, days=None, interests=None, destination=None):
        """设置用户偏好"""
        self.user_preferences = {
            'budget': budget or 2000,
            'days': days or 3,
            'interests': interests or ['culture', 'food'],
            'destination': destination or '北京'
        }
        print(f"用户偏好设置完成: {self.user_preferences}")
    
    def generate_personalized_itinerary(self):
        """生成个性化行程"""
        if not self.user_preferences:
            print("请先设置用户偏好")
            return None
            
        destination = self.user_preferences['destination']
        budget = self.user_preferences['budget']
        days = self.user_preferences['days']
        interests = self.user_preferences['interests']
        
        if destination not in self.travel_database:
            print(f"抱歉，暂不支持{destination}的行程规划")
            return None
            
        data = self.travel_database[destination]
        
        # 智能选择景点
        selected_attractions = []
        for attraction in data['attractions']:
            if attraction['type'] in interests:
                selected_attractions.append(attraction)
        
        # 选择酒店（基于预算）
        suitable_hotels = [h for h in data['hotels'] if h['price_per_night'] * days <= budget * 0.4]
        selected_hotel = max(suitable_hotels, key=lambda x: x['rating']) if suitable_hotels else data['hotels'][-1]
        
        # 选择餐厅
        suitable_restaurants = [r for r in data['restaurants'] if r['type'] in interests or 'food' in interests]
        if not suitable_restaurants:
            suitable_restaurants = data['restaurants']
        
        # 生成每日行程
        daily_itinerary = []
        for day in range(days):
            day_plan = {
                'day': day + 1,
                'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                'attractions': selected_attractions[day:day+1] if day < len(selected_attractions) else [],
                'meals': random.sample(suitable_restaurants, min(2, len(suitable_restaurants))),
                'transport': data['transport']['local'][:2]
            }
            daily_itinerary.append(day_plan)
        
        # 计算总费用
        total_cost = (
            selected_hotel['price_per_night'] * days +
            sum([a['cost'] for a in selected_attractions]) +
            sum([r['avg_cost'] for day in daily_itinerary for r in day['meals']])
        )
        
        self.current_itinerary = {
            'destination': destination,
            'duration': f"{days}天",
            'hotel': selected_hotel,
            'daily_plan': daily_itinerary,
            'estimated_cost': total_cost,
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print("个性化行程生成完成！")
        return self.current_itinerary
    
    def adjust_itinerary_for_weather(self, weather_condition):
        """根据天气情况调整行程"""
        if not self.current_itinerary:
            print("请先生成行程")
            return
            
        print(f"检测到天气变化: {weather_condition}")
        
        if weather_condition == '雨天':
            # 调整为室内活动
            for day in self.current_itinerary['daily_plan']:
                indoor_attractions = [a for a in day['attractions'] if '故宫' in a.get('name', '') or '博物馆' in a.get('name', '')]
                if indoor_attractions:
                    day['weather_adjustment'] = '已调整为室内景点'
                    day['attractions'] = indoor_attractions
                else:
                    day['weather_adjustment'] = '建议室内活动，如参观博物馆'
        
        elif weather_condition == '高温':
            # 调整时间安排
            for day in self.current_itinerary['daily_plan']:
                day['weather_adjustment'] = '建议早上和傍晚出行，中午在酒店休息'
        
        print("行程已根据天气情况进行调整")
    
    def get_real_time_recommendations(self):
        """获取实时推荐"""
        recommendations = {
            'hot_spots': ['网红打卡地推荐', '当地特色体验'],
            'promotions': ['酒店优惠信息', '景点门票折扣'],
            'local_events': ['当地节庆活动', '展览信息'],
            'safety_alerts': ['交通状况', '安全提醒']
        }
        
        print("实时推荐信息获取完成")
        return recommendations
    
    def export_itinerary_to_json(self, filename):
        """导出行程到JSON文件"""
        if not self.current_itinerary:
            print("暂无行程信息可导出")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.current_itinerary, f, ensure_ascii=False, indent=2)
        print(f"行程已导出到 {filename}")
    
    def display_itinerary(self):
        """展示行程"""
        if not self.current_itinerary:
            print("暂无行程信息")
            return
            
        print("\n" + "="*50)
        print(f"🎯 目的地: {self.current_itinerary['destination']}")
        print(f"⏰ 行程时长: {self.current_itinerary['duration']}")
        print(f"🏨 推荐酒店: {self.current_itinerary['hotel']['name']} (¥{self.current_itinerary['hotel']['price_per_night']}/晚)")
        print(f"💰 预估总费用: ¥{self.current_itinerary['estimated_cost']}")
        print(f"📅 生成时间: {self.current_itinerary['generated_time']}")
        
        print("\n📋 详细行程安排:")
        for day_plan in self.current_itinerary['daily_plan']:
            print(f"\n第{day_plan['day']}天 ({day_plan['date']}):")
            print(f"  🎪 景点: {', '.join([a['name'] for a in day_plan['attractions']]) if day_plan['attractions'] else '自由活动'}")
            print(f"  🍽️ 美食: {', '.join([r['name'] for r in day_plan['meals']])}")
            print(f"  🚌 交通: {', '.join(day_plan['transport'])}")
            if 'weather_adjustment' in day_plan:
                print(f"  🌤️ 天气调整: {day_plan['weather_adjustment']}")
        
        print("="*50)

if __name__ == "__main__":
    # 创建智能体实例
    agent = AdvancedTravelAgent()
    
    # 示例用法
    print("=== 旅游智能体演示 ===\n")
    
    # 方式1: 自然语言输入
    user_input = "我想去北京旅游3天，预算3000元，喜欢历史文化和美食"
    parsed_prefs = agent.process_user_input(user_input)
    print(f"解析结果: {parsed_prefs}")
    
    # 设置用户偏好
    agent.set_user_preferences(budget=3000, days=3, interests=['culture', 'food'], destination='北京')
    
    # 生成个性化行程
    agent.generate_personalized_itinerary()
    agent.display_itinerary()
    
    # 模拟天气调整
    agent.adjust_itinerary_for_weather('雨天')
    print("\n🌧️ 天气调整后的行程:")
    agent.display_itinerary()
    
    # 导出行程
    agent.export_itinerary_to_json('travel_itinerary.json')
