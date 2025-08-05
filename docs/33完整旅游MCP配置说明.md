# 完整旅游MCP配置说明

## 概述

本文档详细说明了Cooragent系统中完整的旅游相关MCP（Model Context Protocol）配置，包括所有可用的MCP服务器、工具映射和配置方法。

## 1. 完整的MCP配置文件

### 1.1 主配置文件 (config/mcp.json)

```json
{
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": [
          "-y",
          "@modelcontextprotocol/server-filesystem",
          "/Users/a1/work/cooragent/generated_projects"
        ]
      },
      "flightradar": {
        "command": "npx",
        "args": [
          "-y",
          "flightradar-mcp-server"
        ]
      },
      "mcp-doc": {
        "command": "python",
        "args": ["/Users/a1/work/cooragent/src/tools/MCP-Doc/server.py"],
        "env": {}
      },
      "image-downloader": {
        "command": "node",
        "args": ["/Users/a1/work/cooragent/src/tools/mcp-image-downloader/build/index.js"],
        "env": {}
      },
      "maps-service": {
        "command": "python",
        "args": ["/Users/a1/work/cooragent/src/tools/maps_server.py"],
        "env": {
          "AMAP_API_KEY": "your_amap_api_key"
        }
      },
      "weather-service": {
        "command": "python",
        "args": ["/Users/a1/work/cooragent/src/tools/weather_server.py"],
        "env": {
          "WEATHER_API_KEY": "your_weather_api_key"
        }
      },
      "hotel-booking": {
        "command": "node",
        "args": ["/Users/a1/work/cooragent/src/tools/hotel_server.js"],
        "env": {
          "HOTEL_API_KEY": "your_hotel_api_key"
        }
      },
      "currency-converter": {
        "command": "python",
        "args": ["/Users/a1/work/cooragent/src/tools/currency_server.py"],
        "env": {
          "CURRENCY_API_KEY": "your_currency_api_key"
        }
      },
      "travel-assistant": {
        "command": "python",
        "args": ["/Users/a1/work/cooragent/src/tools/travel_assistant_server.py"],
        "env": {
          "TRAVEL_API_KEY": "your_travel_api_key"
        }
      }
    }
}
```

## 2. 旅游相关MCP服务器

### 2.1 航班信息服务器

#### flightradar
- **功能**: 航班搜索、航班跟踪、航班状态查询
- **包名**: `flightradar-mcp-server`
- **安装**: `npm install -g flightradar-mcp-server`
- **工具映射**: 
  - `searchFlightItineraries`
  - `flight_search`
  - `search_flights`

### 2.2 地图服务服务器

#### maps-service
- **功能**: 地图导航、地点搜索、路线规划
- **API**: 高德地图API
- **环境变量**: `AMAP_API_KEY`
- **工具映射**:
  - `maps_direction_driving` - 驾车导航
  - `maps_direction_transit` - 公交导航
  - `maps_direction_walking` - 步行导航
  - `maps_distance` - 距离计算
  - `maps_geo` - 地理编码
  - `maps_regeocode` - 逆地理编码
  - `maps_ip_location` - IP定位
  - `maps_around_search` - 周边搜索
  - `maps_search_detail` - 地点详情
  - `maps_text_search` - 文本搜索

### 2.3 天气服务服务器

#### weather-service
- **功能**: 旅游目的地天气查询、天气预报
- **环境变量**: `WEATHER_API_KEY`
- **工具映射**:
  - `weather_forecast_travel` - 旅游天气

### 2.4 酒店预订服务器

#### hotel-booking
- **功能**: 酒店搜索、预订、价格比较
- **环境变量**: `HOTEL_API_KEY`
- **工具映射**:
  - `hotel_search_and_booking` - 酒店搜索和预订

### 2.5 货币转换服务器

#### currency-converter
- **功能**: 汇率查询、货币转换
- **环境变量**: `CURRENCY_API_KEY`
- **工具映射**:
  - `currency_converter` - 货币转换

### 2.6 旅游助手服务器

#### travel-assistant
- **功能**: 综合旅游信息、推荐、规划
- **环境变量**: `TRAVEL_API_KEY`
- **工具映射**:
  - `travel_assistant` - 旅游助手

## 3. 代码生成器中的工具映射

### 3.1 DynamicComponentAnalyzer.tool_dependencies

```python
self.tool_dependencies = {
    # 基础工具
    "tavily_tool": ["search.py", "decorators.py"],
    "python_repl_tool": ["python_repl.py", "decorators.py"],
    "bash_tool": ["bash_tool.py", "decorators.py"],
    "crawl_tool": ["crawl.py", "crawler/", "decorators.py"],
    "browser_tool": ["browser.py", "browser_decorators.py", "decorators.py"],
    "excel_tool": ["excel/", "decorators.py"],
    "gmail_tool": ["gmail.py", "decorators.py"],
    "slack_tool": ["slack.py", "decorators.py"],
    "video_tool": ["video.py", "decorators.py"],
    "file_management_tool": ["file_management.py", "decorators.py"],
    "avatar_tool": ["avatar_tool.py", "decorators.py"],
    "office365_tool": ["office365.py", "decorators.py"],
    "web_preview_tool": ["web_preview_tool.py", "web_preview/", "decorators.py"],
    "websocket_tool": ["websocket_manager.py", "decorators.py"],
    
    # 旅游相关MCP工具
    "searchFlightItineraries": ["decorators.py"],
    "flight_search": ["decorators.py"],
    "search_flights": ["decorators.py"],
    "maps_direction_driving": ["decorators.py"],
    "maps_direction_transit": ["decorators.py"],
    "maps_direction_walking": ["decorators.py"],
    "maps_distance": ["decorators.py"],
    "maps_geo": ["decorators.py"],
    "maps_regeocode": ["decorators.py"],
    "maps_ip_location": ["decorators.py"],
    "maps_around_search": ["decorators.py"],
    "maps_search_detail": ["decorators.py"],
    "maps_text_search": ["decorators.py"],
    "weather_forecast_travel": ["decorators.py"],
    "hotel_search_and_booking": ["decorators.py"],
    "currency_converter": ["decorators.py"],
    "travel_assistant": ["decorators.py"],
    "decorators": ["decorators.py"]
}
```

### 3.2 MCPEcosystemIntegrator._generate_mcp_config

```python
# 旅游相关MCP服务器配置
travel_mcp_servers = {
    "flightradar": {
        "command": "npx",
        "args": ["-y", "flightradar-mcp-server"],
        "env": {}
    },
    "maps-service": {
        "command": "python",
        "args": [str(project_path / "src" / "tools" / "maps_server.py")],
        "env": {"AMAP_API_KEY": "your_amap_api_key"}
    },
    "weather-service": {
        "command": "python",
        "args": [str(project_path / "src" / "tools" / "weather_server.py")],
        "env": {"WEATHER_API_KEY": "your_weather_api_key"}
    },
    "hotel-booking": {
        "command": "node",
        "args": [str(project_path / "src" / "tools" / "hotel_server.js")],
        "env": {"HOTEL_API_KEY": "your_hotel_api_key"}
    },
    "currency-converter": {
        "command": "python",
        "args": [str(project_path / "src" / "tools" / "currency_server.py")],
        "env": {"CURRENCY_API_KEY": "your_currency_api_key"}
    },
    "travel-assistant": {
        "command": "python",
        "args": [str(project_path / "src" / "tools" / "travel_assistant_server.py")],
        "env": {"TRAVEL_API_KEY": "your_travel_api_key"}
    }
}

# 工具到MCP服务器的映射
tool_to_mcp_mapping = {
    "searchFlightItineraries": "flightradar",
    "flight_search": "flightradar",
    "search_flights": "flightradar",
    "maps_direction_driving": "maps-service",
    "maps_direction_transit": "maps-service",
    "maps_direction_walking": "maps-service",
    "maps_distance": "maps-service",
    "maps_geo": "maps-service",
    "maps_regeocode": "maps-service",
    "maps_ip_location": "maps-service",
    "maps_around_search": "maps-service",
    "maps_search_detail": "maps-service",
    "maps_text_search": "maps-service",
    "weather_forecast_travel": "weather-service",
    "hotel_search_and_booking": "hotel-booking",
    "currency_converter": "currency-converter",
    "travel_assistant": "travel-assistant"
}
```

## 4. 安装和配置步骤

### 4.1 安装MCP服务器包

```bash
# 安装航班雷达MCP服务器
npm install -g flightradar-mcp-server

# 安装文件系统MCP服务器
npm install -g @modelcontextprotocol/server-filesystem
```

### 4.2 配置环境变量

在 `.env` 文件中添加必要的API密钥：

```bash
# 高德地图API密钥
AMAP_API_KEY=your_amap_api_key

# 天气API密钥
WEATHER_API_KEY=your_weather_api_key

# 酒店API密钥
HOTEL_API_KEY=your_hotel_api_key

# 货币API密钥
CURRENCY_API_KEY=your_currency_api_key

# 旅游API密钥
TRAVEL_API_KEY=your_travel_api_key
```

### 4.3 创建MCP服务器文件

需要创建以下MCP服务器文件：

1. `src/tools/maps_server.py` - 地图服务
2. `src/tools/weather_server.py` - 天气服务
3. `src/tools/hotel_server.js` - 酒店服务
4. `src/tools/currency_server.py` - 货币服务
5. `src/tools/travel_assistant_server.py` - 旅游助手

## 5. 使用示例

### 5.1 旅游智能体配置

```python
# 旅游智能体使用的工具
travel_tools = [
    "searchFlightItineraries",    # 航班搜索
    "maps_direction_transit",     # 公交导航
    "weather_forecast_travel",    # 天气查询
    "hotel_search_and_booking",   # 酒店预订
    "currency_converter",         # 货币转换
    "travel_assistant"            # 旅游助手
]
```

### 5.2 生成的MCP配置

当智能体使用上述工具时，代码生成器会自动生成包含相应MCP服务器的配置文件：

```json
{
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./store", "./static"]
      },
      "flightradar": {
        "command": "npx",
        "args": ["-y", "flightradar-mcp-server"]
      },
      "maps-service": {
        "command": "python",
        "args": ["./src/tools/maps_server.py"],
        "env": {"AMAP_API_KEY": "your_amap_api_key"}
      },
      "weather-service": {
        "command": "python",
        "args": ["./src/tools/weather_server.py"],
        "env": {"WEATHER_API_KEY": "your_weather_api_key"}
      },
      "hotel-booking": {
        "command": "node",
        "args": ["./src/tools/hotel_server.js"],
        "env": {"HOTEL_API_KEY": "your_hotel_api_key"}
      },
      "currency-converter": {
        "command": "python",
        "args": ["./src/tools/currency_server.py"],
        "env": {"CURRENCY_API_KEY": "your_currency_api_key"}
      },
      "travel-assistant": {
        "command": "python",
        "args": ["./src/tools/travel_assistant_server.py"],
        "env": {"TRAVEL_API_KEY": "your_travel_api_key"}
      }
    }
}
```

## 6. 故障排除

### 6.1 常见问题

1. **MCP服务器启动失败**
   - 检查包是否正确安装
   - 验证环境变量配置
   - 确认服务器文件路径正确

2. **工具映射失败**
   - 检查 `tool_dependencies` 中是否包含相应工具
   - 验证 `tool_to_mcp_mapping` 映射关系

3. **API密钥错误**
   - 确认API密钥有效
   - 检查环境变量是否正确设置

### 6.2 调试方法

```bash
# 检查MCP服务器状态
ps aux | grep mcp

# 查看MCP服务器日志
tail -f /var/log/mcp-server.log

# 测试MCP服务器连接
curl -X POST http://localhost:8080/mcp/health
```

## 7. 扩展和自定义

### 7.1 添加新的MCP服务器

1. 在 `travel_mcp_servers` 中添加新服务器配置
2. 在 `tool_to_mcp_mapping` 中添加工具映射
3. 在 `tool_dependencies` 中添加工具依赖
4. 创建相应的MCP服务器文件

### 7.2 自定义工具映射

可以根据需要修改 `tool_to_mcp_mapping` 来调整工具与MCP服务器的映射关系。

## 8. 总结

完整的旅游MCP配置包括：

- ✅ 7个旅游相关MCP服务器
- ✅ 完整的工具到服务器映射
- ✅ 自动化的配置生成
- ✅ 环境变量管理
- ✅ 错误处理和调试支持

这个配置为旅游智能体提供了全面的功能支持，包括航班查询、地图导航、天气查询、酒店预订、货币转换等核心旅游服务。 