# Home Device Control

小米/海尔智能家居设备控制工具，支持设备查询、控制和场景执行。

## 安装

```bash
pip install git+https://github.com/ddandre32/HomeDeviceControl.git
```

## 命令结构

```
hdc                              品牌中立的统一入口
├── device                       统一设备查询（跨品牌）
│   └── list [--brand] [--online]
├── miot                         小米专属
│   ├── device list/get/spec
│   ├── device prop get/set
│   ├── device action
│   ├── device batch
│   ├── scene list/get/search/run
│   └── system status/auth/config/notify/web
└── haier                        海尔专属
    ├── auth/list/control/status/tools
    └── ...
```

## 快速开始

```bash
# 认证
hdc miot system oauth-url        # 小米: 获取授权URL
hdc miot system auth <授权码>     # 小米: 完成认证
hdc haier auth                   # 海尔: 初始化MCP连接

# 查看设备
hdc device list                  # 所有品牌
hdc device list --brand xiaomi   # 仅小米
hdc device list --brand haier    # 仅海尔

# 控制设备（使用品牌专属命令）
hdc miot device prop set <did> 2 1 true   # 小米: 开灯
hdc miot device action <did> 3 3          # 小米: 音箱暂停
hdc miot scene run <scene_id>             # 小米: 执行场景
hdc haier control <did> turn_on           # 海尔: 开灯
```

## 支持的动作

| 动作 | 说明 | 品牌 |
|------|------|------|
| `turn_on` / `turn_off` | 开关设备 | 通用 |
| `set_brightness` | 亮度 (0-100) | 通用 |
| `set_color_temperature` | 色温 (Kelvin) | 小米 |
| `set_temperature` | 温度 (摄氏度) | 通用 |
| `speaker_play/pause/stop/next/previous` | 音箱控制 | 小米 |
| `voice_command` | 语音播报文字 | 小米 |
| `curtain_control` | 窗帘 (0-100) | 海尔 |

## 文档

- [SKILL.md](SKILL.md) - 完整使用指南（Agent 集成参考）
- [cli/PROTOCOL.md](cli/PROTOCOL.md) - CLI 协议规范

## 许可证

MIT License
