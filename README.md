# Home Device Control

小米智能家居设备控制工具，支持设备查询、控制和场景执行。

## 功能特性

- ✅ 设备列表查询
- ✅ 设备开关控制（灯、插座等）
- ✅ 亮度/温度调节
- ✅ 智能音箱控制（暂停、下一首、上一首）
- ✅ 语音指令发送
- ✅ 场景执行
- ✅ 多格式输出（人类可读 / JSON）

## 安装

```bash
pip install git+https://github.com/ddandre32/HomeDeviceControl.git
```

## 快速开始

### 1. 配置认证

```bash
# 获取授权 URL
home-device oauth-url

# 访问 URL 登录小米账号，获取授权码

# 完成认证
home-device auth <授权码>
```

### 2. 查看设备

```bash
home-device list-devices
```

### 3. 控制设备

```bash
# 打开台灯
home-device --yes control <device_id> turn_on

# 关闭台灯
home-device --yes control <device_id> turn_off

# 暂停音箱
home-device --yes control <speaker_id> speaker_pause
```

## 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `list-devices` | 列出所有设备 | `home-device list-devices` |
| `control` | 控制设备 | `home-device control <id> <action>` |
| `list-scenes` | 列出场景 | `home-device list-scenes` |
| `execute-scene` | 执行场景 | `home-device execute-scene <id>` |
| `check` | 检查状态 | `home-device check` |
| `doctor` | 诊断问题 | `home-device doctor` |

## 支持的动作

### 通用设备
- `turn_on` - 打开设备
- `turn_off` - 关闭设备
- `set_brightness` - 设置亮度（0-100）
- `set_temperature` - 设置温度

### 智能音箱
- `speaker_pause` - 暂停播放
- `speaker_next` - 下一首
- `speaker_previous` - 上一首
- `voice_command` - 语音指令（音箱播报文字）

## 全局选项

**注意**：全局选项必须放在子命令之前！

```bash
home-device --json list-devices
home-device --yes control <id> turn_on
home-device --dry-run control <id> turn_on
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 格式输出 |
| `--dry-run` | 预览模式 |
| `--yes` | 自动确认 |
| `--quiet` | 静默模式 |

## 文档

- [详细文档](SKILL.md) - 完整的使用指南
- [测试报告](TEST_REPORT.md) - 功能测试结果
- [更新报告](UPDATE_REPORT.md) - 版本更新记录

## 注意事项

1. **认证有效期**: OAuth 令牌有效期为 30 天
2. **音箱音量**: 只读属性，无法通过 API 设置
3. **语音指令**: `voice_command` 会让音箱播报文字，不是执行指令
4. **网络要求**: 需要访问小米云服务

## 许可证

MIT License
