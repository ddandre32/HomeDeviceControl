# Smart Home Skill 设计哲学重构

> 基于对 Skill 边界和 AI 能力的深度思考

---

## 🎯 核心洞察

### 洞察 1: Skill 应该做"工具"，不做"智能"

**❌ 错误理解**:
- Skill 封装所有业务逻辑
- Skill 实现自然语言理解
- Skill 预置所有功能场景

**✅ 正确理解**:
- Skill 提供**工具能力**（调用设备、查询状态）
- **大模型/Agent** 负责智能（理解意图、规划任务）
- Skill 是**能力的暴露层**，不是**智能的实现层**

```
❌ 旧架构 (Skill 做智能)
用户 → "用灯光发摩斯密码 SOS"
      ↓
    Skill.nlp_parse() → 识别摩斯意图
      ↓
    Skill.morse_encode() → 编码
      ↓
    Skill.execute_morse() → 执行开关序列

✅ 新架构 (Skill 只提供工具)
用户 → "用灯光发摩斯密码 SOS"
      ↓
    Agent 理解意图：需要用灯光发送摩斯密码
      ↓
    Agent 规划任务：
      1. 获取摩斯编码表
      2. 将 SOS 转为 ... --- ...
      3. 通过 Skill 控制灯光开关
      ↓
    Skill.control_device(on) → 开灯
    Skill.control_device(off) → 关灯
    ... (Agent 自行控制时序)
```

---

## 🔧 Skill 的正确边界

### Skill 应该做的 (工具层)

| 功能 | 说明 | 示例 |
|------|------|------|
| **设备发现** | 列出所有设备及其属性 | `miot device list` |
| **设备控制** | 开关、调节等原子操作 | `miot device prop set <id> on` |
| **状态查询** | 获取设备当前状态 | `miot device get <id>` |
| **场景执行** | 执行预定义场景 | `miot scene run <id>` |
| **渠道管理** | 多品牌渠道的统一接口 | `channels/xiaomi.py` |

### Skill 不应该做的 (智能层)

| 功能 | 原因 | 应该由谁做 |
|------|------|-----------|
| **自然语言解析** | 大模型本身就具备 | Agent/LLM |
| **意图识别** | 大模型更擅长理解上下文 | Agent/LLM |
| **任务规划** | 需要推理和决策能力 | Agent/LLM |
| **摩斯密码编码** | 是算法不是工具 | Agent/LLM 实时计算 |
| **延时控制逻辑** | 是调度策略不是工具 | Agent/LLM 规划执行 |
| **模糊匹配** | 大模型语义理解更强 | Agent/LLM |

---

## 🏗️ 重构后的极简架构

### 核心原则: Skill = 设备控制 CLI 的封装

```
smart-home/
├── SKILL.md              # 极简：只告诉 Agent 有哪些工具命令
├── skill.json            # OpenClaw 工具定义 (可选)
├── channels/             # 多品牌渠道封装
│   ├── base.py          # 抽象接口
│   ├── xiaomi.py        # miot CLI 封装
│   └── haier.py         # haier-cli 封装 (预留)
└── doctor.py            # 诊断工具
```

### 极简 SKILL.md 示例

```markdown
# Smart Home Skill

通过 CLI 控制智能家居设备。

## 支持的渠道

| 渠道 | CLI 命令 | 状态 |
|------|---------|------|
| 小米 | `miot` | 需配置 |
| 海尔 | `haier-cli` | 预留 |

## 核心命令

```bash
# 列出设备
miot device list

# 控制设备
miot device prop set <device_id> <siid> <piid> <value>

# 执行场景
miot scene run <scene_id>
```

## 配置

```bash
# 小米认证
miot system oauth-url
miot system auth <code>
```

## 说明

- 本 Skill 只提供设备控制能力
- 复杂任务（如摩斯密码、延时控制）由 Agent 自行规划执行
- Agent 直接调用上述 CLI 命令即可
```

---

## 🧠 Agent 的能力边界

### Agent 应该做的 (智能层)

```python
# 示例：Agent 如何处理"用灯光发摩斯密码"

class Agent:
    def handle_user_request(self, text: str):
        # 1. 理解意图
        intent = self.llm_understand(text)
        # → {action: "send_morse", device: "灯", message: "SOS"}
        
        # 2. 规划任务
        plan = self.llm_plan(intent)
        # → [
        #   {action: "get_morse_table"},
        #   {action: "encode", text: "SOS"},
        #   {action: "find_device", name: "灯"},
        #   {action: "send_morse", pattern: "... --- ..."}
        # ]
        
        # 3. 执行 (调用 Skill 提供的工具)
        for step in plan:
            if step.action == "find_device":
                device = self.exec("miot device list | grep 灯")
            elif step.action == "control":
                self.exec(f"miot device prop set {device.id} 2 1 true")  # 开
                time.sleep(0.2)
                self.exec(f"miot device prop set {device.id} 2 1 false") # 关
```

### 关键认知

| 能力 | Skill | Agent/LLM |
|------|-------|-----------|
| 设备开关 | ✅ | ❌ |
| 摩斯编码 | ❌ | ✅ |
| 延时调度 | ❌ | ✅ |
| 意图理解 | ❌ | ✅ |
| 任务规划 | ❌ | ✅ |
| 模糊匹配 | ❌ | ✅ (语义理解) |

---

## 🔄 对比：重构前后的设计

### 重构前 (Skill 做智能)

```python
# skill.py (600+ 行)
class XiaomiDeviceControlSkill:
    def natural_language_control(self, command):
        # NLP 解析
        # 意图识别
        # 设备匹配
        # 执行控制
        pass
    
    def send_morse_code(self, message):
        # 摩斯编码
        # 时序控制
        # 批量执行
        pass
    
    def create_delayed_action(self, delay, action):
        # 延迟调度
        pass
```

**问题**:
- Skill 越俎代庖，做了 Agent 该做的事
- 功能臃肿，难以穷举所有场景
- 限制了 Agent 的灵活性

### 重构后 (Skill 只做工具)

```python
# channels/xiaomi.py (100+ 行)
class XiaomiChannel:
    def list_devices(self):
        return exec("miot device list")
    
    def control_device(self, device_id, action, value=None):
        return exec(f"miot device prop set {device_id} ...")
```

**优势**:
- Skill 极简，只做设备控制
- Agent 灵活，可以创造无限场景
- 符合"脚手架"设计原则

---

## 🎯 新设计规范

### 规范 1: 原子化工具

**原则**: Skill 只提供**原子操作**，不提供**组合功能**

```
✅ 原子操作 (Skill 提供)
- 开灯 / 关灯
- 设置亮度
- 查询设备状态

❌ 组合功能 (Agent 自行实现)
- 摩斯密码 (开灯+关灯+时序)
- 延时控制 (等待+执行)
- 批量控制 (循环+控制)
```

### 规范 2: 零智能封装

**原则**: Skill 不做任何需要"理解"或"决策"的封装

```
❌ 不做:
- 自然语言解析
- 设备模糊匹配
- 意图识别
- 任务规划

✅ 只做:
- CLI 命令封装
- 参数格式化
- 错误码转换
- 多品牌路由
```

### 规范 3: 能力暴露而非能力实现

**原则**: Skill 暴露**能做什么**，不实现**怎么做**

```
❌ 旧设计:
Skill.send_morse_code("SOS")
→ Skill 内部实现编码、时序、执行

✅ 新设计:
Skill.control_device(device_id, "turn_on")
Skill.control_device(device_id, "turn_off")
→ Agent 自行决定何时开关、持续多久
```

---

## 📋 重构检查清单

### 删除的功能

- [ ] `natural_language_control()` → 由 Agent 直接理解
- [ ] `send_morse_code()` → Agent 用原子操作自行实现
- [ ] `create_delayed_action()` → Agent 自行调度
- [ ] `_find_device_by_name()` → Agent 用语义理解匹配
- [ ] `_parse_control_command()` → Agent 直接解析

### 保留的功能

- [ ] `list_devices()` → 原子查询
- [ ] `control_device()` → 原子控制
- [ ] `list_scenes()` → 原子查询
- [ ] `execute_scene()` → 原子执行
- [ ] `doctor()` → 诊断工具

### 新增的功能

- [ ] `channels/base.py` → 多品牌抽象
- [ ] `channels/xiaomi.py` → 小米渠道
- [ ] `channels/haier.py` → 海尔渠道 (预留)

---

## 💡 示例：新架构下的场景实现

### 场景 1: 摩斯密码

**用户**: "用灯光发摩斯密码 SOS"

**Agent 思考**:
```
1. 用户想用灯光发送摩斯密码
2. 我需要：
   - 找到灯光设备
   - 将 SOS 转为摩斯码 ... --- ...
   - 控制灯光按节奏开关
3. 执行：
   - miot device list → 找到"台灯"
   - 计算摩斯编码
   - for pattern in "... --- ...":
       if '.': 开灯 0.2s, 关灯 0.2s
       if '-': 开灯 0.6s, 关灯 0.2s
```

**Agent 调用 Skill**:
```bash
miot device list
miot device prop set <id> 2 1 true   # 开
miot device prop set <id> 2 1 false  # 关
# ... 自行控制时序
```

### 场景 2: 延时控制

**用户**: "5秒后关灯"

**Agent 思考**:
```
1. 用户想延时关灯
2. 我需要：
   - 等待 5 秒
   - 然后关灯
3. 执行：
   - time.sleep(5)
   - miot device prop set <id> 2 1 false
```

**Agent 调用 Skill**:
```bash
# (等待 5 秒后)
miot device prop set <id> 2 1 false
```

### 场景 3: 模糊匹配

**用户**: "把客厅的灯打开"

**Agent 思考**:
```
1. 用户想打开客厅的灯
2. 我需要找到"客厅的灯"这个设备
3. 执行：
   - miot device list → 获取所有设备
   - 语义匹配：哪个设备最可能是"客厅的灯"？
   - miot device prop set <匹配到的id> 2 1 true
```

**Agent 调用 Skill**:
```bash
miot device list
# (Agent 自行语义匹配)
miot device prop set light_001 2 1 true
```

---

## 🎓 设计哲学总结

### 核心公式

```
完整的智能家居能力 = Skill(工具层) + Agent(智能层)

Skill = 设备控制的原子能力
Agent = 理解、规划、组合这些能力
```

### 类比

| 类比 | Skill | Agent |
|------|-------|-------|
**操作系统** | 系统调用 (open/read/write) | 应用程序 |
**乐高** | 基础积木块 | 搭建说明书 |
**厨房** | 刀具、锅具 | 厨师 |

### 黄金法则

> **如果大模型能做的事，就不要让 Skill 做。**
> 
> **Skill 只做"大模型做不了或做不好的事"。**

大模型做不了的事：
- 实际控制硬件设备
- 访问本地 CLI 工具
- 与物理世界交互

大模型能做的事：
- 理解自然语言
- 规划任务步骤
- 编码摩斯密码
- 计算延时逻辑
- 语义匹配设备

---

## ✅ 重构后的优势

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| **代码量** | 600+ 行 | <200 行 |
| **维护成本** | 高 | 极低 |
| **扩展性** | 差 | 极强 |
| **灵活性** | 受限 | 无限 |
| **场景覆盖** | 预置有限 | 任意创造 |
| **符合规范** | ❌ | ✅ |

---

*设计哲学重构完成*
*时间: 2026-04-01 08:55*
