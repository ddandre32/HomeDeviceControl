# -*- coding: utf-8 -*-
"""
海尔设备管理命令 - MCP协议版本
使用MCP (Model Context Protocol) 协议通过SSE传输层与海尔U+平台通信
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
    """海尔设备管理命令 (MCP协议)"""
    pass


@haier_cmd.command(name="list")
@click.option("--online", is_flag=True, help="仅显示在线设备")
@click.option("--room", help="按房间筛选")
@click.option("--type", "device_type", help="按设备类型筛选")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_list(ctx, online: bool, room: Optional[str],
               device_type: Optional[str], format_type: Optional[str]):
    """获取海尔设备列表 (通过MCP协议)

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
            message=str(e),
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
    """控制海尔设备 (通过MCP协议)

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
      turn_on           - 打开设备 (调用lampControl)
      turn_off          - 关闭设备 (调用lampControl)
      set_brightness    - 设置亮度(0-100)
      set_temperature   - 设置温度(16-31)
      curtain_control   - 窗帘控制
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
            message=str(e),
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
    """获取海尔设备状态 (通过MCP协议)"""
    config = ctx.obj["config"]
    client = CLIClient(config, channel="haier")
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from channels import get_channel
        from haier import HaierClient

        haier_channel = get_channel("haier")
        haier_client = HaierClient()

        async def _get_status():
            async with haier_client:
                status = await haier_client.get_device_status([did])
                return status

        status = run_async(_get_status())

        device = haier_channel.get_device(did)
        if device:
            result = {
                "did": device.id,
                "name": device.name,
                "type": device.type,
                "online": device.online,
                "room": device.room,
                "model": device.model,
                "status": status,
            }
            print_success(result, fmt)
        else:
            print_error(
                message=f"设备未找到: {did}",
                code=ErrorCode.DEVICE_NOT_FOUND,
                format_type=fmt
            )
    except Exception as e:
        print_error(
            message=str(e),
            code=ErrorCode.DEVICE_ERROR,
            format_type=fmt
        )
    finally:
        run_async(client.close())


@haier_cmd.command(name="auth")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_auth(ctx, format_type: Optional[str]):
    """初始化海尔MCP连接

    \b
    MCP协议通过SSE传输层通信，无需用户名密码认证。
    初始化过程会自动：
      1. 建立SSE连接
      2. 发送initialize握手
      3. 启动自动重连和心跳机制

    \b
    使用示例:
      home-device haier auth
    """
    config = ctx.obj["config"]
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from haier import HaierClient

        client = HaierClient()
        success = run_async(client.initialize())

        if success:
            # 获取可用工具列表
            tools = run_async(client.get_tools())
            tool_names = [tool.name for tool in tools]

            print_success(
                {
                    "message": "MCP连接初始化成功",
                    "server_info": client._connection_info.server_info,
                    "available_tools": tool_names,
                },
                fmt
            )
        else:
            print_error(
                message="MCP连接初始化失败",
                code=ErrorCode.AUTH_FAILED,
                format_type=fmt
            )
    except Exception as e:
        print_error(
            message=str(e),
            code=ErrorCode.AUTH_FAILED,
            format_type=fmt
        )


@haier_cmd.command(name="tools")
@click.option("-f", "--format", "format_type", default=None, type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def haier_tools(ctx, format_type: Optional[str]):
    """列出可用的MCP工具

    \b
    使用示例:
      home-device haier tools
    """
    config = ctx.obj["config"]
    fmt = format_type or ctx.obj.get("format", "table")

    try:
        from haier import HaierClient

        client = HaierClient()

        async def _get_tools():
            async with client:
                tools = await client.get_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                    for tool in tools
                ]

        tools = run_async(_get_tools())
        print_success(tools, fmt)

    except Exception as e:
        print_error(
            message=str(e),
            code=ErrorCode.DEVICE_ERROR,
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
