# MCP航班服务器配置修复

## 问题描述

在启动服务时遇到以下错误：
```
npm error code E404
npm error 404 Not Found - GET https://registry.npmjs.org/@modelcontextprotocol%2fserver-variflight - Not found
```

## 问题分析

1. `@modelcontextprotocol/server-variflight` 包在npm注册表中不存在
2. 需要找到替代的航班相关MCP服务器

## 解决方案

### 1. 搜索可用的MCP服务器包

通过 `npm search modelcontextprotocol` 和 `npm search flight` 搜索，发现：
- `@modelcontextprotocol/server-variflight` 不存在
- 但找到了 `flightradar-mcp-server` 包

### 2. 安装替代包

```bash
npm install -g flightradar-mcp-server
```

### 3. 更新MCP配置

修改 `config/mcp.json`：

**修改前：**
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
      "variflight": {
        "command": "npx",
        "args": [
          "-y",
          "@modelcontextprotocol/server-variflight"
        ]
      }
    }
}
```

**修改后：**
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
      }
    }
}
```

## 变更内容

1. **移除不存在的包**：删除了 `@modelcontextprotocol/server-variflight` 配置
2. **添加替代包**：使用 `flightradar-mcp-server` 作为航班信息MCP服务器
3. **更新服务器名称**：从 `variflight` 改为 `flightradar`

## 影响范围

- 修复了服务启动时的MCP服务器加载错误
- 为旅游智能体提供了航班信息查询功能
- 确保生成的代码中包含正确的MCP工具配置

## 测试状态

- [x] 安装 `flightradar-mcp-server` 包
- [x] 更新 `config/mcp.json` 配置
- [ ] 重启服务并验证功能
- [ ] 测试旅游智能体生成和部署

## 注意事项

1. `flightradar-mcp-server` 提供航班跟踪和状态信息功能
2. 需要确保生成的代码中的MCP配置也相应更新
3. 可能需要更新代码生成器中的MCP工具映射

## 后续工作

1. 重启服务并验证MCP工具加载
2. 测试旅游智能体代码生成
3. 验证生成的代码中MCP配置的正确性
4. 如有需要，更新代码生成器中的MCP工具映射 