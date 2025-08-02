# 旅游规划智能体：MCP组件与动态集成策略

## 1. 核心理念：拥抱MCP生态

为了构建一个强大、可扩展的旅游规划智能体，我们采取**MCP优先**的策略。这意味着，我们将尽可能地利用标准化的[模型上下文协议（MCP）](https://modelcontextprotocol.dev/)组件。这种方法能带来以下好处：
- **标准化**：所有工具都遵循统一的接口，简化了集成和替换。
- **解耦**：工具作为独立的微服务（MCP Server）运行，不影响主应用的稳定性。
- **可扩展性**：可以轻松地添加新的MCP组件来增强智能体的能力，而无需修改核心代码。

传统的Tools（如LangChain Tools）将作为补充，仅用于那些尚未有成熟MCP组件或需要快速实现简单功能的场景。

## 2. 动态工具选择策略

一个全球旅游规划智能体必须能够根据用户的目的地智能地选择合适的工具。例如，在**中国国内**旅游，使用高德地图、携程和大众点评是最佳选择；而在**海外**，则应切换到Google Maps、Booking.com和Yelp。

我们将设计一个`IntelligentTravelToolOrchestrator`（智能旅游工具编排器），它会根据用户输入自动加载和配置相应的MCP服务器。

```python
# 概念代码：智能旅游工具编排器
import re

class IntelligentTravelToolOrchestrator:
    def __init__(self):
        # 定义不同区域的MCP服务器配置
        self.mcp_configs = {
            "china": {
                "amap": {
                    "command": "python", "args": ["tools/amap_mcp_server.py"],
                    "env": {"AMAP_API_KEY": "YOUR_AMAP_KEY"}
                },
                "ctrip": {
                    "url": "https://mcp.ctrip.com/sse", # 假设的URL
                    "env": {"CTRIP_API_KEY": "YOUR_CTRIP_KEY"}
                },
                "dianping": {
                    "command": "python", "args": ["tools/dianping_mcp_server.py"],
                    "env": {"DIANPING_API_KEY": "YOUR_DIANPING_KEY"}
                }
            },
            "international": {
                "google_maps": {
                    "url": "https://mcp.google.com/maps", # 假设的URL
                    "env": {"GOOGLE_API_KEY": "YOUR_GOOGLE_KEY"}
                },
                "flights_mcp": {
                    "command": "npx", "args": ["-y", "flights-mcp-server"],
                    "env": {"DUFFEL_API_KEY": "YOUR_DUFFEL_KEY"}
                },
                "booking": {
                    "url": "https://mcp.booking.com/sse", # 假设的URL
                    "env": {"BOOKING_API_KEY": "YOUR_BOOKING_KEY"}
                }
            }
        }

    def _is_china_travel(self, user_query: str) -> bool:
        """通过关键词或地理位置判断是否为中国国内旅游"""
        china_keywords = ['中国', '北京', '上海', '成都', '国内', '三亚', '西安']
        # 使用正则表达式查找关键词
        if any(re.search(keyword, user_query) for keyword in china_keywords):
            return True
        # 更复杂的实现可以调用地理编码服务
        return False

    async def get_mcp_client_for_query(self, user_query: str):
        """根据用户需求返回一个配置好的MCP客户端"""
        from langchain_mcp_adapters.client import MultiServerMCPClient

        if self._is_china_travel(user_query):
            config = self.mcp_configs["china"]
            print("INFO: Loading MCP configuration for China travel.")
        else:
            config = self.mcp_configs["international"]
            print("INFO: Loading MCP configuration for International travel.")

        # 添加通用的文件系统等工具
        config["filesystem"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "./generated_files"]
        }

        # 动态启动并连接MCP服务器
        client = MultiServerMCPClient(config)
        await client.start_servers() # 确保所有服务都已启动
        return client

# --- 使用示例 ---
# orchestrator = IntelligentTravelToolOrchestrator()
# user_request = "帮我规划一个从上海出发去北京的三日游"
# mcp_client = await orchestrator.get_mcp_client_for_query(user_request)
# available_tools = await mcp_client.get_tools()
# print(f"Available tools: {list(available_tools.keys())}")
# # output: ['maps_direction_driving', 'search_flights', 'search_hotels', ...]
```

---

## 3. 推荐的MCP组件与Tools详解

### 3.1. 中国国内旅游

#### **MCP组件**

| 组件名称 | MCP服务器 (示例) | 描述 | 主要功能/API | 认证方式 |
| --- | --- | --- | --- | --- |
| **高德地图** | `amap` | 国内领先的地图服务 | `maps_direction_driving`, `maps_search_detail`, `maps_around_search` | API Key |
| **携程/飞猪** | `ctrip` / `fliggy` | 航班、火车票、酒店预订 | `search_flights`, `search_trains`, `book_hotel` | API Key / OAuth 2.0 |
| **大众点评** | `dianping` | 餐厅、景点、娱乐活动 | `recommend_restaurants`, `search_activities` | API Key |

#### **详细用例：规划北京三日游**

**用户需求**: "我下周想去北京玩三天，从上海出发，帮我规划一下行程，包括交通、住宿和必去景点。"

**自动化流程**:
1.  `IntelligentTravelToolOrchestrator`识别到“北京”，加载`china`配置。
2.  **交通规划 (携程MCP)**:
    - 调用`search_trains(origin="上海", destination="北京", date="2025-08-10")`查询高铁票。
    - 调用`search_flights(origin="SHA", destination="PEK", date="2025-08-10")`查询航班。
    - 比较时间和价格，向用户推荐最佳方案。
3.  **住宿规划 (携程/美团MCP)**:
    - 调用`search_hotels(city="北京", checkin="2025-08-10", checkout="2025-08-13", price_range=[300, 600])`搜索酒店。
4.  **行程与餐饮 (高德+大众点评MCP)**:
    - **Day 1**:
        - 使用`maps_direction_driving`规划从酒店到天安门/故宫的路线。
        - 使用`recommend_restaurants(location="天安门", cuisine="北京烤鸭")`推荐晚餐。
    - **Day 2**:
        - 使用`maps_direction_driving`规划到长城的路线。
        - 使用`search_activities(location="长城", type="缆车")`查询相关活动。
    - **Day 3**:
        - 使用`maps_around_search(location="酒店", keyword="博物馆")`查找附近的博物馆。
        - 使用`recommend_restaurants(location="王府井", type="小吃")`推荐小吃。

---

### 3.2. 海外（国际）旅游

#### **MCP组件**

| 组件名称 | MCP服务器 (示例) | 描述 | 主要功能/API | 认证方式 |
| --- | --- | --- | --- | --- |
| **Google Maps** | `google_maps` | 全球地图与导航服务 | `get_directions`, `find_place`, `nearby_search` | API Key |
| **flights-mcp** | `flights_mcp` | 基于Duffel/Skyscanner的全球航班搜索 | `search_flight_offers`, `get_seat_map` | API Key (Duffel) |
| **Booking.com** | `booking` | 全球酒店预订平台 | `search_hotels`, `get_hotel_details`, `create_booking` | API Key / OAuth 2.0 |
| **Yelp/TripAdvisor** | `yelp` / `tripadvisor`| 全球餐厅和活动推荐 | `search_businesses`, `get_reviews` | API Key |

#### **详细用例：规划法国巴黎五日游**

**用户需求**: "我想去法国巴黎玩五天，从纽约出发，对艺术和美食感兴趣，帮我做个计划。"

**自动化流程**:
1.  `IntelligentTravelToolOrchestrator`未检测到中国关键词，加载`international`配置。
2.  **交通规划 (flights-mcp)**:
    - 调用`search_flight_offers(origin="JFK", destination="CDG", departure_date="2025-09-20", return_date="2025-09-25")`搜索往返航班。
3.  **住宿规划 (Booking.com MCP)**:
    - 调用`search_hotels(destination="Paris", check_in="2025-09-20", check_out="2025-09-25", interests=["art", "museums"])`搜索靠近艺术区的酒店。
4.  **行程与餐饮 (Google Maps + Yelp MCP)**:
    - **Day 1 (艺术之旅)**:
        - `get_directions`规划从酒店到卢浮宫的路线。
        - `search_businesses(location="Louvre Museum", term="cafe")`推荐午餐咖啡馆。
    - **Day 2 (美食探索)**:
        - `get_directions`规划到Le Marais区的路线。
        - `search_businesses(location="Le Marais, Paris", categories="french,bistros", price="2,3")`推荐中高档法式餐厅。
    - **Day 3 (城市漫步)**:
        - `find_place`定位埃菲尔铁塔。
        - `nearby_search(location="Eiffel Tower", type="tourist_attraction")`探索周边景点。

### 3.3. 通用补充Tools (非MCP)

在特定情况下，我们可以使用一些轻量级的传统工具作为补充。

- **Tavily Search Tool**:
  - **描述**: 一个强大的搜索引擎，专为LLM优化，能提供精准、无广告的搜索结果。
  - **用例**: 当需要查询一些实时、长尾信息（如“巴黎九月有什么特别的节日活动吗？”或“去长城需要注意什么？”）时，Tavily可以提供比专业API更灵活的答案。
- **OpenWeatherMap Tool**:
  - **描述**: 提供全球城市的天气预报。
  - **用例**: 在规划每日行程前，查询目的地的天气情况，以便智能体建议合适的着装和活动安排。
- **Currency Converter Tool**:
  - **描述**: 提供实时的货币汇率转换。
  - **用例**: 在进行海外旅游预算规划时，将花费从当地货币转换为用户的本国货币。
- **Python REPL Tool**:
  - **描述**: 执行Python代码，用于动态计算。
  - **用例**: 进行复杂的预算汇总、旅行时间计算或根据多个API返回的数据进行自定义排序。 