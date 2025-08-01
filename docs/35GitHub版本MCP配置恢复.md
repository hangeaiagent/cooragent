# GitHub版本MCP配置恢复

## 恢复概述

根据您提供的GitHub版本MCP配置，已成功恢复了原始的MCP服务器配置，替换了之前添加的旅游相关MCP服务器。

## 配置对比

### 1. 恢复的GitHub版本配置

```json
{
  "mcpServers": {
    "AMAP": {
      "url": "https://mcp.amap.com/sse",
      "env": {
        "AMAP_MAPS_API_KEY": "your_amap_maps_api_key"
      }
    },
    "excel": {
      "command": "npx",
      "args": ["--yes", "@negokaz/excel-mcp-server"],
      "env": {
        "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/a1/work/cooragent/generated_projects"
      ]
    },
    "word": {
      "command": "python",
      "args": ["/Users/a1/work/cooragent/src/tools/MCP-Doc/server.py"]
    },
    "image-downloader": {
      "command": "node",
      "args": ["/Users/a1/work/cooragent/src/tools/mcp-image-downloader/build/index.js"]
    },
    "variflight-mcp": {
      "type": "sse",
      "url": "your_modelscope_variflight_mcp_url"
    }
  }
}
```

### 2. 主要变化

#### 2.1 移除的服务器
- ❌ `flightradar` - 航班雷达服务器
- ❌ `maps-service` - 地图服务服务器
- ❌ `weather-service` - 天气服务服务器
- ❌ `hotel-booking` - 酒店预订服务器
- ❌ `currency-converter` - 货币转换服务器
- ❌ `travel-assistant` - 旅游助手服务器

#### 2.2 恢复的服务器
- ✅ `AMAP` - 高德地图SSE服务器
- ✅ `excel` - Excel处理服务器
- ✅ `word` - Word文档处理服务器
- ✅ `variflight-mcp` - 航班信息SSE服务器

### 3. 连接方式变化

#### 3.1 SSE连接（Server-Sent Events）
- **AMAP**: 使用SSE连接到 `https://mcp.amap.com/sse`
- **variflight-mcp**: 使用SSE连接到 `your_modelscope_variflight_mcp_url`

#### 3.2 stdio连接（标准输入输出）
- **excel**: 使用 `@negokaz/excel-mcp-server`
- **filesystem**: 使用 `@modelcontextprotocol/server-filesystem`
- **word**: 使用本地Python服务器
- **image-downloader**: 使用本地Node.js服务器

## 代码生成器更新

### 1. MCP配置生成方法更新

**文件**: `src/generator/cooragent_generator.py`

**更新内容**:
```python
# GitHub版本的MCP服务器配置
github_mcp_servers = {
    "AMAP": {
        "url": "https://mcp.amap.com/sse",
        "env": {
            "AMAP_MAPS_API_KEY": "your_amap_maps_api_key"
        }
    },
    "excel": {
        "command": "npx",
        "args": ["--yes", "@negokaz/excel-mcp-server"],
        "env": {
            "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000"
        }
    },
    "word": {
        "command": "python",
        "args": [str(project_path / "src" / "tools" / "MCP-Doc" / "server.py")]
    },
    "image-downloader": {
        "command": "node",
        "args": [str(project_path / "src" / "tools" / "mcp-image-downloader" / "build" / "index.js")]
    },
    "variflight-mcp": {
        "type": "sse",
        "url": "your_modelscope_variflight_mcp_url"
    }
}

# 工具到MCP服务器的映射（GitHub版本）
tool_to_mcp_mapping = {
    # 地图相关工具
    "maps_direction_driving": "AMAP",
    "maps_direction_transit": "AMAP",
    "maps_direction_walking": "AMAP",
    "maps_distance": "AMAP",
    "maps_geo": "AMAP",
    "maps_regeocode": "AMAP",
    "maps_ip_location": "AMAP",
    "maps_around_search": "AMAP",
    "maps_search_detail": "AMAP",
    "maps_text_search": "AMAP",
    "amap_tool": "AMAP",
    
    # Excel工具
    "excel_tool": "excel",
    
    # 文档工具
    "mcp_doc": "word",
    "document_processor": "word",
    
    # 图片下载工具
    "mcp_image_downloader": "image-downloader",
    "image_downloader": "image-downloader",
    
    # 航班工具
    "searchFlightItineraries": "variflight-mcp",
    "flight_search": "variflight-mcp",
    "search_flights": "variflight-mcp"
}
```

### 2. 工具依赖映射更新

**更新内容**:
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
    
    # GitHub版本的MCP工具
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
    "amap_tool": ["decorators.py"],
    "mcp_doc": ["MCP-Doc/", "decorators.py"],
    "document_processor": ["MCP-Doc/", "decorators.py"],
    "mcp_image_downloader": ["mcp-image-downloader/", "decorators.py"],
    "image_downloader": ["mcp-image-downloader/", "decorators.py"],
    "decorators": ["decorators.py"]
}
```

## 环境变量配置

### 1. 必需的API密钥

```bash
# 高德地图API密钥
AMAP_MAPS_API_KEY=your_amap_maps_api_key

# 航班信息API URL
VARIFLIGHT_MCP_URL=your_modelscope_variflight_mcp_url
```

### 2. Excel服务器配置

```bash
# Excel分页单元格限制
EXCEL_MCP_PAGING_CELLS_LIMIT=4000
```

## 服务器类型说明

### 1. SSE服务器（Server-Sent Events）
- **AMAP**: 连接到高德地图的SSE服务
- **variflight-mcp**: 连接到ModelScope的航班信息SSE服务

### 2. stdio服务器（标准输入输出）
- **excel**: 使用 `@negokaz/excel-mcp-server` 包
- **filesystem**: 使用 `@modelcontextprotocol/server-filesystem` 包
- **word**: 使用本地Python MCP-Doc服务器
- **image-downloader**: 使用本地Node.js图片下载服务器

## 工具映射关系

### 1. 地图工具 → AMAP
- `maps_direction_driving` → AMAP
- `maps_direction_transit` → AMAP
- `maps_direction_walking` → AMAP
- `maps_distance` → AMAP
- `maps_geo` → AMAP
- `maps_regeocode` → AMAP
- `maps_ip_location` → AMAP
- `maps_around_search` → AMAP
- `maps_search_detail` → AMAP
- `maps_text_search` → AMAP
- `amap_tool` → AMAP

### 2. Excel工具 → excel
- `excel_tool` → excel

### 3. 文档工具 → word
- `mcp_doc` → word
- `document_processor` → word

### 4. 图片工具 → image-downloader
- `mcp_image_downloader` → image-downloader
- `image_downloader` → image-downloader

### 5. 航班工具 → variflight-mcp
- `searchFlightItineraries` → variflight-mcp
- `flight_search` → variflight-mcp
- `search_flights` → variflight-mcp

## 恢复效果

### 1. 配置一致性
- ✅ 恢复了GitHub版本的MCP服务器配置
- ✅ 保持了与原始代码的兼容性
- ✅ 使用了正确的SSE和stdio连接方式

### 2. 功能支持
- ✅ 支持高德地图服务（SSE）
- ✅ 支持Excel处理（stdio）
- ✅ 支持Word文档处理（stdio）
- ✅ 支持图片下载（stdio）
- ✅ 支持航班信息查询（SSE）

### 3. 环境变量
- ✅ 正确配置了AMAP API密钥
- ✅ 正确配置了Excel服务器参数
- ✅ 预留了航班信息API URL配置

## 注意事项

### 1. SSE连接要求
- AMAP和variflight-mcp使用SSE连接，需要确保网络连接正常
- 需要配置正确的API密钥和URL

### 2. 本地服务器要求
- word和image-downloader需要本地服务器文件存在
- 需要安装相应的npm包和Python依赖

### 3. 环境变量配置
- 需要在 `.env` 文件中配置正确的API密钥
- 需要设置正确的服务器URL

## 总结

已成功恢复到GitHub版本的MCP配置，包括：

1. **恢复了原始服务器配置**：AMAP、excel、word、image-downloader、variflight-mcp
2. **更新了连接方式**：正确使用SSE和stdio连接
3. **修正了工具映射**：确保工具正确映射到对应的MCP服务器
4. **保持了兼容性**：与现有代码和配置保持兼容

现在系统使用的是GitHub版本的MCP配置，应该能够正常支持所有原有的功能。 