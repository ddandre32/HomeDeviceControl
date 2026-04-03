"""
海尔IoT类型定义
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class HaierDeviceType(str, Enum):
    """海尔设备类型枚举"""
    AIR_CONDITIONER = "AirConditioner"
    LAMP = "Lamp"
    LIGHT = "Light"
    WINDOW_CURTAINS = "WindowCurtains"
    CURTAIN = "Curtain"
    FRIDGE = "Fridge"
    TV = "TV"
    TELEVISION = "Television"
    SPEAKER = "Speaker"
    CAMERA = "Camera"
    DOOR_LOCK = "DoorLock"
    GATEWAY = "Gateway"
    SENSOR = "Sensor"
    VOICE_PANEL = "VoicePanel"
    SMART_SWITCH = "SmartSwitch"
    BATHROOM_MASTER = "BathRoomMaster"
    CLOTHES_HANGER = "ClothesHanger"
    MASSAGE_BED = "MassageBed"
    SMART_PLUG = "SmartPlug"
    GAS_SENSOR = "GasSensor"
    WATER_IMMERSION_SENSOR = "WaterImmersionSensor"
    OTHER = "Other"


class HaierDeviceStatus(str, Enum):
    """海尔设备状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class HaierDeviceInfo:
    """海尔设备信息"""
    did: str                      # 设备ID
    name: str                     # 设备名称
    type: str                     # 设备类型
    model: Optional[str] = None   # 设备型号
    online: bool = True           # 是否在线
    home_id: Optional[str] = None # 家庭ID
    home_name: Optional[str] = None  # 家庭名称
    room_id: Optional[str] = None    # 房间ID
    room_name: Optional[str] = None  # 房间名称
    floor: Optional[str] = None      # 楼层
    local_ip: Optional[str] = None   # 本地IP
    status: Dict[str, Any] = field(default_factory=dict)  # 设备状态

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "did": self.did,
            "name": self.name,
            "type": self.type,
            "model": self.model,
            "online": self.online,
            "home_id": self.home_id,
            "home_name": self.home_name,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "floor": self.floor,
            "local_ip": self.local_ip,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HaierDeviceInfo":
        """从字典创建"""
        return cls(
            did=data.get("id") or data.get("did", ""),
            name=data.get("name", "Unknown"),
            type=data.get("type", "Other"),
            model=data.get("model"),
            online=data.get("online", True),
            home_id=data.get("home_id"),
            home_name=data.get("home_name"),
            room_id=data.get("room_id"),
            room_name=data.get("room"),
            floor=data.get("floor"),
            local_ip=data.get("local_ip"),
            status=data.get("status", {}),
        )


@dataclass
class HaierHomeInfo:
    """海尔家庭信息"""
    home_id: str                  # 家庭ID
    home_name: str                # 家庭名称
    room_count: int = 0           # 房间数量
    device_count: int = 0         # 设备数量

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "home_id": self.home_id,
            "home_name": self.home_name,
            "room_count": self.room_count,
            "device_count": self.device_count,
        }


@dataclass
class HaierSceneInfo:
    """海尔场景信息"""
    scene_id: str                 # 场景ID
    name: str                     # 场景名称
    enabled: bool = True          # 是否启用
    home_id: Optional[str] = None # 家庭ID

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scene_id": self.scene_id,
            "name": self.name,
            "enabled": self.enabled,
            "home_id": self.home_id,
        }


@dataclass
class HaierProperty:
    """海尔设备属性"""
    siid: int                     # 服务ID
    piid: int                     # 属性ID
    name: str                     # 属性名称
    value: Any                    # 属性值
    description: Optional[str] = None  # 描述


@dataclass
class HaierAction:
    """海尔设备动作"""
    siid: int                     # 服务ID
    aiid: int                     # 动作ID
    name: str                     # 动作名称
    description: Optional[str] = None  # 描述
    in_list: List[Any] = field(default_factory=list)  # 输入参数


@dataclass
class HaierSpec:
    """海尔设备规格"""
    type: str                     # 设备类型
    description: str              # 描述
    properties: List[HaierProperty] = field(default_factory=list)
    actions: List[HaierAction] = field(default_factory=list)
