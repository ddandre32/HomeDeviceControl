# Home Device Control CLI

## 安装

```bash
pip install -e .
```

安装后提供 `hdc` 命令。

## 快速开始

```bash
# 认证
hdc miot system oauth-url          # 小米: 获取 OAuth URL
hdc miot system auth <授权码>       # 小米: 完成认证
hdc haier auth                     # 海尔: 初始化 MCP 连接

# 查看设备
hdc device list                    # 所有品牌
hdc device list --brand xiaomi     # 仅小米

# 控制设备（使用品牌专属命令）
hdc miot device prop set <did> 2 1 true   # 小米: 开灯
hdc miot device action <did> 3 3          # 小米: 音箱暂停
hdc haier control <did> turn_on           # 海尔: 开灯
```

## 命令结构

```
hdc
├── device                       统一设备查询（跨品牌）
│   └── list [--brand] [--online] [--type] [--room]
├── miot                         小米专属
│   ├── device
│   │   ├── list / get / spec
│   │   ├── prop get / set
│   │   ├── action
│   │   └── batch
│   ├── scene
│   │   ├── list / get / search / run
│   └── system
│       ├── status / oauth-url / auth
│       ├── config / notify
│       └── web
└── haier                        海尔专属
    ├── auth / list / control
    ├── status / tools
```

## 全局选项

| 选项 | 说明 |
|------|------|
| `--json` | JSON 输出 |
| `--format [json\|yaml\|table\|human]` | 输出格式 |
| `--config <path>` | 配置文件路径 |
| `-v, --verbose` | 详细输出 |

## 输出格式

| 格式 | 说明 | 默认场景 |
|------|------|---------|
| `json` | 结构化 JSON | 非 TTY（管道/脚本） |
| `table` | 表格对齐 | TTY（终端交互） |
| `yaml` | YAML 格式 | 手动指定 |
| `human` | 简化键值对 | 手动指定 |

## 配置文件

默认路径：`~/.miot/config.json`

## 环境变量

| 变量 | 说明 |
|------|------|
| `HDC_CONFIG_PATH` | 配置文件路径 |
| `MIOT_CLOUD_SERVER` | 云服务器 (cn/sg/us) |
| `MIOT_FORMAT` | 默认输出格式 |
| `MIOT_ACCESS_TOKEN` | 访问令牌（CI 使用） |
