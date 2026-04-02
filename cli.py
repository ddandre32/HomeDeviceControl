#!/usr/bin/env python3
"""
Home Device Control CLI - 命令行入口
提供原子操作，符合 OpenClaw 技能设计规范
"""

import sys
import json
import argparse

from channels import get_channel, list_channels


class GlobalArgs:
    """全局参数容器"""
    json_output = False
    dry_run = False
    yes = False
    quiet = False
    channel = "xiaomi"


def format_table(data, headers):
    """格式化表格输出"""
    if not data:
        return "无数据"
    
    # 计算列宽
    col_widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 构建表格
    lines = []
    
    # 表头
    header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_row)
    lines.append("-" * len(header_row))
    
    # 数据行
    for row in data:
        lines.append(" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))
    
    return "\n".join(lines)


def output_result(result, human_formatter=None):
    """统一输出处理"""
    if GlobalArgs.quiet:
        # 静默模式：只输出成功/失败
        print("success" if result.get("success") else "failed")
        return
    
    if GlobalArgs.json_output:
        # JSON 模式
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif human_formatter:
        # 人类可读格式
        print(human_formatter(result))
    else:
        # 默认 JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))


def confirm_action(action_desc):
    """确认操作"""
    if GlobalArgs.dry_run:
        print(f"[预览模式] 将执行: {action_desc}")
        return False
    
    if GlobalArgs.yes:
        return True
    
    try:
        response = input(f"确认 {action_desc}? [y/N]: ")
        return response.lower() in ('y', 'yes')
    except EOFError:
        # 非交互式环境，默认不执行
        print("非交互式环境，使用 --yes 自动确认")
        return False


def cmd_list_devices(args):
    """列出设备"""
    try:
        channel = get_channel(GlobalArgs.channel)
        devices = channel.list_devices()
    except Exception as e:
        result = {"success": False, "error": str(e), "count": 0, "devices": []}
        output_result(result)
        return 1
    
    result = {
        "success": True,
        "count": len(devices),
        "devices": [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "brand": d.brand,
                "room": d.room,
                "online": d.online
            }
            for d in devices
        ]
    }
    
    def human_format(r):
        if r["count"] == 0:
            return "未发现设备"
        
        data = [[d["id"], d["name"], d["type"], d["room"], "在线" if d["online"] else "离线"]
                for d in r["devices"]]
        return format_table(data, ["ID", "名称", "类型", "房间", "状态"])
    
    output_result(result, human_format)
    return 0


def cmd_control_device(args):
    """控制设备"""
    action_desc = f"{args.action} 设备 {args.device_id}"
    if args.value:
        action_desc += f" (值: {args.value})"
    
    if not confirm_action(action_desc):
        if GlobalArgs.dry_run:
            return 0
        print("操作已取消")
        return 1
    
    try:
        channel = get_channel(GlobalArgs.channel)
        result = channel.control_device(args.device_id, args.action, args.value)
    except Exception as e:
        result = {"success": False, "error": str(e)}
    
    def human_format(r):
        if r.get("success"):
            return f"✅ 操作成功: {action_desc}"
        else:
            return f"❌ 操作失败: {r.get('error', '未知错误')}"
    
    output_result(result, human_format)
    return 0 if result.get("success") else 1


def cmd_list_scenes(args):
    """列出场景"""
    try:
        channel = get_channel(GlobalArgs.channel)
        scenes = channel.list_scenes()
    except Exception as e:
        result = {"success": False, "error": str(e), "count": 0, "scenes": []}
        output_result(result)
        return 1
    
    result = {
        "success": True,
        "count": len(scenes),
        "scenes": [
            {"id": s.id, "name": s.name, "enabled": s.enabled}
            for s in scenes
        ]
    }
    
    def human_format(r):
        if r["count"] == 0:
            return "未发现场景"
        
        data = [[s["id"], s["name"], "启用" if s["enabled"] else "禁用"]
                for s in r["scenes"]]
        return format_table(data, ["ID", "名称", "状态"])
    
    output_result(result, human_format)
    return 0


def cmd_execute_scene(args):
    """执行场景"""
    action_desc = f"执行场景 {args.scene_id}"
    
    if not confirm_action(action_desc):
        if GlobalArgs.dry_run:
            return 0
        print("操作已取消")
        return 1
    
    try:
        channel = get_channel(GlobalArgs.channel)
        result = channel.execute_scene(args.scene_id)
    except Exception as e:
        result = {"success": False, "error": str(e)}
    
    def human_format(r):
        if r.get("success"):
            return f"✅ 场景执行成功: {args.scene_id}"
        else:
            return f"❌ 场景执行失败: {r.get('error', '未知错误')}"
    
    output_result(result, human_format)
    return 0 if result.get("success") else 1


def cmd_check(args):
    """检查渠道状态"""
    try:
        channels = list_channels()
    except Exception as e:
        result = {"success": False, "error": str(e), "channels": {}}
        output_result(result)
        return 1
    
    result = {
        "success": True,
        "channels": {}
    }
    
    for name, status in channels.items():
        result["channels"][name] = {
            "available": status.available,
            "configured": status.configured,
            "message": status.message,
            "suggestion": status.suggestion
        }
    
    def human_format(r):
        lines = ["渠道状态检查:"]
        for name, info in r["channels"].items():
            status = "✅" if info["available"] else "❌"
            lines.append(f"\n{status} {name}")
            lines.append(f"   配置状态: {'已配置' if info['configured'] else '未配置'}")
            lines.append(f"   消息: {info['message']}")
            if info["suggestion"]:
                lines.append(f"   建议: {info['suggestion']}")
        return "\n".join(lines)
    
    output_result(result, human_format)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Home Device Control - 小米智能家居控制",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  home-device list-devices
  home-device control light_001 turn_on
  home-device control light_001 set_brightness --value 50
  home-device execute-scene scene_001 --dry-run
  home-device control device_001 turn_off --yes --quiet
        """
    )
    
    # 全局选项
    parser.add_argument("--json", action="store_true", dest="json_output",
                       help="JSON 格式输出")
    parser.add_argument("--dry-run", action="store_true",
                       help="预览模式，不实际执行")
    parser.add_argument("--yes", action="store_true",
                       help="自动确认，跳过提示")
    parser.add_argument("--quiet", action="store_true",
                       help="静默模式")
    parser.add_argument("--channel", default="xiaomi",
                       help="渠道名称 (默认: xiaomi)")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # list-devices
    p_list = subparsers.add_parser("list-devices", help="列出设备")
    
    # control
    p_control = subparsers.add_parser("control", help="控制设备")
    p_control.add_argument("device_id", help="设备ID")
    p_control.add_argument("action", 
                          choices=["turn_on", "turn_off", "set_brightness", "set_temperature",
                                   "speaker_pause", "speaker_next", "speaker_previous",
                                   "voice_command"],
                          help="动作")
    p_control.add_argument("--value", help="参数值")
    
    # list-scenes
    p_scenes = subparsers.add_parser("list-scenes", help="列出场景")
    
    # execute-scene
    p_exec = subparsers.add_parser("execute-scene", help="执行场景")
    p_exec.add_argument("scene_id", help="场景ID")
    
    # check
    p_check = subparsers.add_parser("check", help="检查渠道状态")
    
    args = parser.parse_args()
    
    # 保存全局参数
    GlobalArgs.json_output = args.json_output
    GlobalArgs.dry_run = args.dry_run
    GlobalArgs.yes = args.yes
    GlobalArgs.quiet = args.quiet
    GlobalArgs.channel = args.channel
    
    if args.command == "list-devices":
        return cmd_list_devices(args)
    elif args.command == "control":
        return cmd_control_device(args)
    elif args.command == "list-scenes":
        return cmd_list_scenes(args)
    elif args.command == "execute-scene":
        return cmd_execute_scene(args)
    elif args.command == "check":
        return cmd_check(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())