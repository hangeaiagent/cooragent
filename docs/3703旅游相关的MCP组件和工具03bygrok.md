# 旅游相关的MCP组件和工具 - 基于MCP生态的旅游规划方案

## 概述
本文档详细列出用于旅游规划、建议和预定的MCP组件和工具，优先采用MCP方案，仅在成熟场景下补充传统Tools。方案强调克服MCP部署困难，更多利用MCP的标准化优势。内容分为国内（中国）和海外（国际）两部分。

每个组件/工具包括：
- **描述**：功能概述
- **API参数**：典型调用参数
- **认证方式**：访问认证方法
- **典型用例**：旅游场景应用
- **代码示例/集成方案**：Python自动化集成代码

## 国内（中国）MCP组件和工具

### 1. 高德地图MCP服务器 (地图导航)
- **描述**：提供中国实时地图、路线规划、POI搜索，支持驾车/步行/公共交通导航。
- **API参数**：
  - origin: 起点坐标 (e.g., "116.407396,39.904199")
  - destination: 终点坐标 (e.g., "108.948024,34.263161")
  - mode: 模式 ("driving", "walking", "transit")
  - key: API密钥
- **认证方式**：API Key (在高德开发者平台注册获取)
- **典型用例**：规划从北京到故宫的步行路线，包含实时交通和景点推荐。
- **代码示例/集成方案**：
  ```python
  from langchain_mcp_adapters.client import MultiServerMCPClient

  client = MultiServerMCPClient({
      "amap": {
          "url": "https://mcp.amap.com/sse",
          "env": {"AMAP_MAPS_API_KEY": "your_key"}
      }
  })
  tools = await client.get_tools()
  result = await tools['maps_direction_driving']({
      "origin": "116.407396,39.904199",
      "destination": "108.948024,34.263161"
  })
  ```

### 2. 携程/飞猪MCP服务器 (航班/酒店预订)
- **描述**：集成携程/飞猪API，支持国内航班搜索、酒店预订和价格比较。
- **API参数**：
  - type: "one_way" / "round_trip"
  - origin: 起点机场代码 (e.g., "PEK")
  - destination: 终点机场代码 (e.g., "SHA")
  - departure_date: "YYYY-MM-DD"
  - adults: 成人人数 (e.g., 2)
- **认证方式**：OAuth 2.0 (用户登录携程账号授权)
- **典型用例**：搜索北京到上海的低价航班，并预订经济舱酒店。
- **代码示例/集成方案**：
  ```python
  # 假设携程MCP服务器
  client = MultiServerMCPClient({"ctrip": {"url": "https://mcp.ctrip.com/sse"}})
  result = await tools['search_flights']({
      "type": "one_way",
      "origin": "PEK",
      "destination": "SHA",
      "departure_date": "2025-08-15"
  })
  ```

### 3. 12306 MCP集成 (火车票预订)
- **描述**：官方高铁/火车票查询和预订，支持实时余票和时刻表。
- **API参数**：
  - from_station: 出发站 (e.g., "北京")
  - to_station: 到达站 (e.g., "上海")
  - date: "YYYY-MM-DD"
- **认证方式**：用户登录 (12306账号OAuth)
- **典型用例**：查询北京到西安的高铁票，并规划换乘。
- **代码示例/集成方案**：
  ```python
  # 假设12306 MCP
  result = await tools['search_trains']({
      "from_station": "北京",
      "to_station": "西安",
      "date": "2025-08-10"
  })
  ```

### 4. 美团酒店MCP (住宿预订)
- **描述**：本地化酒店搜索，支持价格过滤和用户评价。
- **API参数**：
  - city: "北京"
  - checkin: "YYYY-MM-DD"
  - checkout: "YYYY-MM-DD"
  - price_range: [200, 500]
- **认证方式**：API Key或用户登录
- **典型用例**：在北京寻找200-500元/晚的酒店，包含早餐。
- **代码示例/集成方案**：
  ```python
  result = await tools['search_hotels']({
      "city": "北京",
      "checkin": "2025-08-15",
      "checkout": "2025-08-18"
  })
  ```

### 5. 大众点评MCP (餐饮推荐)
- **描述**：餐厅搜索、评价和本地美食推荐。
- **API参数**：
  - location: "北京"
  - cuisine: "川菜"
  - price_level: "medium"
- **认证方式**：API Key
- **典型用例**：推荐北京的川菜餐厅，包含用户评分。
- **代码示例/集成方案**：
  ```python
  result = await tools['recommend_restaurants']({
      "location": "北京",
      "cuisine": "川菜"
  })
  ```

### 补充成熟Tools (非MCP)
- **Tavily Search**：通用搜索工具，用于补充信息。
  - 用例：查询天气或景点详情。
- **Python REPL**：计算工具，用于预算计算。

## 海外（国际）MCP组件和工具

### 1. Google Maps MCP (地图导航)
- **描述**：全球地图服务，支持路线规划和地点搜索。
- **API参数**：
  - origin: "New York"
  - destination: "London"
  - mode: "driving" / "flight"
- **认证方式**：Google API Key
- **典型用例**：规划纽约到波士顿的自驾路线。
- **代码示例/集成方案**：
  ```python
  result = await tools['get_directions']({
      "origin": "New York",
      "destination": "Boston",
      "mode": "driving"
  })
  ```

### 2. flights-mcp (Duffel API) (航班搜索)
- **描述**：全球450+航司的航班搜索和价格比较。
- **API参数**：
  - origin: "JFK"
  - destination: "LHR"
  - departure_date: "2025-09-01"
  - cabin_class: "economy"
- **认证方式**：Duffel API Key
- **典型用例**：搜索纽约到伦敦的经济舱航班。
- **代码示例/集成方案**：
  ```python
  result = await tools['search_flights']({
      "origin": "JFK",
      "destination": "LHR",
      "departure_date": "2025-09-01"
  })
  ```

### 3. Booking.com MCP (酒店预订)
- **描述**：全球酒店搜索，支持免费取消和实时价格。
- **API参数**：
  - destination: "Paris"
  - check_in: "2025-09-10"
  - check_out: "2025-09-15"
  - adults: 2
- **认证方式**：OAuth 2.0
- **典型用例**：在巴黎预订5晚中档酒店。
- **代码示例/集成方案**：
  ```python
  result = await tools['search_hotels']({
      "destination": "Paris",
      "check_in": "2025-09-10",
      "check_out": "2025-09-15"
  })
  ```

### 4. Yelp MCP服务器 (餐饮推荐)
- **描述**：全球餐厅评价和推荐，支持过滤和地图集成。
- **API参数**：
  - location: "San Francisco"
  - term: "Italian food"
  - price: 2  # 1-4 level
- **认证方式**：Yelp API Key
- **典型用例**：推荐旧金山的意大利餐厅。
- **代码示例/集成方案**：
  ```python
  result = await tools['search_restaurants']({
      "location": "San Francisco",
      "term": "Italian"
  })
  ```

### 5. Turkish Airlines MCP (特定航空服务)
- **描述**：航班状态、预订和会员服务。
- **API参数**：
  - flight_number: "TK123"
  - date: "2025-09-05"
- **认证方式**：Miles&Smiles账号登录 (OAuth)
- **典型用例**：查询伊斯坦布尔到纽约的航班状态。
- **代码示例/集成方案**：
  ```python
  result = await tools['get_flight_status']({
      "flight_number": "TK123",
      "date": "2025-09-05"
  })
  ```

### 补充成熟Tools (非MCP)
- **OpenWeatherMap**：全球天气查询工具。
  - 用例：获取目的地天气预报。
- **Exchangeratesapi**：货币转换工具。
  - 用例：预算计算和本地货币转换。

## 集成方案总结
### 自动化旅游规划流程
```python
async def automated_travel_plan(user_input):
    selector = IntelligentTravelToolSelector()
    tools = await selector.select_tools(user_input)
    
    # 调用工具生成行程
    itinerary = await generate_itinerary(tools, user_input)
    return itinerary
```

此方案实现智能工具分配，确保国内使用本地化MCP，海外使用全球服务。完整代码可扩展为LangGraph工作流。 