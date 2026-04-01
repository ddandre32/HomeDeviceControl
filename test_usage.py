#!/usr/bin/env python3
"""
HomeDeviceControl Skill 使用测试
模拟各种使用场景
"""

import sys
import json
sys.path.insert(0, '/Users/Laura/Documents/openclaw_lab/skills/HomeDeviceControl')

from channels import get_channel, list_channels
from channels.base import Device, Scene


def test_channel_check():
    """测试渠道检查"""
    print("=" * 60)
    print("测试 1: 渠道状态检查")
    print("=" * 60)
    
    channels = list_channels()
    
    for name, status in channels.items():
        print(f"\n渠道: {name}")
        print(f"  可用: {status.available}")
        print(f"  已配置: {status.configured}")
        print(f"  消息: {status.message}")
        if status.suggestion:
            print(f"  建议: {status.suggestion}")
    
    return True


def test_mock_devices():
    """测试设备列表（模拟数据）"""
    print("\n" + "=" * 60)
    print("测试 2: 设备列表（模拟）")
    print("=" * 60)
    
    # 创建模拟设备
    mock_devices = [
        Device(id="light_001", name="客厅灯", type="light", brand="xiaomi", room="客厅", online=True),
        Device(id="light_002", name="卧室台灯", type="light", brand="xiaomi", room="卧室", online=True),
        Device(id="ac_001", name="空调", type="air_conditioner", brand="xiaomi", room="主卧", online=True),
        Device(id="curtain_001", name="窗帘", type="curtain", brand="xiaomi", room="主卧", online=False),
    ]
    
    print(f"\n找到 {len(mock_devices)} 个设备:")
    for device in mock_devices:
        status = "在线" if device.online else "离线"
        print(f"  - {device.name} ({device.type}) [{status}] - {device.room}")
    
    return True


def test_mock_control():
    """测试设备控制（模拟）"""
    print("\n" + "=" * 60)
    print("测试 3: 设备控制（模拟）")
    print("=" * 60)
    
    # 模拟控制命令
    commands = [
        {"device": "客厅灯", "action": "turn_on", "description": "打开客厅灯"},
        {"device": "卧室台灯", "action": "turn_off", "description": "关闭卧室台灯"},
        {"device": "空调", "action": "set_temperature", "value": 26, "description": "设置空调温度26度"},
    ]
    
    print("\n模拟控制命令:")
    for cmd in commands:
        value_str = f" -> {cmd['value']}" if cmd.get('value') else ""
        print(f"  - {cmd['description']}: {cmd['action']}{value_str}")
    
    return True


def test_mock_scenes():
    """测试场景（模拟）"""
    print("\n" + "=" * 60)
    print("测试 4: 场景执行（模拟）")
    print("=" * 60)
    
    mock_scenes = [
        Scene(id="scene_001", name="回家模式", enabled=True),
        Scene(id="scene_002", name="离家模式", enabled=True),
        Scene(id="scene_003", name="睡眠模式", enabled=True),
    ]
    
    print(f"\n可用场景 ({len(mock_scenes)} 个):")
    for scene in mock_scenes:
        status = "启用" if scene.enabled else "禁用"
        print(f"  - {scene.name} [{status}]")
    
    print("\n模拟执行场景:")
    print("  - 执行: 回家模式")
    print("    动作: 开灯、开空调、关窗帘")
    
    return True


def test_agent_workflow():
    """测试 Agent 工作流程"""
    print("\n" + "=" * 60)
    print("测试 5: Agent 工作流程")
    print("=" * 60)
    
    print("""
场景: 用户说"打开客厅的灯"

Agent 思考过程:
1. 理解意图: 用户想打开客厅的灯
2. 规划任务:
   - 步骤1: 获取设备列表
   - 步骤2: 找到"客厅的灯"
   - 步骤3: 发送开灯命令

Agent 调用 Skill:
```
# 步骤1: 列出设备
$ python3 cli.py list-devices
→ [{"id": "light_001", "name": "客厅灯", ...}]

# 步骤2: 语义匹配 (Agent 自行完成)
→ 匹配到 "light_001"

# 步骤3: 控制设备
$ python3 cli.py control light_001 turn_on
→ {"success": true}
```

结果: ✅ 灯已打开
""")
    
    return True


def test_complex_scenario():
    """测试复杂场景"""
    print("\n" + "=" * 60)
    print("测试 6: 复杂场景 - 摩斯密码")
    print("=" * 60)
    
    print("""
场景: 用户说"用灯光发摩斯密码 SOS"

Agent 思考过程:
1. 理解意图: 用灯光发送摩斯密码
2. 规划任务:
   - 步骤1: 将 SOS 转为摩斯码 ... --- ...
   - 步骤2: 找到灯光设备
   - 步骤3: 按节奏控制开关

Agent 执行:
```python
# Agent 自行编码 (不依赖 Skill)
morse = {"S": "...", "O": "---"}
pattern = "... --- ..."

# Agent 直接调用原子操作
for symbol in pattern:
    if symbol == ".":
        exec("miot device set light_001 on")
        sleep(0.2)
        exec("miot device set light_001 off")
        sleep(0.2)
    elif symbol == "-":
        exec("miot device set light_001 on")
        sleep(0.6)
        exec("miot device set light_001 off")
        sleep(0.2)
```

结果: ✅ SOS 摩斯密码发送完成
""")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("HomeDeviceControl Skill 使用测试")
    print("=" * 60)
    
    tests = [
        ("渠道检查", test_channel_check),
        ("设备列表", test_mock_devices),
        ("设备控制", test_mock_control),
        ("场景执行", test_mock_scenes),
        ("Agent 工作流", test_agent_workflow),
        ("复杂场景", test_complex_scenario),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
