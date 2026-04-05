# HomeDeviceControl MCP协议改造总结

## 改造概述

将HomeDeviceControl项目中海尔设备的底层控制接口从HTTP REST API改为MCP (Model Context Protocol) 协议，与haier-claw项目保持一致。

## 主要修改

### 1. 依赖更新 (setup.py)
- 添加 `httpx>=0.25.0` - 用于MCP HTTP通信
- 添加 `sseclient-py>=1.8.0` - 用于SSE传输层

### 2. 核心SDK改造

#### haier/client.py (完全重写)
- **协议**: HTTP REST API → MCP over SSE
- **传输层**: aiohttp → httpx + sseclient
- **认证方式**: Bearer Token → MCP initialize握手
- **连接管理**: 添加自动重连和心跳机制（5秒间隔）
- **错误处理**: 添加MCP专用错误类型

**关键特性**:
- SSE长连接保持
- 自动重连机制（5秒间隔）
- 心跳保活（5秒ping）
- 工具发现和调用

#### haier/types.py
- 添加 `MCPToolInfo` - MCP工具信息
- 添加 `MCPCallResult` - MCP调用结果
- 支持JSON Schema解析

#### haier/error.py
- 添加MCP错误码：`MCP_CONNECTION_ERROR`, `MCP_INITIALIZE_FAILED`, `MCP_TOOL_NOT_FOUND`, `MCP_SSE_ERROR`, `MCP_RECONNECT_FAILED`
- 添加 `HaierMCPError` 异常类

### 3. 渠道层适配 (channels/haier.py)
- 更新动作映射表，映射到MCP工具名称：
  - `turn_on` → `lampControl`
  - `turn_off` → `lampControl`
  - `set_brightness` → `lampControl`
  - `set_temperature` → `airConditionerControl`
  - `curtain_control` → `curtainControl`
- 更新状态检查逻辑，检测MCP连接状态
- 移除场景功能（MCP暂不支持）

### 4. CLI层更新

#### cli/commands_haier.py
- 更新 `haier auth` 命令 - MCP初始化（无需用户名密码）
- 添加 `haier tools` 命令 - 列出可用MCP工具
- 更新帮助文档，说明MCP协议使用方式

#### cli/client.py
- 更新HaierClient初始化逻辑，自动调用`initialize()`
- 更新关闭逻辑，调用MCP的`close()`方法

### 5. 导出更新 (haier/__init__.py)
- 导出新的MCP类型和错误类

## 使用方式对比

### 改造前 (REST API)
```bash
# 认证（需要用户名密码）
home-device haier auth --username xxx --password xxx

# 获取设备列表（调用REST API）
home-device haier list

# 控制设备（调用REST API）
home-device haier control <did> turn_on
```

### 改造后 (MCP协议)
```bash
# 初始化MCP连接（建立SSE连接，发送initialize）
home-device haier auth

# 获取设备列表（调用MCP工具getDeviceList）
home-device haier list

# 控制设备（调用MCP工具lampControl等）
home-device haier control <did> turn_on

# 查看可用MCP工具
home-device haier tools
```

## 架构对比

| 维度 | 改造前 (REST API) | 改造后 (MCP协议) |
|------|-------------------|------------------|
| 协议 | HTTP REST API | MCP over SSE |
| 传输层 | 短连接 | 长连接 |
| 认证 | Bearer Token (24h) | initialize握手 |
| 发现机制 | 固定端点 | 动态工具发现 |
| 重连机制 | 无 | 自动重连（5秒） |
| 心跳 | 无 | 5秒ping |
| 设备控制 | POST /api/devices/{id}/control | call_tool("lampControl") |

## 设备类型支持

MCP协议支持的真实设备类型（通过MCP工具）：
- `getDeviceList` - 获取设备列表
- `getDeviceStatus` - 获取设备状态
- `lampControl` - 灯控制
- `airConditionerControl` - 空调控制
- `curtainControl` - 窗帘控制

## 注意事项

1. **场景功能**: MCP协议暂不支持场景功能，相关命令返回空列表或错误提示
2. **认证变化**: 无需用户名密码，通过`haier auth`自动建立MCP连接
3. **网络要求**: 需要保持SSE长连接，断开后会自动重连
4. **设备真实性**: 现在只通过MCP协议获取真实设备，不再使用本地模拟数据

## 测试建议

1. 运行 `home-device haier auth` 初始化MCP连接
2. 运行 `home-device haier tools` 查看可用工具
3. 运行 `home-device haier list` 获取设备列表
4. 运行 `home-device haier control <did> turn_on` 测试设备控制

## 后续优化方向

1. 支持更多MCP工具（如空调控制、窗帘控制）
2. 添加MCP工具参数自动补全
3. 支持MCP会话持久化
4. 添加MCP连接状态监控
