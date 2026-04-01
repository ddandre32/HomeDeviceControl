# Home Device Control

整合 XMIoT SDK 的智能家居控制 Skill，支持小米、海尔等多品牌。

## 特点

- ✅ **开箱即用** - 整合 miot SDK，无需额外安装
- ✅ **多品牌支持** - 小米（已完成）、海尔（预留）
- ✅ **原子操作** - 只提供设备控制、查询、场景执行
- ✅ **CLI + Python API** - 支持命令行和编程调用
- ✅ **Token 持久化** - 自动保存，长期使用

## 快速开始

### 安装

```bash
git clone https://github.com/ddandre32/HomeDeviceControl.git
cd HomeDeviceControl
./install.sh
```

### 认证

```bash
# 获取授权 URL
home-device oauth-url

# 访问 URL，登录小米账号，获取授权码

# 完成认证
home-device auth <授权码>
```

### 使用

```bash
# 列出设备
home-device list

# 控制设备
home-device control <device_id> turn_on
home-device control <device_id> turn_off
home-device control <device_id> set_brightness 50

# 执行场景
home-device scene run <scene_id>
```

## Python API

```python
from channels import get_channel

# 获取渠道
xiaomi = get_channel("xiaomi")

# 检查状态
status = xiaomi.check()

# 列出设备
devices = xiaomi.list_devices()

# 控制设备
result = xiaomi.control_device("light_001", "turn_on")

# 执行场景
result = xiaomi.execute_scene("scene_001")
```

## 项目结构

```
HomeDeviceControl/
├── SKILL.md              # Skill 入口文档
├── README.md             # 项目说明
├── setup.py              # 安装配置
├── install.sh            # 安装脚本
├── home_device.py        # 主入口
├── cli/                  # CLI 命令
│   ├── main.py          # CLI 主入口
│   ├── commands_device.py
│   ├── commands_scene.py
│   └── ...
├── channels/             # 多品牌渠道
│   ├── base.py          # 抽象基类
│   ├── xiaomi.py        # 小米渠道
│   └── haier.py         # 海尔渠道（预留）
├── miot/                 # miot SDK
│   ├── __init__.py
│   ├── client.py
│   ├── cloud.py
│   └── ...
└── ...
```

## 支持的设备

### 小米

- 💡 灯（开关、亮度调节）
- 📹 摄像头
- 🔊 音箱
- 🎛️ 智能中控屏
- ...

## 文档

- [架构设计](ARCHITECTURE.md)
- [设计哲学](DESIGN_PHILOSOPHY.md)
- [成功测试报告](SUCCESS_REPORT.md)

## 许可证

MIT
