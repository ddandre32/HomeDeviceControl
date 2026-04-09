# -*- coding: utf-8 -*-
"""
小米(MIoT)专属命令
包含: device prop/action/spec/batch, scene, system
"""
import json
import sys
from typing import Optional

import click

from .client import CLIClient, run_async
from .config import CLIConfig
from .formatter import ErrorCode, OutputFormat, print_error, print_success
from .commands_scene import scene_cmd
from .commands_system import system_cmd


def _parse_value(value: str):
    """解析值为合适的数据类型"""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in ("null", "none"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass
    return value


@click.group(name="miot")
@click.pass_context
def miot_cmd(ctx):
    """小米(MIoT)设备管理

    \b
    小米专属命令，包含底层属性/动作控制、场景和系统管理。

    \b
    示例:
      hdc miot device list                       小米设备列表
      hdc miot device prop set <did> 2 1 true    开灯
      hdc miot device action <did> 3 3           音箱暂停
      hdc miot scene list                        场景列表
      hdc miot system status                     系统状态
    """
    ctx.ensure_object(dict)


# ── miot device ──────────────────────────────────────────

@miot_cmd.group(name="device")
@click.pass_context
def miot_device_cmd(ctx):
    """小米设备管理（底层MIoT协议）"""
    ctx.ensure_object(dict)


@miot_device_cmd.command(name="list")
@click.option("--refresh", is_flag=True, help="刷新设备列表")
@click.option("--online", is_flag=True, help="仅在线设备")
@click.option("--room", help="按房间筛选")
@click.option("--home", help="按家庭筛选")
@click.option("--type", "device_type", help="按设备类型筛选")
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_device_list(ctx, refresh, online, room, home, device_type, format_type):
    """列出小米设备"""
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        devices = run_async(client.get_devices(refresh=refresh))
        result = []
        for did, device in devices.items():
            if online and not device.online:
                continue
            if room and device.room_id != room:
                continue
            if home and device.home_id != home:
                continue
            if device_type and device_type.lower() not in device.model.lower():
                continue
            result.append({
                "did": device.did, "name": device.name, "model": device.model,
                "online": device.online, "home_name": device.home_name,
                "room_name": device.room_name, "local_ip": device.local_ip,
            })
        print_success(result, fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.DEVICE_ERROR, format_type=fmt)
    finally:
        run_async(client.close())


@miot_device_cmd.command(name="get")
@click.argument("did")
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_device_get(ctx, did, format_type):
    """获取小米设备详情"""
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        device = run_async(client.get_device(did))
        if device:
            print_success(device.model_dump(), fmt)
        else:
            print_error(message=f"设备未找到: {did}", code=ErrorCode.DEVICE_NOT_FOUND, format_type=fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.DEVICE_ERROR, format_type=fmt)
    finally:
        run_async(client.close())


@miot_device_cmd.command(name="spec")
@click.argument("did")
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_device_spec(ctx, did, format_type):
    """获取设备SPEC"""
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        spec = run_async(client.get_device_spec(did))
        if not spec:
            print_error(message=f"SPEC未找到: {did}", code=ErrorCode.SPEC_NOT_FOUND, format_type=fmt)
            return
        print_success({k: v.model_dump() for k, v in spec.items()}, fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.SPEC_NOT_FOUND, format_type=fmt)
    finally:
        run_async(client.close())


# ── miot device prop ─────────────────────────────────────

@miot_device_cmd.group(name="prop")
@click.pass_context
def miot_prop(ctx):
    """属性读写（MIoT协议）"""
    pass


@miot_prop.command(name="get")
@click.argument("did")
@click.argument("siid", type=int)
@click.argument("piid", type=int)
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_prop_get(ctx, did, siid, piid, format_type):
    """获取属性值

    \b
    参数: DID SIID PIID
    示例: hdc miot device prop get <did> 2 1
    """
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        value = run_async(client.get_property(did, siid, piid))
        print_success({"did": did, "siid": siid, "piid": piid, "value": value}, fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.PROP_GET_ERROR, format_type=fmt)
    finally:
        run_async(client.close())


@miot_prop.command(name="set")
@click.argument("did")
@click.argument("siid", type=int)
@click.argument("piid", type=int)
@click.argument("value")
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_prop_set(ctx, did, siid, piid, value, format_type):
    """设置属性值

    \b
    参数: DID SIID PIID VALUE
    示例:
      hdc miot device prop set <did> 2 1 true    开灯
      hdc miot device prop set <did> 2 2 50      亮度50%
    """
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        result = run_async(client.set_property(did, siid, piid, _parse_value(value)))
        print_success(result, fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.PROP_SET_ERROR, format_type=fmt)
    finally:
        run_async(client.close())


# ── miot device action ───────────────────────────────────

@miot_device_cmd.command(name="action")
@click.argument("did")
@click.argument("siid", type=int)
@click.argument("aiid", type=int)
@click.argument("in_list", nargs=-1)
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_action(ctx, did, siid, aiid, in_list, format_type):
    """执行动作（MIoT协议）

    \b
    参数: DID SIID AIID [参数...]
    示例:
      hdc miot device action <did> 3 3              音箱暂停
      hdc miot device action <did> 7 3 "你好"       语音播报(TTS)
      hdc miot device action <did> 7 4 "播放周杰伦"  执行语音指令
    """
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        result = run_async(client.execute_action(did, siid, aiid,
                                                  [_parse_value(v) for v in in_list]))
        print_success(result, fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.ACTION_ERROR, format_type=fmt)
    finally:
        run_async(client.close())


# ── miot device batch ────────────────────────────────────

@miot_device_cmd.command(name="batch")
@click.option("--file", "file_path", help="批量操作JSON文件路径")
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def miot_batch(ctx, file_path, format_type):
    """批量控制设备

    \b
    JSON格式: [{"type":"set_prop|action","did":"...","siid":N,"piid":N,"value":V}]
    示例: echo '[...]' | hdc miot device batch
    """
    config = ctx.obj["config"]
    client = CLIClient(config)
    fmt = format_type or ctx.obj.get("format", "table")

    if not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                operations = json.load(f)
        else:
            operations = json.load(sys.stdin)

        if not isinstance(operations, list):
            print_error(message="操作列表必须是数组", code=ErrorCode.INVALID_FORMAT, format_type=fmt)
            return

        print_success(run_async(client.batch_control(operations)), fmt)
    except json.JSONDecodeError as e:
        print_error(message=f"JSON解析错误: {e}", code=ErrorCode.INVALID_FORMAT, format_type=fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.DEVICE_ERROR, format_type=fmt)
    finally:
        run_async(client.close())


# ── miot scene / miot system ─────────────────────────────

miot_cmd.add_command(scene_cmd)    # hdc miot scene ...
miot_cmd.add_command(system_cmd)   # hdc miot system ...
