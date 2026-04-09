---
name: home-device-control
description: "控制小米/海尔智能家居设备的原子工具，支持设备查询、控制和场景执行"
homepage: https://github.com/ddandre32/HomeDeviceControl
metadata:
  openclaw:
    emoji: "🏠"
    requires:
      bins: ["hdc"]
      env: ["MIOT_TOKEN", "MIOT_UUID"]
      config: ["channels.xiaomi.enabled", "channels.haier.enabled"]
    primaryEnv: "MIOT_TOKEN"
    install:
      - id: "pip"
        kind: "pip"
        package: "git+https://github.com/ddandre32/HomeDeviceControl.git"
        bins: ["hdc"]
        label: "Install via pip"
    complexity: "high"
---

# Home Device Control

通过 CLI 控制小米/海尔智能家居设备。提供原子操作，复杂任务由 Agent 规划执行。

- 小米设备：MIoT 协议（REST API + OAuth）
- 海尔设备：MCP 协议（SSE 传输层）

## 使用场景

✅ **使用时机**:
- 查询所有品牌设备列表和状态
- 控制小米/海尔智能家居设备（开关、亮度、温度）
- 执行预设的智能场景（仅小米）
- 智能音箱控制（播放、暂停、切换、语音播报）

❌ **不适用场景**:
- 设备初次配对和配网（需使用米家App/海尔智家App）
- 创建或修改智能场景
- 直接设置音箱音量（部分旧型号只读）
- 海尔场景执行（MCP协议暂不支持）

## 安装

```bash
pip install git+https://github.com/ddandre32/HomeDeviceControl.git
```

## 配置

```bash
# 小米认证
hdc miot system oauth-url        # 获取 OAuth URL
hdc miot system auth <授权码>     # 完成认证

# 海尔认证
hdc haier auth                   # 初始化 MCP 连接

# 验证
python3 doctor.py                # 检查所有渠道状态
```

## 常用命令

### 统一设备查询（跨品牌）

```bash
hdc device list                          # 所有品牌
hdc device list --brand xiaomi           # 仅小米
hdc device list --brand haier            # 仅海尔
hdc device list --online                 # 仅在线
hdc --json device list | jq -r '.data[].did'   # JSON管道
```

### 小米设备控制（hdc miot）

```bash
# 设备列表/详情/SPEC
hdc miot device list
hdc miot device get <did>
hdc miot device spec <did>

# 属性读写
hdc miot device prop get <did> 2 1
hdc miot device prop set <did> 2 1 true      # 开灯
hdc miot device prop set <did> 2 2 50        # 亮度 50%
hdc miot device prop set <did> 2 3 4000      # 色温 4000K

# 执行动作
hdc miot device action <did> 3 3             # 音箱暂停
hdc miot device action <did> 7 3 "你好"      # 语音播报(TTS)
hdc miot device action <did> 7 4 "播放周杰伦"  # 执行语音指令(等同对小爱说话)

# 批量控制
echo '[{"type":"set_prop","did":"x","siid":2,"piid":1,"value":true}]' | hdc miot device batch

# 场景
hdc miot scene list
hdc miot scene search "回家"
hdc miot scene run <scene_id>

# 系统
hdc miot system status
hdc miot system notify "消息"
hdc miot system web                          # 启动 Web 界面
```

### 海尔设备控制（hdc haier）

```bash
hdc haier auth                               # 初始化 MCP 连接
hdc haier list                               # 海尔设备列表
hdc haier control <did> turn_on              # 开灯
hdc haier control <did> set_brightness --value 50
hdc haier control <did> set_temperature --value 24
hdc haier status <did>                       # 设备状态
hdc haier tools                              # 可用 MCP 工具
```

### 智能音箱控制

音箱通过 MIoT SPEC 协议控制，主要涉及两个服务：

| 服务 | SIID | 说明 |
|------|------|------|
| Play Control | 3 | 播放/暂停/上下首 |
| Intelligent Speaker | 7 | 语音播报/执行语音指令/音乐播放 |

常用动作：

| 动作 | SIID/AIID | 命令示例 | 说明 |
|------|-----------|----------|------|
| 播放 | 3/2 | `hdc miot device action <did> 3 2` | 继续播放 |
| 暂停 | 3/3 | `hdc miot device action <did> 3 3` | 暂停播放 |
| 上一首 | 3/5 | `hdc miot device action <did> 3 5` | |
| 下一首 | 3/6 | `hdc miot device action <did> 3 6` | |
| 语音播报 | 7/3 | `hdc miot device action <did> 7 3 "你好"` | TTS朗读文字 |
| 执行语音指令 | 7/4 | `hdc miot device action <did> 7 4 "播放周杰伦"` | 等同对小爱说话 |
| 设置音量 | prop 2/1 | `hdc miot device prop set <did> 2 1 30` | 音量范围 5-100 |

⚠️ 注意：不同型号音箱的 SIID 可能不同，以上基于 Xiaomi 智能音箱 Pro (oh2p) 实测验证。

## 命令参考

| 命令 | 说明 |
|------|------|
| `hdc device list [--brand] [--online]` | 统一设备列表（跨品牌） |
| `hdc miot device list/get/spec` | 小米设备查询 |
| `hdc miot device prop get/set` | 小米属性读写 |
| `hdc miot device action` | 小米动作执行 |
| `hdc miot device batch` | 小米批量控制 |
| `hdc miot scene list/get/search/run` | 小米场景管理 |
| `hdc miot system status/auth/config/notify/web` | 小米系统管理 |
| `hdc haier auth/list/control/status/tools` | 海尔 MCP 管理 |

## 动作类型

| 动作 | 说明 | 品牌 |
|------|------|------|
| `turn_on` / `turn_off` | 开关设备 | 通用 |
| `set_brightness` | 亮度 (0-100) | 通用 |
| `set_color_temperature` | 色温 (Kelvin) | 小米 |
| `set_temperature` | 温度 (摄氏度) | 通用 |
| `speaker_play/pause/stop` | 音箱播放控制 | 小米 |
| `speaker_set_volume` | 设置音量 (5-100) | 小米 |
| `voice_command` | 语音播报文字(TTS) | 小米 |
| `execute_text_directive` | 执行语音指令(等同对小爱说话) | 小米 |
| `curtain_control` | 窗帘控制 (0-100) | 海尔 |

## Python API

```python
from channels import get_channel

xiaomi = get_channel("xiaomi")
haier = get_channel("haier")

devices = xiaomi.list_devices()
result = xiaomi.control_device("958946692", "turn_on")
result = haier.control_device("haier_light_001", "set_brightness", 50)
```

## 注意事项

- OAuth 令牌有效期 30 天，过期需重新授权
- 设备列表本地缓存 5 分钟，`--refresh` 强制刷新
- 音箱音量可通过 `speaker_set_volume` 或 `prop set <did> 2 1 <值>` 设置 (范围 5-100)
- `voice_command` (siid=7/aiid=3) 让音箱播报文字(TTS)，不是执行指令
- `execute_text_directive` (siid=7/aiid=4) 等同对小爱说话，可触发音乐播放等
- 海尔场景功能暂不支持（MCP 协议限制）
