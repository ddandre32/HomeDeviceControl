# XiaomiDeviceControl

小米智能家居自然语言控制 Skill for OpenClaw

## 功能特点

- 🎯 **自然语言控制** - 用日常语言控制设备
- ⚡ **批量控制** - 同时控制多个设备
- ⏰ **延迟控制** - 支持定时和延迟操作
- 🔐 **摩斯密码** - 用灯光发送摩斯密码
- 🎭 **场景执行** - 执行预设智能场景
- 🔍 **模糊匹配** - 智能识别设备名称

## 快速开始

### 安装

```bash
./install.sh
```

### 认证

```bash
miot system oauth-url
# 访问输出的URL，登录小米账号
miot system auth <授权码>
```

### 测试

```bash
# 列出设备
python3 skill.py list_devices

# 自然语言控制
python3 skill.py natural_language_control "打开客厅的灯"
```

## 使用示例

### 基础控制
```bash
"打开客厅的灯"
"关闭台灯"
"把卧室灯亮度调到50"
```

### 延迟控制
```bash
"5秒后关闭台灯"
"10秒后打开客厅灯"
```

### 批量控制
```bash
"打开客厅灯和卧室灯"
"同时关闭所有灯"
```

### 摩斯密码
```bash
"用台灯发送摩斯密码，信息是【你好】"
python3 skill.py send_morse_code "SOS"
```

## 文件结构

```
XiaomiDeviceControl/
├── skill.py          # 主程序
├── skill.json        # Skill 配置
├── SKILL.md          # 使用文档
├── README.md         # 项目说明
├── EXAMPLES.md       # 详细示例
└── install.sh        # 安装脚本
```

## 依赖

- Python 3.9+
- XMIoT CLI
- OpenClaw

## License

MIT
