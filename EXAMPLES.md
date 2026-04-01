# XiaomiDeviceControl 使用示例

## 目录
1. [基础查询](#基础查询)
2. [设备控制](#设备控制)
3. [批量控制](#批量控制)
4. [延迟控制](#延迟控制)
5. [场景执行](#场景执行)
6. [摩斯密码](#摩斯密码)
7. [复杂组合](#复杂组合)
8. [故障排除](#故障排除)

---

## 基础查询

### 列出所有设备
```bash
python3 skill.py list_devices
```

输出示例：
```json
{
  "success": true,
  "devices": [
    {"id": "12345", "name": "客厅灯", "type": "light", "room": "客厅", "online": true},
    {"id": "12346", "name": "卧室台灯", "type": "light", "room": "卧室", "online": true},
    {"id": "12347", "name": "空气净化器", "type": "purifier", "room": "客厅", "online": true}
  ],
  "count": 3
}
```

### 按条件筛选
```bash
# 仅在线设备
python3 skill.py list_devices --online

# 按房间筛选
python3 skill.py list_devices --room "客厅"

# 按类型筛选
python3 skill.py list_devices --type light
```

### 获取设备信息
```bash
python3 skill.py get_device_info "客厅灯"
# 或
python3 skill.py get_device_info 12345
```

---

## 设备控制

### 开关控制
```bash
# 打开设备
python3 skill.py control_device "客厅灯" turn_on

# 关闭设备
python3 skill.py control_device "客厅灯" turn_off

# 切换状态
python3 skill.py control_device "客厅灯" toggle
```

### 亮度调节
```bash
# 设置亮度为50%
python3 skill.py control_device "台灯" set_brightness 50

# 设置亮度为100%
python3 skill.py control_device "台灯" set_brightness 100
```

### 温度控制
```bash
# 设置空调温度
python3 skill.py control_device "空调" set_temperature 26
```

---

## 批量控制

### 同时打开多个灯
```bash
python3 skill.py batch_control '[
  {"device_name": "客厅灯", "action": "turn_on"},
  {"device_name": "卧室灯", "action": "turn_on"},
  {"device_name": "书房灯", "action": "turn_on"}
]'
```

### 关闭全屋灯光
```bash
python3 skill.py batch_control '[
  {"device_name": "客厅灯", "action": "turn_off"},
  {"device_name": "卧室灯", "action": "turn_off"},
  {"device_name": "厨房灯", "action": "turn_off"},
  {"device_name": "卫生间灯", "action": "turn_off"}
]'
```

### 带延迟的批量控制
```bash
python3 skill.py batch_control '[
  {"device_name": "客厅灯", "action": "turn_on", "delay_after": 2},
  {"device_name": "卧室灯", "action": "turn_on", "delay_after": 2},
  {"device_name": "书房灯", "action": "turn_on"}
]'
```

---

## 延迟控制

### 延迟关闭
```bash
python3 skill.py control_device "台灯" turn_off --delay 5
```

### 创建延迟任务
```bash
python3 skill.py create_delayed_action 10 '{"device_name": "客厅灯", "action": "turn_off"}'
```

---

## 场景执行

### 列出所有场景
```bash
python3 skill.py list_scenes
```

### 执行场景
```bash
# 通过名称
python3 skill.py execute_scene "回家模式"

# 通过ID
python3 skill.py execute_scene scene_12345
```

---

## 摩斯密码

### 发送简单消息
```bash
python3 skill.py send_morse_code "SOS"
```

### 指定设备和速度
```bash
python3 skill.py send_morse_code "HELLO" --name "台灯" --unit 0.3
```

### 发送中文
```bash
python3 skill.py send_morse_code "你好"
```

摩斯密码规则：
- `.` (点) = 短信号，亮 unit_duration 秒
- `-` (划) = 长信号，亮 unit_duration*3 秒
- 字符间间隔 = unit_duration 秒
- 单词间间隔 = unit_duration*3 秒

---

## 复杂组合

### 自然语言指令

```bash
# 基础控制
python3 skill.py natural_language_control "打开客厅的灯"

# 延迟控制
python3 skill.py natural_language_control "5秒后关闭台灯"

# 批量控制
python3 skill.py natural_language_control "打开客厅灯和卧室灯"

# 场景执行
python3 skill.py natural_language_control "执行回家模式"

# 摩斯密码
python3 skill.py natural_language_control "用台灯发送摩斯密码，信息是【你好】"
```

### 更多自然语言示例

| 指令 | 功能 |
|------|------|
| "把客厅的灯打开" | 打开客厅灯 |
| "关掉所有灯" | 关闭所有灯光设备 |
| "5秒后关闭台灯" | 延迟5秒执行 |
| "同时打开客厅和卧室的灯" | 批量控制 |
| "把台灯亮度调到80" | 调节亮度 |
| "执行睡眠模式" | 执行场景 |
| "查看有哪些设备" | 列出设备 |

---

## 故障排除

### 设备未找到
```bash
# 刷新设备列表
miot device list --refresh

# 检查设备是否在线
miot device list --online
```

### 认证问题
```bash
# 重新获取授权URL
miot system oauth-url

# 使用新授权码认证
miot system auth <新授权码>
```

### 命令未找到
```bash
# 确保 miot 在 PATH 中
export PATH="$HOME/.local/bin:$PATH"

# 或使用完整路径
python3 -m cli.main device list
```

---

## 高级用法

### 管道操作
```bash
# 获取所有在线灯具并关闭
miot device list --online --json | \
  jq -r '.data[] | select(.model | contains("light")) | .did' | \
  xargs -I {} miot device prop set {} 2 1 false
```

### 定时任务（配合 cron）
```bash
# 每天早上7点执行
0 7 * * * /usr/bin/python3 /path/to/skill.py natural_language_control "打开窗帘"
```

---

*更多示例将持续更新...*
