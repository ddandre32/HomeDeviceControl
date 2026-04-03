"""
海尔IoT客户端
提供与海尔U+平台的完整交互能力
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .types import (
    HaierDeviceInfo,
    HaierHomeInfo,
    HaierSceneInfo,
    HaierDeviceType,
)
from .error import (
    HaierError,
    HaierAuthError,
    HaierAPIError,
    HaierDeviceError,
    ErrorCode,
)


@dataclass
class HaierAuthInfo:
    """海尔认证信息"""
    token: str
    expires_at: datetime
    refresh_token: Optional[str] = None

    def is_valid(self) -> bool:
        """检查token是否有效（提前5分钟认为过期）"""
        return datetime.now() < (self.expires_at - timedelta(minutes=5))


class HaierClient:
    """
    海尔IoT客户端
    提供与海尔U+平台的HTTP REST API交互
    """

    DEFAULT_BASE_URL = "http://uws-aiot.haier.net:8000"
    MCP_SSE_ENDPOINT = "/m2m-mcp-server/sse"

    def __init__(
        self,
        base_url: str = None,
        family_id: str = None,
        cache_path: str = None,
        timeout: int = 30,
    ):
        """
        初始化海尔客户端

        Args:
            base_url: 服务器地址，默认使用海尔UWS平台
            family_id: 家庭ID
            cache_path: 缓存目录路径
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.family_id = family_id
        self.timeout = timeout
        self._session = None
        self._auth_info: Optional[HaierAuthInfo] = None

        # 设置缓存路径
        if cache_path:
            self.cache_path = Path(cache_path)
        else:
            self.cache_path = Path.home() / ".haier"
        self.cache_path.mkdir(parents=True, exist_ok=True)

        # 加载已保存的认证信息
        self._load_auth()

    async def _get_session(self):
        """获取HTTP会话"""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def close(self):
        """关闭会话"""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    def _get_auth_header(self) -> Dict[str, str]:
        """获取认证头"""
        if self._auth_info and self._auth_info.is_valid():
            return {"Authorization": f"Bearer {self._auth_info.token}"}
        return {}

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Dict = None,
        params: Dict = None,
        need_auth: bool = True,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            path: API路径
            json_data: JSON请求体
            params: URL参数
            need_auth: 是否需要认证

        Returns:
            Dict: 响应数据

        Raises:
            HaierAuthError: 认证失败
            HaierAPIError: API请求失败
        """
        session = await self._get_session()

        headers = {}
        if need_auth:
            headers.update(self._get_auth_header())
            if not headers.get("Authorization"):
                raise HaierAuthError(
                    "未认证，请先调用authenticate()",
                    ErrorCode.NOT_AUTHENTICATED,
                )

        url = f"{self.base_url}{path}"

        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    self._auth_info = None
                    raise HaierAuthError(
                        "认证已过期，请重新认证",
                        ErrorCode.TOKEN_EXPIRED,
                    )
                elif resp.status == 429:
                    raise HaierAPIError(
                        "请求过于频繁，请稍后再试",
                        status_code=429,
                    )
                else:
                    text = await resp.text()
                    raise HaierAPIError(
                        f"请求失败: {text}",
                        status_code=resp.status,
                    )
        except asyncio.TimeoutError:
            raise HaierError("请求超时", ErrorCode.TIMEOUT_ERROR)
        except HaierError:
            raise
        except Exception as e:
            raise HaierError(f"网络错误: {str(e)}", ErrorCode.NETWORK_ERROR)

    async def authenticate(self, username: str, password: str) -> bool:
        """
        用户认证获取Token

        Args:
            username: 用户名/手机号
            password: 密码

        Returns:
            bool: 认证是否成功

        Raises:
            HaierAuthError: 认证失败
        """
        try:
            session = await self._get_session()
            auth_url = f"{self.base_url}/api/auth/login"
            payload = {"username": username, "password": password}

            async with session.post(auth_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("token")
                    if token:
                        self._auth_info = HaierAuthInfo(
                            token=token,
                            expires_at=datetime.now() + timedelta(hours=24),
                            refresh_token=data.get("refresh_token"),
                        )
                        self._save_auth()
                        return True
                    else:
                        raise HaierAuthError("响应中未包含token")
                elif resp.status == 401:
                    raise HaierAuthError("用户名或密码错误", ErrorCode.AUTH_FAILED)
                else:
                    text = await resp.text()
                    raise HaierAuthError(f"认证失败: {text}")
        except HaierError:
            raise
        except Exception as e:
            raise HaierAuthError(f"认证请求失败: {str(e)}")

    def _save_auth(self):
        """保存认证信息到文件"""
        if self._auth_info:
            auth_file = self.cache_path / "auth.json"
            with open(auth_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "token": self._auth_info.token,
                        "refresh_token": self._auth_info.refresh_token,
                        "expires_at": self._auth_info.expires_at.isoformat(),
                    },
                    f,
                    indent=2,
                )

    def _load_auth(self):
        """从文件加载认证信息"""
        auth_file = self.cache_path / "auth.json"
        if auth_file.exists():
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._auth_info = HaierAuthInfo(
                    token=data["token"],
                    refresh_token=data.get("refresh_token"),
                    expires_at=datetime.fromisoformat(data["expires_at"]),
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self._auth_info is not None and self._auth_info.is_valid()

    async def get_homes(self) -> Dict[str, HaierHomeInfo]:
        """
        获取家庭列表

        Returns:
            Dict[str, HaierHomeInfo]: 家庭列表
        """
        path = "/api/homes"
        result = await self._request("GET", path)

        homes = {}
        for item in result.get("homes", []):
            home = HaierHomeInfo(
                home_id=item.get("home_id"),
                home_name=item.get("home_name"),
                room_count=item.get("room_count", 0),
                device_count=item.get("device_count", 0),
            )
            homes[home.home_id] = home

        return homes

    async def get_devices(self, home_id: str = None) -> Dict[str, HaierDeviceInfo]:
        """
        获取设备列表

        Args:
            home_id: 家庭ID，默认使用初始化时的family_id

        Returns:
            Dict[str, HaierDeviceInfo]: 设备列表
        """
        hid = home_id or self.family_id
        if hid:
            path = f"/api/homes/{hid}/devices"
        else:
            path = "/api/devices"

        try:
            result = await self._request("GET", path)

            devices = {}
            for item in result.get("devices", []):
                device = HaierDeviceInfo.from_dict(item)
                devices[device.did] = device

            return devices
        except HaierError:
            # 如果从API获取失败，尝试从本地缓存加载
            return await self._load_devices_from_cache()

    async def _load_devices_from_cache(self) -> Dict[str, HaierDeviceInfo]:
        """从本地缓存加载设备列表"""
        devices = {}

        # 查找设备列表文件
        possible_paths = [
            Path(__file__).parent.parent / "resources" / "haier_devices.json",
            self.cache_path / "devices.json",
            Path("/usr/local/share/haier/devices.json"),
        ]

        for device_file in possible_paths:
            if device_file.exists():
                try:
                    with open(device_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    for item in data.get("device_list", []):
                        device = HaierDeviceInfo.from_dict(item)
                        devices[device.did] = device

                    return devices
                except (json.JSONDecodeError, KeyError):
                    continue

        return devices

    async def get_device(self, device_id: str) -> Optional[HaierDeviceInfo]:
        """
        获取设备详情

        Args:
            device_id: 设备ID

        Returns:
            HaierDeviceInfo: 设备信息，不存在返回None
        """
        try:
            path = f"/api/devices/{device_id}"
            result = await self._request("GET", path)
            return HaierDeviceInfo.from_dict(result.get("device", {}))
        except HaierDeviceError:
            return None

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备状态

        Args:
            device_id: 设备ID

        Returns:
            Dict: 设备状态
        """
        path = f"/api/devices/{device_id}/status"
        return await self._request("GET", path)

    async def set_prop(
        self, device_id: str, siid: int, piid: int, value: Any
    ) -> Dict[str, Any]:
        """
        设置设备属性

        Args:
            device_id: 设备ID
            siid: 服务ID
            piid: 属性ID
            value: 属性值

        Returns:
            Dict: 操作结果
        """
        path = f"/api/devices/{device_id}/properties"
        payload = {"siid": siid, "piid": piid, "value": value}
        return await self._request("POST", path, json_data=payload)

    async def get_prop(self, device_id: str, siid: int, piid: int) -> Any:
        """
        获取设备属性

        Args:
            device_id: 设备ID
            siid: 服务ID
            piid: 属性ID

        Returns:
            Any: 属性值
        """
        path = f"/api/devices/{device_id}/properties"
        result = await self._request("GET", path, params={"siid": siid, "piid": piid})
        return result.get("value")

    async def action(
        self, device_id: str, siid: int, aiid: int, in_list: List[Any] = None
    ) -> Dict[str, Any]:
        """
        执行设备动作

        Args:
            device_id: 设备ID
            siid: 服务ID
            aiid: 动作ID
            in_list: 输入参数列表

        Returns:
            Dict: 操作结果
        """
        path = f"/api/devices/{device_id}/actions"
        payload = {"siid": siid, "aiid": aiid, "in": in_list or []}
        return await self._request("POST", path, json_data=payload)

    async def control_device(
        self, device_id: str, command: str, value: Any = None
    ) -> Dict[str, Any]:
        """
        控制设备（高级封装）

        Args:
            device_id: 设备ID
            command: 控制命令（如"turn_on", "set_temperature"）
            value: 参数值

        Returns:
            Dict: 操作结果
        """
        # 命令映射到具体API调用
        command_map = {
            "turn_on": ("action", 2, 1, []),  # siid=2, aiid=1
            "turn_off": ("action", 2, 2, []),  # siid=2, aiid=2
            "set_brightness": ("set_prop", 2, 2),  # siid=2, piid=2
            "set_temperature": ("set_prop", 2, 2),  # siid=2, piid=2
        }

        if command not in command_map:
            raise HaierDeviceError(f"未知命令: {command}", device_id)

        mapping = command_map[command]
        if mapping[0] == "action":
            return await self.action(device_id, mapping[1], mapping[2], mapping[3])
        else:
            return await self.set_prop(device_id, mapping[1], mapping[2], value)

    async def get_scenes(self, home_id: str = None) -> Dict[str, HaierSceneInfo]:
        """
        获取场景列表

        Args:
            home_id: 家庭ID

        Returns:
            Dict[str, HaierSceneInfo]: 场景列表
        """
        hid = home_id or self.family_id
        if hid:
            path = f"/api/homes/{hid}/scenes"
        else:
            path = "/api/scenes"

        result = await self._request("GET", path)

        scenes = {}
        for item in result.get("scenes", []):
            scene = HaierSceneInfo(
                scene_id=item.get("id") or item.get("scene_id"),
                name=item.get("name", "Unknown"),
                enabled=item.get("enabled", True),
                home_id=hid,
            )
            scenes[scene.scene_id] = scene

        return scenes

    async def run_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scene_id: 场景ID

        Returns:
            Dict: 执行结果
        """
        path = f"/api/scenes/{scene_id}/run"
        return await self._request("POST", path)

    async def batch_control(
        self, operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量控制设备

        Args:
            operations: 操作列表

        Returns:
            List[Dict]: 操作结果列表
        """
        path = "/api/batch"
        return await self._request("POST", path, json_data={"operations": operations})
