"""
海尔IoT SDK - 海尔智能家居设备控制
提供与海尔U+平台的完整交互能力
"""

from .client import HaierClient
from .types import HaierDeviceInfo, HaierHomeInfo, HaierSceneInfo
from .error import HaierError, HaierAuthError, HaierAPIError

__version__ = "1.0.0"

__all__ = [
    "HaierClient",
    "HaierDeviceInfo",
    "HaierHomeInfo",
    "HaierSceneInfo",
    "HaierError",
    "HaierAuthError",
    "HaierAPIError",
]
