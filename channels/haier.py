"""
海尔智能家居渠道
基于海尔UWS IoT平台API实现设备控制
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .base import SmartHomeChannel, ChannelStatus, Device, Scene


@dataclass
class HaierDeviceInfo:
    """海尔设备信息"""
    id: str
    type: str
    name: str
    floor: str
    room: str
    online: bool = True
    status: Dict[str, Any] = field(default_factory=dict)


class HaierIoTClient:
    """
    海尔IoT平台客户端
    通过HTTP REST API与海尔UWS平台通信
    """

    # 海尔IoT平台配置 (来自haier-claw项目)
    DEFAULT_BASE_URL = "http://uws-aiot.haier.net:8000"
    MCP_SSE_ENDPOINT = "/m2m-mcp-server/sse"

    def __init__(self, base_url: str = None, family_id: str = None):
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.family_id = family_id
        self._session = None
        self._token = None
        self._token_expires = None

    async def _get_session(self):
        """获取HTTP会话"""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
        return self._session

    async def close(self):
        """关闭会话"""
        if self._session:
            await self._session.close()
            self._session = None

    async def authenticate(self, username: str, password: str) -> bool:
        """
        用户认证获取Token

        Args:
            username: 用户名/手机号
            password: 密码

        Returns:
            bool: 认证是否成功
        """
        try:
            session = await self._get_session()
            # 调用海尔认证接口
            auth_url = f"{self.base_url}/api/auth/login"
            payload = {
                "username": username,
                "password": password
            }

            async with session.post(auth_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._token = data.get("token")
                    # Token有效期24小时
                    self._token_expires = datetime.now() + timedelta(hours=24)
                    return True
                return False
        except Exception as e:
            print(f"海尔认证失败: {e}")
            return False

    def _is_token_valid(self) -> bool:
        """检查Token是否有效"""
        if not self._token or not self._token_expires:
            return False
        # 提前5分钟认为过期
        return datetime.now() < (self._token_expires - timedelta(minutes=5))

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            path: API路径
            **kwargs: 请求参数

        Returns:
            Dict: 响应数据
        """
        session = await self._get_session()

        # 添加认证头
        if self._token:
            headers = kwargs.pop("headers", {})
            headers["Authorization"] = f"Bearer {self._token}"
            kwargs["headers"] = headers

        url = f"{self.base_url}{path}"

        async with session.request(method, url, **kwargs) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 401:
                # Token过期
                self._token = None
                return {"error": "认证已过期，请重新配置"}
            else:
                text = await resp.text()
                return {"error": f"请求失败({resp.status}): {text}"}

    async def get_device_list(self, family_id: str = None) -> List[HaierDeviceInfo]:
        """
        获取设备列表
        优先从本地缓存加载，如未配置则读取默认设备列表

        Args:
            family_id: 家庭ID

        Returns:
            List[HaierDeviceInfo]: 设备列表
        """
        try:
            # 尝试从API获取
            if self._is_token_valid() and family_id:
                path = f"/api/family/{family_id}/devices"
                result = await self._request("GET", path)

                if "error" not in result:
                    devices = []
                    for item in result.get("devices", []):
                        devices.append(HaierDeviceInfo(
                            id=item.get("id"),
                            type=item.get("type"),
                            name=item.get("name"),
                            floor=item.get("floor", "默认"),
                            room=item.get("room", "默认"),
                            online=item.get("online", True),
                            status=item.get("status", {})
                        ))
                    return devices

            # 从本地JSON文件加载默认设备列表
            return await self._load_default_devices()

        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return await self._load_default_devices()

    async def _load_default_devices(self) -> List[HaierDeviceInfo]:
        """从本地文件加载默认设备列表"""
        try:
            # 查找设备列表文件
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "resources", "haier_devices.json"),
                os.path.expanduser("~/.haier/devices.json"),
                "/usr/local/share/haier/devices.json",
            ]

            device_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    device_file = path
                    break

            # 如果没有找到文件，返回空列表
            if not device_file:
                return []

            with open(device_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            devices = []
            for item in data.get("device_list", []):
                devices.append(HaierDeviceInfo(
                    id=item.get("id"),
                    type=item.get("type"),
                    name=item.get("name"),
                    floor=item.get("floor", "默认"),
                    room=item.get("room", "默认"),
                    online=True
                ))

            return devices

        except Exception as e:
            print(f"加载默认设备列表失败: {e}")
            return []

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备状态

        Args:
            device_id: 设备ID

        Returns:
            Dict: 设备状态
        """
        if not self._is_token_valid():
            return {"error": "未认证"}

        path = f"/api/device/{device_id}/status"
        return await self._request("GET", path)

    async def control_device(self, device_id: str, command: str, value: Any = None) -> Dict[str, Any]:
        """
        控制设备

        Args:
            device_id: 设备ID
            command: 控制命令
            value: 参数值

        Returns:
            Dict: 控制结果
        """
        if not self._is_token_valid():
            return {"success": False, "error": "未认证"}

        path = f"/api/device/{device_id}/control"
        payload = {
            "command": command,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

        result = await self._request("POST", path, json=payload)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        return {"success": True, "data": result}

    async def get_scenes(self, family_id: str = None) -> List[Dict[str, Any]]:
        """
        获取场景列表

        Args:
            family_id: 家庭ID

        Returns:
            List: 场景列表
        """
        if not self._is_token_valid():
            return []

        fid = family_id or self.family_id
        if not fid:
            return []

        path = f"/api/family/{fid}/scenes"
        result = await self._request("GET", path)

        if "error" in result:
            return []

        return result.get("scenes", [])

    async def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scene_id: 场景ID

        Returns:
            Dict: 执行结果
        """
        if not self._is_token_valid():
            return {"success": False, "error": "未认证"}

        path = f"/api/scene/{scene_id}/execute"
        result = await self._request("POST", path)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        return {"success": True, "data": result}


class HaierChannel(SmartHomeChannel):
    """
    海尔智能家居渠道
    支持海尔U+平台设备控制
    """

    name = "haier"
    display_name = "海尔"
    cli_command = "haier-cli"

    # 设备类型映射 (海尔类型 -> 标准类型)
    DEVICE_TYPE_MAP = {
        "AirConditioner": "air_conditioner",
        "Lamp": "light",
        "Light": "light",
        "WindowCurtains": "curtain",
        "Curtain": "curtain",
        "Fridge": "fridge",
        "TV": "tv",
        "Speaker": "speaker",
        "Camera": "camera",
        "Lock": "lock",
        "Gateway": "gateway",
        "Sensor": "sensor",
        "VoicePanel": "voice_panel",
        "SmartSwitch": "switch",
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
        self._config = None

    def _get_client(self) -> Optional[HaierIoTClient]:
        """获取或创建海尔客户端"""
        if self._client is None:
            # 从配置加载
            config = self._load_config()
            if config:
                base_url = config.get("base_url", HaierIoTClient.DEFAULT_BASE_URL)
                family_id = config.get("family_id")
                self._client = HaierIoTClient(base_url, family_id)

                # 如果有token，设置到客户端
                if "token" in config:
                    self._client._token = config["token"]
                    expires_str = config.get("token_expires")
                    if expires_str:
                        from datetime import datetime
                        self._client._token_expires = datetime.fromisoformat(expires_str)
            else:
                # 未配置时也创建默认客户端，以便加载演示设备
                self._client = HaierIoTClient(HaierIoTClient.DEFAULT_BASE_URL, None)

        return self._client

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置文件"""
        config_path = os.path.expanduser("~/.haier/config.json")
        if not os.path.exists(config_path):
            return None

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载海尔配置失败: {e}")
            return None

    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        config_dir = os.path.expanduser("~/.haier")
        os.makedirs(config_dir, exist_ok=True)

        config_path = os.path.join(config_dir, "config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"保存海尔配置失败: {e}")

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
            return {"success": False, "error": str(e)}

    def check(self) -> ChannelStatus:
        """检查海尔渠道状态"""
        client = self._get_client()
        if not client:
            return ChannelStatus(
                name=self.name,
                available=True,  # 渠道可用，只是未配置
                configured=False,
                message="海尔SDK就绪，等待配置",
                suggestion="运行: home-device config haier 完成配置"
            )

        # 检查token是否有效
        if client._is_token_valid():
            return ChannelStatus(
                name=self.name,
                available=True,
                configured=True,
                message="已认证，可以控制海尔设备"
            )
        else:
            return ChannelStatus(
                name=self.name,
                available=True,
                configured=False,
                message="认证已过期",
                suggestion="运行: home-device auth haier 重新认证"
            )

    def configure(self) -> bool:
        """配置海尔渠道"""
        print("海尔智能家居配置")
        print("==================")
        print()
        print("1. 输入海尔U+平台账号信息")
        print("2. 或者提供API Token")
        print()

        try:
            # 简单配置方式
            base_url = input(f"海尔服务器地址 [{HaierIoTClient.DEFAULT_BASE_URL}]: ").strip()
            if not base_url:
                base_url = HaierIoTClient.DEFAULT_BASE_URL

            family_id = input("家庭ID (可选): ").strip()

            # 保存基本配置
            config = {
                "base_url": base_url,
                "family_id": family_id if family_id else None,
            }

            self._save_config(config)
            print("配置已保存")
            return True

        except KeyboardInterrupt:
            print("\n配置已取消")
            return False

    def list_devices(self) -> List[Device]:
        """列出所有设备"""
        client = self._get_client()
        if not client:
            return []

        async def _get_devices():
            config = self._load_config()
            family_id = config.get("family_id") if config else None
            devices = await client.get_device_list(family_id)
            await client.close()
            return devices

        try:
            haier_devices = self._run_async(_get_devices())

            # 检查是否是错误返回
            if isinstance(haier_devices, dict) and "error" in haier_devices:
                print(f"获取设备列表失败: {haier_devices['error']}")
                return []

            # 转换为标准Device对象
            result = []
            for d in haier_devices:
                device = Device(
                    id=d.id,
                    name=d.name,
                    type=self._map_device_type(d.type),
                    brand=self.name,
                    room=d.room if d.room else None,
                    online=d.online,
                    model=d.type
                )
                result.append(device)

            return result

        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []

    def get_device(self, device_id: str) -> Optional[Device]:
        """获取设备详情"""
        devices = self.list_devices()
        for device in devices:
            if device.id == device_id:
                return device
        return None

    def control_device(self, device_id: str, action: str, value: Any = None) -> Dict[str, Any]:
        """控制设备"""
        client = self._get_client()
        if not client:
            return {"success": False, "error": "客户端未初始化"}

        # 映射标准动作到海尔命令
        haier_command = self.ACTION_MAP.get(action, action)

        async def _do_control():
            result = await client.control_device(device_id, haier_command, value)
            await client.close()
            return result

        try:
            return self._run_async(_do_control())
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_scenes(self) -> List[Scene]:
        """列出所有场景"""
        client = self._get_client()
        if not client:
            return []

        async def _get_scenes():
            config = self._load_config()
            family_id = config.get("family_id") if config else None
            scenes = await client.get_scenes(family_id)
            await client.close()
            return scenes

        try:
            haier_scenes = self._run_async(_get_scenes())

            if isinstance(haier_scenes, dict) and "error" in haier_scenes:
                return []

            result = []
            for s in haier_scenes:
                scene = Scene(
                    id=s.get("id", ""),
                    name=s.get("name", "Unknown"),
                    enabled=s.get("enabled", True)
                )
                result.append(scene)

            return result

        except Exception:
            return []

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景"""
        client = self._get_client()
        if not client:
            return {"success": False, "error": "客户端未初始化"}

        async def _do_execute():
            result = await client.execute_scene(scene_id)
            await client.close()
            return result

        try:
            return self._run_async(_do_execute())
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _map_device_type(self, haier_type: str) -> str:
        """
        将海尔设备类型映射为标准类型

        Args:
            haier_type: 海尔设备类型

        Returns:
            str: 标准设备类型
        """
        return self.DEVICE_TYPE_MAP.get(haier_type, "unknown")
