# Home Device Control

通过 CLI 控制智能家居设备。支持小米、海尔等多品牌。

## Metadata

| 字段 | 值 |
|------|-----|
| name | home-device-control |
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
# 安装
./install.sh

# 认证
home-device oauth-url
# 访问 URL，登录账号，获取授权码
home-device auth <授权码>

# 列出设备
home-device list

# 控制设备
home-device control <device_id> turn_on
home-device control <device_id> turn_off
```

## 支持的渠道

| 渠道 | 状态 | 说明 |
|------|------|------|
| 小米 | ✅ 可用 | 通过 miot SDK |
| 海尔 | ⚠️ 预留 | 待实现 |

## 安装

### 方法 1: 直接安装（推荐）

```bash
git clone https://github.com/ddandre32/HomeDeviceControl.git
cd HomeDeviceControl
./install.sh
```

### 方法 2: pip 安装

```bash
pip install git+https://github.com/ddandre32/HomeDeviceControl.git
```

## 配置

### 小米

```bash
# 获取授权 URL
home-device oauth-url

# 访问 URL，登录账号，获取授权码

# 完成认证
home-device auth <授权码>
```

## 诊断

```bash
# 检查渠道状态
home-device doctor
```

## 说明

- 本 Skill 只提供**原子操作**（设备控制、查询、场景执行）
- **复杂任务**（如摩斯密码、延时控制、批量操作）由 Agent 自行规划执行
- Agent 直接调用上述 CLI 命令即可
- 设备匹配、意图理解由 Agent/LLM 负责

## Python API

```python
from channels import get_channel

# 获取小米渠道
xiaomi = get_channel("xiaomi")

# 列出设备
devices = xiaomi.list_devices()

# 控制设备
result = xiaomi.control_device("light_001", "turn_on")
```

## 参考

- GitHub: https://github.com/ddandre32/HomeDeviceControl
