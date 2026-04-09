# -*- coding: utf-8 -*-
"""
统一设备管理命令（跨品牌）
仅提供跨品牌聚合查询，控制操作由品牌专属命令完成
"""
from typing import Optional

import click

from .client import CLIClient, run_async
from .formatter import ErrorCode, print_error, print_success


@click.group(name="device")
@click.pass_context
def device_cmd(ctx):
    """统一设备管理（跨品牌）

    \b
    聚合查询所有品牌设备，使用 --brand 筛选。
    控制设备请使用品牌专属命令:
      hdc miot device prop set ...    小米设备
      hdc haier control ...           海尔设备
    """
    ctx.ensure_object(dict)


@device_cmd.command(name="list")
@click.option("--brand", type=click.Choice(["xiaomi", "haier", "all"]), default="all",
              help="品牌筛选 (默认: all)")
@click.option("--online", is_flag=True, help="仅在线设备")
@click.option("--room", help="按房间筛选")
@click.option("--home", help="按家庭筛选")
@click.option("--type", "device_type", help="按设备类型筛选")
@click.option("--refresh", is_flag=True, help="刷新设备列表")
@click.option("-f", "--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]))
@click.pass_context
def device_list(ctx, brand: str, online: bool, room: Optional[str],
                home: Optional[str], device_type: Optional[str],
                refresh: bool, format_type: Optional[str]):
    """列出设备（跨品牌聚合）

    \b
    示例:
      hdc device list                          所有品牌
      hdc device list --brand xiaomi --online  小米在线设备
      hdc device list --brand haier            海尔设备
      hdc --json device list | jq '.data[]'    JSON管道
    """
    config = ctx.obj["config"]
    fmt = format_type or ctx.obj.get("format", "table")

    if brand == "xiaomi" and not config.is_authenticated:
        print_error(code=ErrorCode.NOT_AUTHENTICATED, format_type=fmt)
        return

    try:
        result = []

        if brand in ("xiaomi", "all") and config.is_authenticated:
            client = CLIClient(config)
            try:
                devices = run_async(client.get_devices(refresh=refresh))
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
                        "did": device.did, "name": device.name,
                        "model": device.model, "brand": "xiaomi",
                        "online": device.online, "home_name": device.home_name,
                        "room_name": device.room_name,
                    })
            finally:
                run_async(client.close())

        if brand in ("haier", "all"):
            try:
                from channels import get_channel
                for d in get_channel("haier").list_devices():
                    if online and not d.online:
                        continue
                    if room and d.room != room:
                        continue
                    if device_type and device_type.lower() not in d.type.lower():
                        continue
                    result.append({
                        "did": d.id, "name": d.name,
                        "model": d.model, "brand": "haier",
                        "online": d.online, "home_name": None,
                        "room_name": d.room,
                    })
            except Exception:
                pass

        print_success(result, fmt)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.DEVICE_ERROR, format_type=fmt)
