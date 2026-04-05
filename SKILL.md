---
name: home-device-control
description: "控制小米/海尔智能家居设备的原子工具，支持设备查询、控制和场景执行"
homepage: https://github.com/ddandre32/HomeDeviceControl
metadata:
  openclaw:
    emoji: "🏠"
    requires:
      bins: ["home-device"]
      env: ["MIOT_TOKEN", "MIOT_UUID"]
      config: ["channels.xiaomi.enabled", "channels.haier.enabled"]
    primaryEnv: "MIOT_TOKEN"
    install:
      - id: "pip"
        kind: "pip"
        package: "git+https://github.com/ddandre32/HomeDeviceControl.git"
        bins: ["home-device"]
        label: "Install via pip"
    complexity: "high"
---

# Home Device Control

通过 CLI 控制小米/海尔智能家居设备。提供原子操作，复杂任务由 Agent 规划执行。

海尔设备采用 MCP (Model Context Protocol) 协议，通过 SSE 传输层与海尔U+平台通信。

## 使用场景

✅ **使用时机**:
- 控制已配置的小米/海尔智能家居设备（开关、调节亮度/温度）
- 查询设备列表和状态
- 执行预设的智能场景（仅小米）
- 检查渠道连接状态
- **智能音箱语音控制**（播放、暂停、切换歌曲）

❌ **不适用场景**:
- 设备初次配对和配网（需使用米家App/海尔智家App）
- 创建或修改智能场景
- 设备固件升级
- 非小米/海尔品牌设备控制
- **直接设置音箱音量**（音量属性只读）
- **海尔场景执行**（MCP协议暂不支持）

## 安装

```bash
pip install git+https://github.com/ddandre32/HomeDeviceControl.git
```

## 配置

### 1. 小米设备认证

```bash
# 获取 OAuth URL
home-device oauth-url

# 访问 URL 登录小米账号，获取授权码

# 完成认证
home-device auth <授权码>
```

### 2. 海尔设备MCP连接初始化

```bash
# 初始化MCP连接（建立SSE连接，发送initialize握手）
home-device haier auth

# MCP协议特点：
# - 使用SSE长连接传输
# - 支持自动重连（5秒间隔）
# - 支持心跳保活（5秒ping）
```

### 3. 验证配置

```bash
home-device doctor
```

## 常用命令

### 列出设备

```bash
# 人类可读格式（默认）
home-device list-devices

# JSON 格式（注意：--json 在子命令前）
home-device --json list-devices

# 海尔设备列表
home-device haier list

# 海尔设备JSON格式
home-device --json haier list
```

### 控制设备

```bash
# 打开设备
home-device control <device_id> turn_on

# 关闭设备
home-device control <device_id> turn_off

# 设置亮度（0-100）
home-device control <device_id> set_brightness --value 50

# 设置温度
home-device control <device_id> set_temperature --value 24

# 预览模式（注意：--dry-run 在子命令前）
home-device --dry-run control <device_id> turn_on

# 自动确认（注意：--yes 在子命令前）
home-device --yes control <device_id> turn_on

# 海尔设备控制
home-device haier control <device_id> turn_on
home-device haier control <device_id> set_brightness --value 50
```

### 海尔设备管理 (MCP协议)

海尔设备采用 MCP (Model Context Protocol) 协议，通过 SSE 传输层与海尔U+平台通信。

```bash
# 初始化MCP连接（建立SSE连接，发送initialize握手）
home-device haier auth

# 列出可用的MCP工具
home-device haier tools

# 查看海尔设备列表（通过MCP getDeviceList工具）
home-device haier list

# 获取设备状态（通过MCP getDeviceStatus工具）
home-device haier status <device_id>

# 控制设备（通过MCP工具调用）
home-device haier control <device_id> turn_on      # 调用lampControl
home-device haier control <device_id> turn_off     # 调用lampControl
home-device haier control <device_id> set_brightness --value 50  # 调用lampControl
```

**MCP协议特点**：
- 使用SSE长连接传输，支持自动重连（5秒间隔）
- 支持心跳保活（5秒ping）
- 动态工具发现（`haier tools`查看可用工具）
- 无需用户名密码认证，通过initialize握手完成

**注意**：海尔设备暂不支持场景功能（MCP协议限制）

### 智能音箱控制

⚠️ **重要区别**：音箱有两种控制方式

#### 方式一：动作控制（真正执行播放控制）
```bash
# 暂停（siid=3, aiid=2）
home-device control <speaker_id> speaker_pause

# 下一首（siid=3, aiid=3）
home-device control <speaker_id> speaker_next

# 上一首（siid=3, aiid=4）
home-device control <speaker_id> speaker_previous
```

**注意**：部分音箱不支持"播放"动作（因为没有当前播放队列），需要使用语音指令开始播放。

#### 方式二：语音指令（音箱播报文字）
```bash
# 发送语音指令（音箱会播报这段文字）
home-device control <speaker_id> voice_command --value "播放孙燕姿的歌曲"

# 注意：这不是执行指令，而是让音箱说出这句话
```

**区别说明**：
- **动作控制** (`speaker_*`): 真正控制播放状态
- **语音指令** (`voice_command`): 音箱播报文字，不执行动作

### 场景管理

```bash
# 列出场景
home-device list-scenes

# 执行场景
home-device execute-scene <scene_id>
```

### 诊断检查

```bash
# 检查渠道状态
home-device check

# 检查海尔渠道状态
home-device haier status
```

## 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `list-devices` | 列出所有设备 | `home-device list-devices` / `home-device --json list-devices` |
| `control` | 控制设备 | `home-device control <id> <action>` / `home-device --dry-run control <id> <action>` |
| `list-scenes` | 列出场景 | `home-device list-scenes` / `home-device --json list-scenes` |
| `execute-scene` | 执行场景 | `home-device execute-scene <id>` / `home-device --yes execute-scene <id>` |
| `check` | 检查状态 | `home-device check` / `home-device --json check` |
| `doctor` | 诊断问题 | `home-device doctor` |
| `oauth-url` | 获取授权链接 | `home-device oauth-url` |
| `auth` | 完成认证 | `home-device auth <code>` |

## 动作类型

### 通用设备动作

| 动作 | 说明 | 需要 value |
|------|------|-----------|
| `turn_on` | 打开设备 | 否 |
| `turn_off` | 关闭设备 | 否 |
| `set_brightness` | 设置亮度 | 是 (0-100) |
| `set_temperature` | 设置温度 | 是 (摄氏度) |

### 智能音箱动作

| 动作 | 说明 | 效果 |
|------|------|------|
| `speaker_pause` | 暂停播放 | ✅ 真正暂停 |
| `speaker_next` | 下一首 | ✅ 切换下一首 |
| `speaker_previous` | 上一首 | ✅ 切换上一首 |
| `voice_command` | 语音指令 | ⚠️ 音箱播报文字，不执行动作 |

**注意**：`voice_command` 会让音箱播报文字内容，不是执行指令。例如发送"播放音乐"，音箱会说出"播放音乐"这句话，而不是真的播放音乐。

## 全局选项

**注意**: 全局选项必须放在子命令之前！

| 选项 | 说明 | 示例 |
|------|------|------|
| `--json` | 输出 JSON 格式 | `home-device --json check` |
| `--dry-run` | 预览模式，不实际执行 | `home-device --dry-run control light_01 turn_on` |
| `--yes` | 自动确认，跳过提示 | `home-device --yes control light_01 turn_off` |
| `--quiet` | 静默模式，只输出结果 | `home-device --quiet --yes control light_01 turn_on` |
| `--channel` | 指定渠道（默认: xiaomi） | `home-device --channel xiaomi list-devices` |

## 设备类型说明

### 灯类设备
- 支持：`turn_on`, `turn_off`, `set_brightness`
- 示例：台灯、吸顶灯

### 空调/温控设备
- 支持：`turn_on`, `turn_off`, `set_temperature`
- 示例：空调、暖气

### 智能音箱
- 支持：`speaker_play`, `speaker_pause`, `speaker_next`, `speaker_previous`
- 不支持：`set_brightness`（音量只读）
- 注意：使用 `voice_command` 会让音箱播报文字，不是执行指令

### 摄像头
- 支持：`turn_on`, `turn_off`
- 示例：小米智能摄像机

### 控制面板
- 支持：有限，主要用于控制子设备
- 示例：小米智能中控屏

## 注意事项

- **认证有效期**: OAuth 令牌有效期为 30 天，过期需重新授权
- **设备缓存**: 设备列表会本地缓存 5 分钟，使用 `--refresh` 强制刷新
- **速率限制**: API 调用有速率限制，频繁操作可能触发限制
- **网络要求**: 需要访问小米云服务，确保网络连接正常
- **设备状态**: 设备离线时控制命令会失败，先检查设备在线状态
- **音箱音量**: 智能音箱的音量属性是只读的，无法通过 API 设置
- **语音指令**: `voice_command` 动作会让音箱播报文字，不是执行指令

## Python API

```python
from channels import get_channel

# 获取渠道
xiaomi = get_channel("xiaomi")
haier = get_channel("haier")

# 列出设备
xiaomi_devices = xiaomi.list_devices()
haier_devices = haier.list_devices()

# 控制设备
result = xiaomi.control_device("light_001", "turn_on")
result = haier.control_device("haier_light_001", "turn_on")

# 控制音箱播放
result = xiaomi.control_device("speaker_001", "speaker_play")
result = haier.control_device("haier_speaker_001", "speaker_pause")

# 控制音箱暂停
result = xiaomi.control_device("speaker_001", "speaker_pause")
result = haier.control_device("haier_speaker_001", "speaker_pause")
```

## 故障排查

### 认证失败
```bash
# 检查认证状态
home-device doctor

# 重新授权
home-device oauth-url
home-device auth <新授权码>
```

### 设备不响应
- 检查设备是否在线：`home-device list-devices` 或 `home-device haier list`
- 检查网络连接
- 尝试通过米家App/海尔智家App控制，确认设备正常

### 命令无输出
- 添加 `--json` 查看结构化错误信息
- 检查 `~/.home-device-control/` 目录权限

### 音箱控制问题
- **问题**: 发送 `voice_command` 但音箱只是播报文字
- **解决**: 使用 `speaker_play`, `speaker_pause` 等动作控制
- **问题**: 无法设置音量
- **解决**: 音箱音量属性只读，需通过语音或物理按键调节

## 参考

- GitHub: https://github.com/ddandre32/HomeDeviceControl
- 小米 IoT 文档: https://home.mi.com
- 海尔 U+ 文档: https://uplus.haier.com
