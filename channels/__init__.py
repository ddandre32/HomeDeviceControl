"""
Smart Home Channels - 多品牌智能家居渠道
"""

from .base import SmartHomeChannel, ChannelStatus
from .xiaomi import XiaomiChannel

try:
    from .haier import HaierChannel
except ImportError:
    HaierChannel = None

# 渠道注册表
CHANNELS = {
    "xiaomi": XiaomiChannel,
}

if HaierChannel:
    CHANNELS["haier"] = HaierChannel


def get_channel(name: str) -> SmartHomeChannel:
    """获取指定渠道实例"""
    channel_class = CHANNELS.get(name)
    if not channel_class:
        raise ValueError(f"Unknown channel: {name}. Available: {list(CHANNELS.keys())}")
    return channel_class()


def list_channels() -> dict:
    """列出所有可用渠道"""
    result = {}
    for name, channel_class in CHANNELS.items():
        channel = channel_class()
        result[name] = channel.check()
    return result
