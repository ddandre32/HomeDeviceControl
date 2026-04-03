# -*- coding: utf-8 -*-
"""
海尔设备管理命令
类似于 commands_device.py，但针对海尔设备
"""

import json
import sys
from typing import Optional

import click

from .client import CLIClient, run_async
from .config import CLIConfig
from .formatter import ErrorCode, OutputFormat, print_error, print_success


@click.group(name="haier")
@click.pass_context
def haier_cmd(ctx):
    """海尔设备管理命令"""
    pass


@haier_cmd.command(name="list")
@click.option("--refresh", is_flag=True, help="刷新设备列表")
@click.option("--online", is_flag=True, help="仅显示在线设备")
@click.option("--room", help="按房间筛选")
@click.option("--type", "device_type", help="按设备类型筛选")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_list(ctx, refresh: bool, online: bool, room: Optional[str],
               device_type: Optional[str], format_type: Optional[str]):
    """获取海尔设备列表

    \b
    使用示例:
      home-device haier list                    # 列出所有海尔设备
      home-device haier list --online           # 仅在线设备
      home-device haier list --room 客厅        # 特定房间
      home-device haier list --type light       # 特定类型（如灯）
    """
    config = ctx.obj["config"]
    client = CLIClient(config, channel="haier")
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from channels import get_channel
        haier = get_channel("haier")
        devices = haier.list_devices()

        # 筛选
        result = []
        for device in devices:
            if online and not device.online:
                continue
            if room and device.room != room:
                continue
            if device_type and device_type.lower() not in device.type.lower():
                continue

            result.append({
                "did": device.id,
                "name": device.name,
                "type": device.type,
                "online": device.online,
                "room": device.room,
                "model": device.model,
            })

        print_success(result, fmt)
    except Exception as e:
        print_error(
            error_message=str(e),
            code=ErrorCode.DEVICE_ERROR,
            format_type=fmt
        )
    finally:
        run_async(client.close())


@haier_cmd.command(name="control")
@click.argument("did")
@click.argument("action")
@click.option("--value", help="动作参数值")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_control(ctx, did: str, action: str, value: Optional[str], format_type: Optional[str]):
    """控制海尔设备

    \b
    参数: DID(设备ID) ACTION(动作) [--value VALUE]

    \b
    使用示例:
      home-device haier control <did> turn_on              # 打开设备
      home-device haier control <did> turn_off             # 关闭设备
      home-device haier control <did> set_brightness --value 50  # 设置亮度
      home-device haier control <did> set_temperature --value 24 # 设置温度

    \b
    支持的动作:
      turn_on           - 打开设备
      turn_off          - 关闭设备
      set_brightness    - 设置亮度(0-100)
      set_temperature   - 设置温度(16-31)
      set_mode          - 设置模式
    """
    config = ctx.obj["config"]
    client = CLIClient(config, channel="haier")
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from channels import get_channel
        haier = get_channel("haier")

        # 解析value为合适类型
        parsed_value = _parse_value(value) if value else None

        result = haier.control_device(did, action, parsed_value)
        print_success(result, fmt)
    except Exception as e:
        print_error(
            error_message=str(e),
            code=ErrorCode.DEVICE_ERROR,
            format_type=fmt
        )
    finally:
        run_async(client.close())


@haier_cmd.command(name="status")
@click.argument("did")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_status(ctx, did: str, format_type: Optional[str]):
    """获取海尔设备状态"""
    config = ctx.obj["config"]
    client = CLIClient(config, channel="haier")
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from channels import get_channel
        haier = get_channel("haier")

        device = haier.get_device(did)
        if device:
            result = {
                "did": device.id,
                "name": device.name,
                "type": device.type,
                "online": device.online,
                "room": device.room,
                "model": device.model,
            }
            print_success(result, fmt)
        else:
            print_error(
                error_message=f"设备未找到: {did}",
                code=ErrorCode.DEVICE_NOT_FOUND,
                format_type=fmt
            )
    except Exception as e:
        print_error(
            error_message=str(e),
            code=ErrorCode.DEVICE_ERROR,
            format_type=fmt
        )
    finally:
        run_async(client.close())


@haier_cmd.command(name="auth")
@click.option("--username", prompt=True, help="海尔账号")
@click.option("--password", prompt=True, hide_input=True, help="密码")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_auth(ctx, username: str, password: str, format_type: Optional[str]):
    """海尔设备认证"""
    config = ctx.obj["config"]
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from haier import HaierClient
        from channels.haier import HaierChannel

        client = HaierClient()
        success = run_async(client.authenticate(username, password))

        if success:
            print_success(
                {"message": "认证成功", "username": username},
                fmt
            )
        else:
            print_error(
                error_message="认证失败",
                code=ErrorCode.AUTH_FAILED,
                format_type=fmt
            )
    except Exception as e:
        print_error(
            error_message=str(e),
            code=ErrorCode.AUTH_FAILED,
            format_type=fmt
        )


def _parse_value(value: str):
    """解析值为合适的数据类型"""
    if value is None:
        return None

    # 尝试布尔值
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() == "null" or value.lower() == "none":
        return None

    # 尝试整数
    try:
        return int(value)
    except ValueError:
        pass

    # 尝试浮点数
    try:
        return float(value)
    except ValueError:
        pass

    # 尝试JSON解析
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    # 返回字符串
    return value
