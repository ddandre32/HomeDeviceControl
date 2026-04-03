"""
海尔智能家居渠道
封装 haier SDK，提供原子操作
"""

import sys
import os
import asyncio
from typing import Dict, List, Optional, Any

# 添加 haier 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base import SmartHomeChannel, ChannelStatus, Device, Scene

# 导入 haier SDK
try:
    from haier import HaierClient
    from haier.types import HaierDeviceInfo, HaierSceneInfo
    from haier.error import HaierError, HaierAuthError
    HAIER_AVAILABLE = True
except ImportError as e:
    HAIER_AVAILABLE = False


class HaierChannel(SmartHomeChannel):
    """
    海尔智能家居渠道

    基于 Haier SDK 封装，只提供原子操作
    """

    name = "haier"
    display_name = "海尔"
    cli_command = "haier"

    # 设备类型映射 (海尔类型 -> 标准类型)
    DEVICE_TYPE_MAP = {
        "AirConditioner": "air_conditioner",
        "Lamp": "light",
        "Light": "light",
        "WindowCurtains": "curtain",
        "Curtain": "curtain",
        "Fridge": "fridge",
        "TV": "tv",
        "Television": "tv",
        "Speaker": "speaker",
        "Camera": "camera",
        "DoorLock": "lock",
        "Lock": "lock",
        "Gateway": "gateway",
        "Sensor": "sensor",
        "VoicePanel": "voice_panel",
        "SmartSwitch": "switch",
        "BathRoomMaster": "bathroom_master",
        "ClothesHanger": "clothes_hanger",
        "MassageBed": "massage_bed",
        "SmartPlug": "smart_plug",
        "GasSensor": "gas_sensor",
        "WaterImmersionSensor": "water_sensor",
    }

    # 动作映射 (标准动作 -> 海尔命令)
    ACTION_MAP = {
        "turn_on": "openDevice",
        "turn_off": "closeDevice",
        "set_brightness": "setBrightness",
        "set_temperature": "setTemperature",
        "set_mode": "setMode",
        "set_color_temperature": "setColorTemperature",
        "set_openness": "setOpenness",
        "increase_brightness": "increaseBrightness",
        "decrease_brightness": "decreaseBrightness",
        "increase_temperature": "increaseTemperature",
        "decrease_temperature": "decreaseTemperature",
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client = None

    def _get_client(self) -> Optional[HaierClient]:
        """获取 Haier 客户端"""
        if not HAIER_AVAILABLE:
            return None
        if self._client is None:
            try:
                # 从配置文件读取
                import json
                import os
                config_path = os.path.expanduser("~/.haier/config.json")

                base_url = None
                family_id = None

                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    base_url = config.get('base_url')
                    family_id = config.get('family_id')

                self._client = HaierClient(
                    base_url=base_url,
                    family_id=family_id,
                    timeout=self.timeout,
                )
            except Exception as e:
                print(f"初始化海尔客户端失败: {e}")
                return None
        return self._client

    def _run_async(self, coro):
        """运行异步代码"""
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=self.timeout)
            else:
                return loop.run_until_complete(coro)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def check(self) -> ChannelStatus:
        """
        检查海尔渠道状态

        Returns:
            ChannelStatus: 渠道可用性和配置状态
        """
        if not HAIER_AVAILABLE:
            return ChannelStatus(
                name=self.name,
                available=False,
                configured=False,
                message="haier SDK 未安装",
                suggestion="运行: pip install -e ."
            )

        try:
            client = self._get_client()
            if not client:
                return ChannelStatus(
                    name=self.name,
                    available=False,
                    configured=False,
                    message="无法初始化 haier 客户端",
                    suggestion="检查配置文件 ~/.haier/config.json"
                )

            # 检查是否已认证
            if client.is_authenticated():
                return ChannelStatus(
                    name=self.name,
                    available=True,
                    configured=True,
                    message="可用"
                )
            else:
                return ChannelStatus(
                    name=self.name,
                    available=True,
                    configured=False,
                    message="未认证",
                    suggestion="运行: home-device haier auth 完成认证"
                )
        except Exception as e:
            return ChannelStatus(
                name=self.name,
                available=False,
                configured=False,
                message=f"检查失败: {str(e)[:50]}",
                suggestion="检查网络连接或重新认证"
            )

    def configure(self) -> bool:
        """
        引导配置海尔渠道

        Returns:
            bool: 配置是否成功
        """
        print("海尔智能家居配置")
        print("==================")
        print("1. 运行: home-device haier auth")
        print("2. 输入海尔账号和密码完成认证")
        print("")
        return False

    def list_devices(self) -> List[Device]:
        """
        列出所有设备

        Returns:
            List[Device]: 设备列表
        """
        if not HAIER_AVAILABLE:
            return []

        client = self._get_client()
        if not client:
            return []

        async def _get_devices():
            """获取设备列表"""
            async with client:
                haier_devices = await client.get_devices()

                # 转换为 Device 对象列表
                device_list = []
                for did, info in haier_devices.items():
                    device = Device(
                        id=info.did,
                        name=info.name,
                        type=self._infer_type(info.type),
                        brand=self.name,
                        room=info.room_name,
                        online=info.online,
                        model=info.model or info.type,
                    )
                    device_list.append(device)

                return device_list

        try:
            result = self._run_async(_get_devices())
            # 检查是否是错误返回
            if isinstance(result, dict) and "error" in result:
                print(f"获取设备列表失败: {result['error']}")
                return []
            return result
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_device(self, device_id: str) -> Optional[Device]:
        """
        获取设备详情

        Args:
            device_id: 设备ID

        Returns:
            Optional[Device]: 设备信息
        """
        devices = self.list_devices()
        for device in devices:
            if device.id == device_id:
                return device
        return None

    def control_device(self, device_id: str, action: str, value: Any = None) -> Dict[str, Any]:
        """
        控制设备（原子操作）

        Args:
            device_id: 设备ID
            action: 动作
            value: 参数值

        Returns:
            Dict: 操作结果
        """
        if not HAIER_AVAILABLE:
            return {"success": False, "error": "haier SDK not available"}

        client = self._get_client()
        if not client:
            return {"success": False, "error": "client not initialized"}

        # 映射标准动作到海尔命令
        haier_command = self.ACTION_MAP.get(action, action)

        async def _do_control():
            """执行控制"""
            async with client:
                result = await client.control_device(device_id, haier_command, value)
                return result

        try:
            result = self._run_async(_do_control())

            if isinstance(result, dict) and "success" in result:
                return result
            elif isinstance(result, dict):
                return {"success": True, "data": result}
            else:
                return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_scenes(self) -> List[Scene]:
        """
        列出所有场景

        Returns:
            List[Scene]: 场景列表
        """
        if not HAIER_AVAILABLE:
            return []

        client = self._get_client()
        if not client:
            return []

        async def _get_scenes():
            """获取场景列表"""
            async with client:
                haier_scenes = await client.get_scenes()

                scenes = []
                for scene_id, info in haier_scenes.items():
                    scene = Scene(
                        id=scene_id,
                        name=info.name,
                        enabled=info.enabled,
                    )
                    scenes.append(scene)

                return scenes

        try:
            result = self._run_async(_get_scenes())
            if not isinstance(result, list):
                return []
            return result
        except Exception:
            return []

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scene_id: 场景ID

        Returns:
            Dict: 执行结果
        """
        if not HAIER_AVAILABLE:
            return {"success": False, "error": "haier SDK not available"}

        client = self._get_client()
        if not client:
            return {"success": False, "error": "client not initialized"}

        async def _do_execute():
            """执行场景"""
            async with client:
                result = await client.run_scene(scene_id)
                return result

        try:
            result = self._run_async(_do_execute())
            if isinstance(result, dict) and "success" in result:
                return result
            elif isinstance(result, dict):
                return {"success": True, "data": result}
            else:
                return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _infer_type(self, haier_type: str) -> str:
        """
        从海尔类型推断标准设备类型

        Args:
            haier_type: 海尔设备类型

        Returns:
            str: 标准设备类型
        """
        return self.DEVICE_TYPE_MAP.get(haier_type, "unknown")
