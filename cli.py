#!/usr/bin/env python3
"""
Home Device Control CLI - 命令行入口
提供原子操作，不做智能封装
"""

import sys
import json
import argparse

from channels import get_channel, list_channels


def cmd_list_devices(args):
    """列出设备"""
    channel = get_channel(args.channel or "xiaomi")
    devices = channel.list_devices()
    
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
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_control_device(args):
    """控制设备"""
    channel = get_channel(args.channel or "xiaomi")
    result = channel.control_device(args.device_id, args.action, args.value)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success") else 1


def cmd_list_scenes(args):
    """列出场景"""
    channel = get_channel(args.channel or "xiaomi")
    scenes = channel.list_scenes()
    
    result = {
        "success": True,
        "count": len(scenes),
        "scenes": [
            {"id": s.id, "name": s.name, "enabled": s.enabled}
            for s in scenes
        ]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_execute_scene(args):
    """执行场景"""
    channel = get_channel(args.channel or "xiaomi")
    result = channel.execute_scene(args.scene_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success") else 1


def cmd_check(args):
    """检查渠道状态"""
    channels = list_channels()
    
    result = {}
    for name, status in channels.items():
        result[name] = {
            "available": status.available,
            "configured": status.configured,
            "message": status.message,
            "suggestion": status.suggestion
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Smart Home CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # list-devices
    p_list = subparsers.add_parser("list-devices", help="列出设备")
    p_list.add_argument("--channel", help="渠道名称")
    
    # control
    p_control = subparsers.add_parser("control", help="控制设备")
    p_control.add_argument("device_id", help="设备ID")
    p_control.add_argument("action", choices=["turn_on", "turn_off", "set_brightness", "set_temperature"])
    p_control.add_argument("--value", help="参数值")
    p_control.add_argument("--channel", help="渠道名称")
    
    # list-scenes
    p_scenes = subparsers.add_parser("list-scenes", help="列出场景")
    p_scenes.add_argument("--channel", help="渠道名称")
    
    # execute-scene
    p_exec = subparsers.add_parser("execute-scene", help="执行场景")
    p_exec.add_argument("scene_id", help="场景ID")
    p_exec.add_argument("--channel", help="渠道名称")
    
    # check
    p_check = subparsers.add_parser("check", help="检查渠道状态")
    
    args = parser.parse_args()
    
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
