# MCP组件真实API密钥配置指南

## 🔑 API密钥注册和配置

### 1. 高德地图API 🗺️

**注册地址**: https://lbs.amap.com/api/

**注册步骤**:
1. 访问高德开放平台: https://lbs.amap.com/api/
2. 点击"立即注册"或"登录"（如果已有账号）
3. 实名认证（需要身份证信息）
4. 创建应用，选择"Web端"
5. 获取API Key

**配置方法**:
```bash
# 在项目根目录的.env文件中添加
AMAP_API_KEY=your_real_amap_api_key_here
```

**API功能**:
- 地理编码/逆地理编码
- 天气查询
- 路线规划
- POI搜索
- 交通状况

### 2. 携程API 🏨

**注册地址**: https://open.ctrip.com/

**注册步骤**:
1. 访问携程开放平台: https://open.ctrip.com/
2. 注册企业账号（需要营业执照）
3. 申请API接入权限
4. 完成商务谈判和技术对接
5. 获取API密钥和访问权限

**配置方法**:
```bash
# 在项目根目录的.env文件中添加
CTRIP_API_KEY=your_real_ctrip_api_key_here
```

**API功能**:
- 酒店搜索和预订
- 机票搜索和预订
- 旅游套餐查询
- 景点门票预订
- 当地游产品

**注意**: 携程API需要商业合作，个人开发者可能无法直接获取。

### 3. 大众点评API 🍜

**注册地址**: https://open.dianping.com/

**注册步骤**:
1. 访问大众点评开放平台: https://open.dianping.com/
2. 注册开发者账号
3. 申请API权限（需要审核）
4. 提交应用信息和使用场景
5. 获取API密钥

**配置方法**:
```bash
# 在项目根目录的.env文件中添加
DIANPING_API_KEY=your_real_dianping_api_key_here
```

**API功能**:
- 餐厅搜索
- 用户评价查询
- 餐厅详情信息
- 美食推荐
- 评分排行

### 4. 其他推荐API服务

#### 12306火车票 🚄
- **官方网站**: https://kyfw.12306.cn/
- **说明**: 官方购票平台，主要用于用户登录购票
- **第三方接口**: 可考虑使用携程、去哪儿等平台的火车票API

#### 去哪儿网API ✈️
- **注册地址**: https://open.qunar.com/
- **功能**: 机票、酒店、旅游产品搜索

#### 美团API 🛒
- **注册地址**: https://open.meituan.com/
- **功能**: 餐饮、酒店、生活服务

## 🔧 配置文件更新

### 更新.env文件
```bash
# 高德地图
AMAP_API_KEY=demo_amap_key_please_replace

# 携程（需要商业合作）
CTRIP_API_KEY=demo_ctrip_key_please_replace

# 大众点评
DIANPING_API_KEY=demo_dianping_key_please_replace

# 其他API（可选）
QUNAR_API_KEY=demo_qunar_key_please_replace
MEITUAN_API_KEY=demo_meituan_key_please_replace
```

### 更新config/mcp.json
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

## ⚠️ 重要注意事项

### 1. API限制和费用
- **高德地图**: 个人开发者有一定免费额度，超出需付费
- **携程**: 需要商业合作，通常有最低消费要求
- **大众点评**: 需要审核，个人开发可能受限

### 2. 安全建议
- 不要将真实API密钥提交到代码仓库
- 使用环境变量管理敏感信息
- 定期轮换API密钥
- 监控API使用量，避免超额费用

### 3. 开发建议
- 先使用演示密钥进行功能开发
- 实现降级机制，API失败时有备用方案
- 添加缓存机制，减少API调用次数
- 实现请求限制，避免触发API频率限制

### 4. 测试建议
- 使用沙箱环境进行开发测试
- 准备测试数据，避免使用真实用户数据
- 监控API响应时间和错误率

## 🚀 快速开始

1. **获取高德地图API密钥**（推荐优先）:
   - 注册简单，个人开发者友好
   - 免费额度充足，适合测试

2. **配置环境变量**:
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入真实密钥
   ```

3. **测试API连接**:
   ```bash
   python -m src.tools.real_mcp_client
   ```

4. **启动服务**:
   ```bash
   ./restart_with_clean_logs.sh
   ```

---

**文档更新时间**: 2025-08-07
**版本**: v1.0
**状态**: 配置指南完成