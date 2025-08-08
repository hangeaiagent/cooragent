# MCP组件配置方法

## 概述

本文档详细说明了Cooragent系统中各种Model Context Protocol (MCP) 组件的安装、配置和验证方法。MCP是一个开放标准，允许AI系统与外部工具和数据源安全交互。

## 系统架构

Cooragent通过`config/mcp.json`文件统一管理所有MCP服务器配置。每个MCP组件作为独立的服务器运行，通过标准化接口与主系统通信。

## 当前已集成的MCP组件

### 1. 📁 Filesystem Server - 文件系统操作

#### 功能特性
- 安全的文件和目录读写操作
- 限制访问特定目录（白名单机制）
- 支持文件创建、修改、删除、移动
- 目录遍历和搜索功能

#### 安装配置

**步骤1: 验证组件可用性**
```bash
# 测试安装
npx -y @modelcontextprotocol/server-filesystem /Users/a1/work/cooragent/generated_projects
```

**步骤2: 配置文件设置**
在`config/mcp.json`中添加：
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
    }
  }
}
```

**步骤3: 重启服务验证**
```bash
./start_local_dev.sh
```

#### 使用示例
```
"帮我在generated_projects目录下创建一个新的项目文件夹"
"查看generated_projects目录中的所有文件"
"删除指定的项目文件"
```

---

### 2. 📊 Excel MCP Server - Excel文档处理

#### 功能特性
- Excel文件读写操作
- 工作表管理（创建、删除、重命名）
- 单元格数据操作
- 公式计算和数据分析
- 图表生成

#### 安装配置

**步骤1: 安装组件**
```bash
# 在conda环境中安装
conda activate cooragent
npx --yes @negokaz/excel-mcp-server
```

**步骤2: 配置文件设置**
在`config/mcp.json`中添加：
```json
{
  "mcpServers": {
    "excel": {
      "command": "npx",
      "args": ["--yes", "@negokaz/excel-mcp-server"],
      "env": {
        "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000"
      }
    }
  }
}
```

**步骤3: 验证安装**
```bash
# 检查服务状态
curl http://localhost:8000/health
```

#### 使用示例
```
"创建一个销售数据的Excel表格"
"在Excel中添加图表分析"
"计算表格中的数据统计"
```

---

### 3. 📄 MCP-Doc - Word文档处理

#### 功能特性
- Word文档创建和编辑
- 文本格式化（字体、颜色、样式）
- 段落和章节管理
- 表格插入和编辑
- 图片和媒体插入

#### 安装配置

**步骤1: 克隆项目**
```bash
cd cooragent/src/tools
git clone https://github.com/MeterLong/MCP-Doc.git
```

**步骤2: 安装依赖**
```bash
cd MCP-Doc
pip install -r requirements.txt
```

**步骤3: 测试服务器**
```bash
python -c "import sys; sys.path.append('.'); import server; print('MCP-Doc服务器测试成功')"
```

**步骤4: 配置文件设置**
在`config/mcp.json`中添加：
```json
{
  "mcpServers": {
    "mcp-doc": {
      "command": "python",
      "args": ["/Users/a1/work/cooragent/src/tools/MCP-Doc/server.py"],
      "env": {}
    }
  }
}
```

#### 使用示例
```
"创建一个项目需求文档"
"生成Word格式的技术报告"
"制作产品使用手册"
```

---

### 4. 🖼️ MCP Image Downloader - 图片下载优化

#### 功能特性
- 高效图片下载
- 图片格式转换和优化
- 批量图片处理
- 图片压缩和尺寸调整
- 支持多种图片格式

#### 安装配置

**步骤1: 克隆项目**
```bash
cd cooragent/src/tools
git clone https://github.com/qpd-v/mcp-image-downloader.git
```

**步骤2: 安装Node.js依赖**
```bash
cd mcp-image-downloader
npm install
```

**步骤3: 构建项目**
```bash
npm run build
```

**步骤4: 验证构建结果**
```bash
ls -la build/index.js
```

**步骤5: 配置文件设置**
在`config/mcp.json`中添加：
```json
{
  "mcpServers": {
    "image-downloader": {
      "command": "node",
      "args": ["/Users/a1/work/cooragent/src/tools/mcp-image-downloader/build/index.js"],
      "env": {}
    }
  }
}
```

#### 使用示例
```
"下载并优化网站上的产品图片"
"批量处理图片尺寸调整"
"转换图片格式为WebP提高性能"
```

---

### 5. ✈️ Variflight MCP - 航班信息查询

#### 功能特性
- 实时航班状态查询
- 航班时刻表查询
- 机场信息和动态
- 航班延误统计
- 航线信息查询

#### 安装配置

**步骤1: 测试组件**
```bash
npx -y @variflight-ai/variflight-mcp &
sleep 5
pkill -f variflight
```

**步骤2: 配置文件设置**
在`config/mcp.json`中添加：
```json
{
  "mcpServers": {
    "variflight": {
      "command": "npx",
      "args": [
        "-y",
        "@variflight-ai/variflight-mcp"
      ],
      "env": {
        "X_VARIFLIGHT_KEY": "sk-8pzBmAr8jdNHvuz5C4z579yEDbDJWPL0JLBzTDjCbu4"
      }
    }
  }
}
```

**步骤3: 重启服务验证**
```bash
# 停止当前服务
pkill -f "generator_cli"

# 重新启动
conda activate cooragent
python generator_cli.py server --host 0.0.0.0 --port 8000 &
```

#### 使用示例
```
"查询CA1234航班的实时状态"
"北京到上海的航班时刻表"
"首都机场今天的航班延误情况"
```

---

### 6. 🗺️ AMAP - 地图服务

#### 功能特性
- 地图位置查询
- 路线规划
- 地理编码和逆地理编码
- POI（兴趣点）搜索

#### 配置设置
```json
{
  "mcpServers": {
    "AMAP": {
      "url": "https://mcp.amap.com/sse",
      "env": {
        "AMAP_MAPS_API_KEY": "72a87689c90310d3a119865c755a5681"
      }
    }
  }
}
```

---

## 完整配置文件示例

`config/mcp.json`完整配置：
```json
{
  "mcpServers": {
    "aws-kb-retrieval": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-aws-kb-retrieval"],
      "env": {
        "AWS_ACCESS_KEY_ID": "YOUR_ACCESS_KEY_HERE",
        "AWS_SECRET_ACCESS_KEY": "YOUR_SECRET_ACCESS_KEY_HERE",
        "AWS_REGION": "YOUR_AWS_REGION_HERE"
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
    "excel": {
      "command": "npx",
      "args": ["--yes", "@negokaz/excel-mcp-server"],
      "env": {
        "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000"
      }
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
    "variflight": {
      "command": "npx",
      "args": [
        "-y",
        "@variflight-ai/variflight-mcp"
      ],
      "env": {
        "X_VARIFLIGHT_KEY": "sk-8pzBmAr8jdNHvuz5C4z579yEDbDJWPL0JLBzTDjCbu4"
      }
    },
    "AMAP": {
      "url": "https://mcp.amap.com/sse",
      "env": {
        "AMAP_MAPS_API_KEY": "72a87689c90310d3a119865c755a5681"
      }
    }
  }
}
```

## 通用配置步骤

### 1. 环境准备
```bash
# 确保conda环境激活
conda activate cooragent

# 确保Node.js可用（某些组件需要）
node --version
npm --version
```

### 2. 组件安装
```bash
# 对于NPM包
npx -y @package-name

# 对于Python项目
cd src/tools
git clone <repository-url>
cd <project-name>
pip install -r requirements.txt

# 对于Node.js项目
npm install
npm run build
```

### 3. 配置更新
1. 编辑`config/mcp.json`
2. 添加相应的服务器配置
3. 设置必要的环境变量

### 4. 服务重启
```bash
# 停止当前服务
pkill -f "generator_cli"

# 重新启动
./start_local_dev.sh
```

### 5. 验证测试
```bash
# 健康检查
curl http://localhost:8000/health

# 查看服务状态
ps aux | grep "generator_cli"

# 检查日志
tail -f logs/server.log
```

## 故障排除

### 常见问题

**问题1: 端口占用**
```bash
# 检查端口占用
lsof -i :8000

# 强制停止占用进程
pkill -f "generator_cli"
pkill -f "8000"
```

**问题2: 依赖缺失**
```bash
# Python依赖
pip install -r requirements.txt

# Node.js依赖
npm install

# 系统级依赖
conda install <package-name>
```

**问题3: 权限问题**
```bash
# 检查文件权限
ls -la config/mcp.json

# 修复权限
chmod 644 config/mcp.json
```

**问题4: 配置文件语法错误**
```bash
# 验证JSON语法
python -m json.tool config/mcp.json

# 或使用在线JSON验证器
```

### 日志查看

**应用日志**
```bash
# 实时查看服务日志
tail -f logs/server.log

# 查看生成器日志
tail -f logs/generator.log

# 查看模板日志
grep "template_debug" logs/server.log
```

**MCP组件日志**
```bash
# 查看特定组件启动信息
grep "MCP.*running on stdio" logs/server.log

# 查看组件错误
grep "ERROR.*MCP" logs/server.log
```

## 性能优化

### 1. 内存管理
- 定期重启长时间运行的MCP服务
- 监控内存使用情况
- 配置合适的环境变量限制

### 2. 并发处理
- 根据系统性能调整并发连接数
- 使用连接池管理MCP服务连接
- 实施请求速率限制

### 3. 缓存策略
- 启用适当的缓存机制
- 定期清理临时文件
- 优化数据传输格式

## 扩展新组件

### 添加新的MCP组件的步骤：

1. **调研组件**
   - 查看组件文档和API
   - 了解功能特性和依赖需求

2. **测试安装**
   - 在测试环境验证安装
   - 确认组件正常工作

3. **配置集成**
   - 更新`config/mcp.json`
   - 设置必要的环境变量

4. **验证功能**
   - 重启Cooragent服务
   - 测试组件功能
   - 检查日志输出

5. **文档更新**
   - 更新此配置文档
   - 添加使用示例
   - 记录故障排除方法

## 安全考虑

### 1. API密钥管理
- 使用环境变量存储敏感信息
- 定期轮换API密钥
- 限制密钥权限范围

### 2. 文件系统访问
- 严格限制文件访问路径
- 使用白名单机制
- 定期审计文件操作

### 3. 网络安全
- 配置防火墙规则
- 使用HTTPS加密通信
- 监控异常网络活动

## 维护计划

### 定期维护任务：

**每日**
- 检查服务运行状态
- 监控日志错误信息
- 验证关键功能正常

**每周**
- 清理临时文件和日志
- 检查组件更新
- 性能监控和优化

**每月**
- 更新组件版本
- 安全漏洞扫描
- 备份配置文件

## 总结

通过本配置指南，您可以：
- ✅ 成功安装和配置所有MCP组件
- ✅ 理解各组件的功能特性和使用场景
- ✅ 掌握故障排除和性能优化方法
- ✅ 具备扩展新组件的能力

Cooragent的MCP组件生态为多智能体系统提供了强大的工具支持，通过合理配置和维护，可以显著提升系统的功能丰富度和实用性。

## 🌟 真实旅游API集成配置（2025-08-07更新）

### 真实MCP客户端配置

为了提供真实的旅游数据服务，系统已集成以下真实API：

#### 1. 配置真实API密钥

创建或更新`.env`文件：
```bash
# 高德地图API（地理信息、天气、路线）
AMAP_API_KEY=demo_amap_key_please_replace

# 携程API（酒店、机票、旅游套餐）
CTRIP_API_KEY=demo_ctrip_key_please_replace

# 大众点评API（餐厅、美食推荐）
DIANPING_API_KEY=demo_dianping_key_please_replace
```

#### 2. 真实MCP服务器配置

更新`config/mcp.json`：
```json
{
    "mcpServers": {
        "amap": {
            "url": "https://restapi.amap.com/v3",
            "env": {
                "AMAP_API_KEY": "demo_amap_key_please_replace"
            }
        },
        "ctrip": {
            "url": "https://api.ctrip.com/v1",
            "env": {
                "CTRIP_API_KEY": "demo_ctrip_key_please_replace"
            }
        },
        "dianping": {
            "url": "https://api.dianping.com/v1",
            "env": {
                "DIANPING_API_KEY": "demo_dianping_key_please_replace"
            }
        }
    }
}
```

#### 3. API注册地址

| 服务商 | 注册地址 | 说明 |
|--------|----------|------|
| 🗺️ **高德地图** | https://lbs.amap.com/api/ | 个人开发者友好，免费额度充足 |
| 🏨 **携程** | https://open.ctrip.com/ | 需要商业合作，企业账号 |
| 🍜 **大众点评** | https://open.dianping.com/ | 需要审核，个人开发可能受限 |

#### 4. 真实MCP客户端特性

✅ **已实现功能**：
- 高德地图地理编码和天气查询
- 携程酒店和航班信息查询框架
- 大众点评餐厅和美食推荐框架
- 异步HTTP请求处理
- 错误处理和降级机制
- API响应数据结构化处理

✅ **安全特性**：
- 环境变量管理API密钥
- HTTP超时和重试机制
- 错误日志记录
- 降级服务支持

#### 5. 使用示例

启动系统后，真实MCP工具会自动调用：

```python
# 系统自动调用真实API
from src.tools.real_mcp_client import call_real_mcp_tools

# 获取旅游数据
mcp_data = await call_real_mcp_tools(
    tools_config={'amap': {}, 'ctrip': {}, 'dianping': {}},
    destination="北京",
    departure="上海"
)
```

#### 6. 快速配置指南

1. **获取高德地图API密钥**（推荐优先）
2. **更新环境变量文件**
3. **重启服务验证**：`./restart_with_clean_logs.sh`
4. **测试旅游规划功能**

详细配置说明请参考：`docs/MCP_API_Keys_Setup.md`

### 系统架构更新

- 移除了所有模拟MCP调用代码
- 集成真实HTTP API客户端
- 实现了完整的错误处理和降级机制
- 支持多个旅游API服务商同时调用

---

**最后更新**: 2025-08-07  
**文档版本**: v2.0（真实API集成版）  
**适用系统**: Cooragent v1.0+ 