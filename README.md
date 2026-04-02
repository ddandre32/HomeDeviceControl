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
- ✅ 🆕 **智能家居地图** - 可视化户型图，拖拽设备到房间位置
- ✅ 🆕 **Web 界面** - 浏览器中管理设备和查看实时状态

## 安装

```bash
pip install git+https://github.com/ddandre32/HomeDeviceControl.git
```

## 智能家居地图 (Web 界面)

启动可视化 Web 界面，在浏览器中管理您的智能家居设备。

### 启动 Web 服务器

```bash
# 默认启动（端口 8080）
home-device web

# 指定端口
home-device web --port 3000

# 仅本地访问
home-device web --host 127.0.0.1
```

启动后打开浏览器访问 `http://localhost:8080`

### 功能特性

1. **多家庭支持**
   - 切换不同家庭/公司
   - 每个家庭独立的户型图

2. **户型图编辑**
   - 点击"编辑模式"进入编辑
   - 添加房间并调整大小和位置
   - 右键房间可重命名或删除

3. **设备位置管理**
   - 从左侧设备列表拖拽设备到房间
   - 设备在地图上以图标形式展示
   - 绿色表示开启，灰色表示关闭

4. **实时状态显示**
   - 设备在线/离线状态
   - 灯具开关状态
   - 亮度值实时更新

5. **设备控制**
   - 点击地图上的设备图标
   - 在右侧面板中开关设备
   - 调节灯光亮度
   - 控制音箱播放

### 使用步骤

1. 启动 Web 服务器：`home-device web`
2. 浏览器访问 `http://localhost:8080`
3. 选择您的家庭
4. 点击"编辑模式"
5. 添加房间并调整布局
6. 拖拽设备到对应房间位置
7. 点击"保存"
8. 退出编辑模式，查看实时状态

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
| `web` | 启动 Web 界面 | `home-device web --port 8080` |

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
