# Home Device Control

通过 CLI 控制智能家居设备。支持小米、海尔等多品牌。

## Metadata

| 字段 | 值 |
|------|-----|
| name | smart-home |
| version | 2.0.0 |
| description | 控制智能家居设备的原子工具，支持多品牌渠道 |

## Triggers

| 意图 | 关键词 |
|------|--------|
| 设备控制 | 打开/关闭/调节/设置 + 设备名 |
| 设备查询 | 有哪些设备/设备列表/查询设备 |
| 场景执行 | 执行场景/运行模式 |

## Quick Start

```bash
# 列出设备
miot device list

# 控制设备
miot device prop set <device_id> <siid> <piid> <value>

# 执行场景
miot scene run <scene_id>
```

## 支持的渠道

| 渠道 | CLI 命令 | 状态 |
|------|---------|------|
| 小米 | `miot` | 需配置 |
| 海尔 | `haier-cli` | 预留 |

## 配置

### 小米

```bash
# 获取授权 URL
miot system oauth-url

# 访问 URL，登录账号，获取授权码

# 完成认证
miot system auth <授权码>
```

## 诊断

```bash
# 检查渠道状态
python3 doctor.py
```

## 说明

- 本 Skill 只提供**原子操作**（设备控制、查询、场景执行）
- **复杂任务**（如摩斯密码、延时控制、批量操作）由 Agent 自行规划执行
- Agent 直接调用上述 CLI 命令即可
- 设备匹配、意图理解由 Agent/LLM 负责

## 参考

- 小米 CLI 文档: https://github.com/ddandre32/XMIoT
