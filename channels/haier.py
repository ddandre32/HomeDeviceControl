"""
海尔智能家居渠道
基于 MCP (Model Context Protocol) 协议封装，提供原子操作
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
    from haier.types import HaierDeviceInfo, HaierSceneInfo, MCPToolInfo
    from haier.error import HaierError, HaierAuthError, HaierMCPError
    HAIER_AVAILABLE = True
except ImportError as e:
    HAIER_AVAILABLE = False


class HaierChannel(SmartHomeChannel):
    """
    海尔智能家居渠道

    基于 MCP 协议封装，通过 SSE 传输层与海尔U+平台通信
    支持自动重连和工具发现
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

    # 动作映射 (标准动作 -> MCP工具名称)
    ACTION_MAP = {
        "turn_on": "lampControl",
        "turn_off": "lampControl",
        "set_brightness": "lampControl",
        "set_temperature": "airConditionerControl",
        "curtain_control": "curtainControl",
        "lamp_control": "lampControl",
        "get_device_list": "getDeviceList",
        "get_device_status": "getDeviceStatus",
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client = None

    def _get_client(self) -> Optional[HaierClient]:
        """获取 Haier MCP 客户端"""
        if not HAIER_AVAILABLE:
            return None
        if self._client is None:
            try:
                # 从配置文件读取
                import json
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
                print(f"初始化海尔MCP客户端失败: {e}")
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
                    message="无法初始化 haier MCP 客户端",
                    suggestion="检查网络连接和MCP服务器配置"
                )

            # 检查MCP连接状态
            if client.is_authenticated():
                return ChannelStatus(
                    name=self.name,
                    available=True,
                    configured=True,
                    message="MCP连接可用"
                )
            else:
                return ChannelStatus(
                    name=self.name,
                    available=True,
                    configured=False,
                    message="MCP未连接",
                    suggestion="运行: home-device haier auth 完成MCP初始化"
                )
        except Exception as e:
            return ChannelStatus(
                name=self.name,
                available=False,
                configured=False,
                message=f"检查失败: {str(e)[:50]}",
                suggestion="检查MCP服务器连接或重新初始化"
            )

    def configure(self) -> bool:
        """
        引导配置海尔渠道

        Returns:
            bool: 配置是否成功
        """
        print("海尔智能家居MCP配置")
        print("====================")
        print("1. 运行: home-device haier auth")
        print("2. MCP客户端将自动初始化SSE连接")
        print("3. 支持自动重连和心跳保活")
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

        async def _do_control():
            """执行控制"""
            async with client:
                result = await client.control_device(device_id, action, value)
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
        # MCP协议暂不支持场景功能
        return []

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scene_id: 场景ID

        Returns:
            Dict: 执行结果
        """
        # MCP协议暂不支持场景功能
        return {"success": False, "error": "MCP协议暂不支持场景功能"}

    def _infer_type(self, haier_type: str) -> str:
        """
        从海尔类型推断标准设备类型

        Args:
            haier_type: 海尔设备类型

        Returns:
            str: 标准设备类型
        """
        return self.DEVICE_TYPE_MAP.get(haier_type, "unknown")
