# 旅游智能体 (Travel Agent) 使用说明

## 概述
这是一个基于AI的智能旅游规划助手，能够根据用户需求生成个性化的旅行行程，支持自然语言交互和智能推荐。

## 主要功能

### 1. 个性化行程规划
- 根据用户预算、时间、兴趣自动生成最优行程
- 智能匹配景点、酒店、餐厅
- 支持多种旅游偏好（文化、美食、观光等）

### 2. 多模态交互
- 支持自然语言输入处理
- 自动解析用户需求和偏好
- 智能对话式交互体验

### 3. 动态行程调整
- 根据天气情况实时调整行程
- 支持突发情况的应急处理
- 灵活修改旅行计划

### 4. 实时推荐系统
- 提供热门景点推荐
- 实时优惠信息推送
- 本地活动和安全提醒

## 使用方法

### 基础使用
```python
from travel_agent import AdvancedTravelAgent

# 创建智能体实例
agent = AdvancedTravelAgent()

# 方式1: 自然语言输入
user_input = "我想去北京旅游3天，预算3000元，喜欢历史文化和美食"
preferences = agent.process_user_input(user_input)

# 方式2: 直接设置偏好
agent.set_user_preferences(
    budget=3000, 
    days=3, 
    interests=['culture', 'food'], 
    destination='北京'
)

# 生成行程
agent.generate_personalized_itinerary()

# 展示行程
agent.display_itinerary()

# 导出行程
agent.export_itinerary_to_json('my_trip.json')
```

### 高级功能
```python
# 天气调整
agent.adjust_itinerary_for_weather('雨天')

# 获取实时推荐
recommendations = agent.get_real_time_recommendations()
```

## 支持的目的地
- 北京：故宫、长城、天坛、颐和园、国家博物馆
- 上海：外滩、东方明珠、豫园、上海博物馆、田子坊

## 配置参数

### 用户偏好设置
- `budget`: 预算金额（元）
- `days`: 旅行天数
- `interests`: 兴趣列表 ['culture', 'food', 'sightseeing']
- `destination`: 目的地城市

### 兴趣类型
- `culture`: 文化历史类景点
- `food`: 美食餐厅
- `sightseeing`: 观光游览

## 输出格式

### 行程信息
```json
{
  "destination": "北京",
  "duration": "3天",
  "hotel": {
    "name": "如家快捷酒店",
    "price_per_night": 200,
    "rating": 3.8
  },
  "daily_plan": [
    {
      "day": 1,
      "date": "2024-01-15",
      "attractions": [{"name": "故宫", "type": "culture", "cost": 60}],
      "meals": [{"name": "全聚德烤鸭店", "avg_cost": 150}],
      "transport": ["地铁", "公交"]
    }
  ],
  "estimated_cost": 1830,
  "generated_time": "2024-01-15 10:30:00"
}
```

## 扩展开发

### 添加新城市
在 `_initialize_travel_database()` 方法中添加新的城市数据：

```python
'新城市': {
    'attractions': [...],
    'hotels': [...],
    'restaurants': [...],
    'transport': {...}
}
```

### 自定义推荐算法
重写 `generate_personalized_itinerary()` 方法以实现更复杂的推荐逻辑。

### 接入外部API
可以扩展 `get_real_time_recommendations()` 方法接入真实的旅游数据API。

## 技术特点
- 面向对象设计，易于扩展
- 支持JSON格式数据导入导出
- 模块化架构，便于维护
- 自然语言处理能力
- 智能决策算法

## 版本信息
- 版本: 1.0.0
- 开发语言: Python 3.7+
- 依赖库: json, random, datetime, re

## 注意事项
- 当前版本为演示版本，数据为模拟数据
- 实际部署时需要接入真实的旅游数据源
- 建议根据具体需求调整推荐算法
- 支持的城市有限，可根据需要扩展

## 联系方式
如有问题或建议，请联系开发团队。
