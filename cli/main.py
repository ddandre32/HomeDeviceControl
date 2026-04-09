# -*- coding: utf-8 -*-
"""
Home Device Control CLI 主入口

命令结构:
  hdc device list/control/get     统一设备管理（跨品牌）
  hdc miot ...                    小米专属命令（prop/action/spec/scene/system）
  hdc haier ...                   海尔专属命令（auth/tools/status）
"""
import sys
import os
from typing import Optional

import click

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import __version__
from .commands_device import device_cmd
from .commands_miot import miot_cmd
from .commands_haier import haier_cmd
from .config import CLIConfig
from .formatter import ErrorCode, OutputFormat, get_default_format, is_tty, print_error


@click.group()
@click.version_option(version=__version__, prog_name="hdc")
@click.option("--config", "config_path", default=None,
              help="配置文件路径 (也可用 HDC_CONFIG_PATH 环境变量)")
@click.option("--format", "format_type", default=None,
              type=click.Choice(["json", "yaml", "table", "human"]),
              help="输出格式 (默认根据环境自动选择)")
@click.option("--json", "json_mode", is_flag=True,
              help="JSON输出 (等同 --format=json)")
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.pass_context
def cli(ctx, config_path: Optional[str], format_type: Optional[str],
        json_mode: bool, verbose: bool):
    """Home Device Control - 智能家居命令行控制

    \b
    统一查询（跨品牌）:
      hdc device list                          列出所有设备
      hdc device list --brand xiaomi           仅小米设备

    \b
    小米专属 (hdc miot):
      hdc miot device prop set <did> 2 1 true  开灯
      hdc miot device action <did> 3 3         音箱暂停
      hdc miot scene list / run <id>           场景管理
      hdc miot system auth / status            系统管理

    \b
    海尔专属 (hdc haier):
      hdc haier control <did> turn_on          控制设备
      hdc haier list                           设备列表
      hdc haier auth                           初始化MCP连接

    \b
    环境变量:
      HDC_CONFIG_PATH     配置文件路径
      MIOT_CLOUD_SERVER   小米云服务器(cn/sg/us)
      MIOT_FORMAT         默认输出格式
      MIOT_ACCESS_TOKEN   小米访问令牌
    """
    ctx.ensure_object(dict)
    config = CLIConfig(config_path)

    if json_mode:
        final_format = "json"
    elif format_type:
        final_format = format_type
    elif config.get_default_format():
        final_format = config.get_default_format()
    else:
        final_format = get_default_format()

    ctx.obj["config"] = config
    ctx.obj["format"] = final_format
    ctx.obj["verbose"] = verbose
    ctx.obj["is_tty"] = is_tty()


# 注册子命令
cli.add_command(device_cmd)    # hdc device ...  (统一跨品牌)
cli.add_command(miot_cmd)      # hdc miot ...    (小米专属)
cli.add_command(haier_cmd)     # hdc haier ...   (海尔专属)


def main():
    """CLI入口点"""
    try:
        cli()
    except KeyboardInterrupt:
        print_error(message="操作被用户中断", code=ErrorCode.INTERRUPTED,
                    format_type=OutputFormat.JSON)
        sys.exit(130)
    except Exception as e:
        print_error(message=str(e), code=ErrorCode.UNKNOWN_ERROR,
                    format_type=OutputFormat.JSON)
        sys.exit(1)


if __name__ == "__main__":
    main()
