"""
海尔IoT MCP客户端
基于MCP (Model Context Protocol) 协议与海尔U+平台交互
使用SSE传输层，支持自动重连
"""

import json
import time
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path

import httpx
from sseclient import SSEClient

from .types import (
    HaierDeviceInfo,
    HaierHomeInfo,
    HaierSceneInfo,
    MCPToolInfo,
    MCPCallResult,
)
from .error import (
    HaierError,
    HaierAuthError,
    HaierMCPError,
    ErrorCode,
)


@dataclass
class MCPConnectionInfo:
    """MCP连接信息"""
    initialized: bool = False
    server_info: Dict[str, Any] = None
    tools: List[MCPToolInfo] = None
    last_ping: float = 0

    def __post_init__(self):
        if self.server_info is None:
            self.server_info = {}
        if self.tools is None:
            self.tools = []


class HaierClient:
    """
    海尔IoT MCP客户端
    基于MCP协议实现，使用SSE传输层
    """

    DEFAULT_BASE_URL = "http://uws-aiot.haier.net"
    MCP_SSE_ENDPOINT = "/m2m-mcp-server/sse"
    MCP_SERVER_IP = "10.205.241.117"  # 通过hosts映射无法解析时的备用IP
    RECONNECT_INTERVAL = 5  # 重连间隔（秒）
    PING_INTERVAL = 5  # 心跳间隔（秒）

    def __init__(
        self,
        base_url: str = None,
        family_id: str = None,
        cache_path: str = None,
        timeout: int = 30,
    ):
        """
        初始化海尔MCP客户端

        Args:
            base_url: 服务器地址，默认使用海尔UWS平台
            family_id: 家庭ID
            cache_path: 缓存目录路径
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.family_id = family_id
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._sse_client: Optional[SSEClient] = None
        self._connection_info = MCPConnectionInfo()
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._session_id: Optional[str] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._initialized = False
        self._lock = asyncio.Lock()

        # 设置缓存路径
        if cache_path:
            self.cache_path = Path(cache_path)
        else:
            self.cache_path = Path.home() / ".haier"
        self.cache_path.mkdir(parents=True, exist_ok=True)

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self):
        """关闭连接"""
        self._initialized = False

        # 取消后台任务
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None

        # 关闭HTTP客户端
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def initialize(self) -> bool:
        """
        初始化MCP连接

        Returns:
            bool: 初始化是否成功
        """
        async with self._lock:
            if self._initialized:
                return True

            try:
                # 先测试直接IP连接
                import sys
                print(f"正在连接MCP服务器: {self.MCP_SERVER_IP}...", file=sys.stderr)

                # 发送initialize请求 (使用IP + Host头)
                init_result = await self._send_request(
                    "initialize",
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "home-device-control",
                            "version": "2.0.0"
                        }
                    }
                )

                if init_result:
                    self._connection_info.server_info = init_result.get("serverInfo", {})
                    self._connection_info.initialized = True
                    self._initialized = True

                    # 启动后台任务
                    self._reconnect_task = asyncio.create_task(self._reconnect_loop())
                    self._ping_task = asyncio.create_task(self._ping_loop())

                    return True
                else:
                    raise HaierMCPError(
                        "MCP初始化失败",
                        ErrorCode.MCP_INITIALIZE_FAILED
                    )

            except Exception as e:
                raise HaierMCPError(
                    f"MCP连接失败: {str(e)}",
                    ErrorCode.MCP_CONNECTION_ERROR
                )

    async def _process_sse_events(self):
        """处理SSE事件流"""
        try:
            if self._sse_client:
                for event in self._sse_client:
                    if event.event == "message":
                        try:
                            data = json.loads(event.data)
                            await self._handle_sse_message(data)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            # SSE连接断开，标记需要重连
            self._initialized = False

    async def _handle_sse_message(self, data: Dict[str, Any]):
        """处理SSE消息"""
        msg_id = data.get("id")
        msg_type = data.get("type")

        if msg_id and msg_id in self._pending_requests:
            future = self._pending_requests.pop(msg_id)
            if not future.done():
                future.set_result(data)

    async def _send_request(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        发送MCP请求

        Args:
            method: 方法名
            params: 参数

        Returns:
            Optional[Dict]: 响应数据
        """
        msg_id = f"req_{int(time.time() * 1000)}_{threading.current_thread().ident}"

        message = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params
        }

        # 创建Future等待响应
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[msg_id] = future

        try:
            # 使用IP地址访问，同时保留Host头
            client = await self._get_client()
            # 优先使用IP地址访问（绕过DNS）
            post_url = f"http://{self.MCP_SERVER_IP}{self.MCP_SSE_ENDPOINT}"

            response = await client.post(
                post_url,
                json=message,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Host": "uws-aiot.haier.net",  # 保留原始Host头
                }
            )

            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    raise HaierMCPError(
                        f"MCP错误: {result['error']}",
                        ErrorCode.MCP_CONNECTION_ERROR
                    )
            else:
                raise HaierMCPError(
                    f"HTTP错误: {response.status_code}",
                    ErrorCode.MCP_CONNECTION_ERROR
                )

        except asyncio.TimeoutError:
            raise HaierMCPError(
                "请求超时",
                ErrorCode.TIMEOUT_ERROR
            )
        except Exception as e:
            if isinstance(e, HaierMCPError):
                raise
            raise HaierMCPError(
                f"请求失败: {str(e)}",
                ErrorCode.MCP_CONNECTION_ERROR
            )
        finally:
            self._pending_requests.pop(msg_id, None)

    async def _reconnect_loop(self):
        """自动重连循环"""
        while True:
            try:
                await asyncio.sleep(self.RECONNECT_INTERVAL)

                if not self._initialized:
                    try:
                        await self.initialize()
                    except Exception:
                        pass

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _ping_loop(self):
        """心跳循环"""
        while True:
            try:
                await asyncio.sleep(self.PING_INTERVAL)

                if self._initialized:
                    try:
                        await self._send_request("ping", {})
                        self._connection_info.last_ping = time.time()
                    except Exception:
                        self._initialized = False

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def is_authenticated(self) -> bool:
        """检查是否已认证（MCP通过initialize完成认证）"""
        return self._initialized and self._connection_info.initialized

    async def get_tools(self) -> List[MCPToolInfo]:
        """
        获取可用工具列表

        Returns:
            List[MCPToolInfo]: 工具列表
        """
        if not self._initialized:
            raise HaierMCPError(
                "MCP未初始化",
                ErrorCode.MCP_INITIALIZE_FAILED
            )

        try:
            result = await self._send_request(
                "tools/list",
                {}
            )

            tools = []
            for tool_data in result.get("tools", []):
                tool = MCPToolInfo.from_dict(tool_data)
                tools.append(tool)

            self._connection_info.tools = tools
            return tools

        except Exception as e:
            raise HaierMCPError(
                f"获取工具列表失败: {str(e)}",
                ErrorCode.MCP_TOOL_NOT_FOUND
            )

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> MCPCallResult:
        """
        调用MCP工具

        Args:
            tool_name: 工具名称
            arguments: 参数

        Returns:
            MCPCallResult: 调用结果
        """
        if not self._initialized:
            raise HaierMCPError(
                "MCP未初始化",
                ErrorCode.MCP_INITIALIZE_FAILED
            )

        try:
            result = await self._send_request(
                "tools/call",
                {
                    "name": tool_name,
                    "arguments": arguments
                }
            )

            return MCPCallResult(
                is_error=result.get("isError", False),
                content=result.get("content", []),
                tool_name=tool_name
            )

        except Exception as e:
            raise HaierMCPError(
                f"工具调用失败: {str(e)}",
                ErrorCode.MCP_CONNECTION_ERROR
            )

    # ============== 设备控制方法 ==============

    async def get_devices(self, home_id: str = None) -> Dict[str, HaierDeviceInfo]:
        """
        获取设备列表

        Args:
            home_id: 家庭ID（可选）

        Returns:
            Dict[str, HaierDeviceInfo]: 设备列表
        """
        # 构建参数
        arguments = {}
        if home_id or self.family_id:
            arguments["deviceId"] = home_id or self.family_id

        # 调用MCP工具
        result = await self.call_tool("getDeviceList", arguments)

        if result.is_error:
            raise HaierMCPError(
                "获取设备列表失败",
                ErrorCode.DEVICE_ERROR
            )

        # 解析返回内容
        text_content = result.get_text_content()
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError:
            data = {"device_list": []}

        devices = {}
        for item in data.get("device_list", []):
            device = HaierDeviceInfo.from_dict(item)
            devices[device.did] = device

        return devices

    async def get_device(self, device_id: str) -> Optional[HaierDeviceInfo]:
        """
        获取设备详情

        Args:
            device_id: 设备ID

        Returns:
            Optional[HaierDeviceInfo]: 设备信息
        """
        devices = await self.get_devices()
        return devices.get(device_id)

    async def get_device_status(self, device_ids: List[str]) -> Dict[str, Any]:
        """
        获取设备状态

        Args:
            device_ids: 设备ID列表

        Returns:
            Dict: 设备状态
        """
        result = await self.call_tool(
            "getDeviceStatus",
            {"deviceIds": device_ids}
        )

        if result.is_error:
            raise HaierMCPError(
                "获取设备状态失败",
                ErrorCode.DEVICE_ERROR
            )

        text_content = result.get_text_content()
        try:
            return json.loads(text_content)
        except json.JSONDecodeError:
            return {}

    async def control_device(
        self,
        device_id: str,
        command: str,
        value: Any = None
    ) -> Dict[str, Any]:
        """
        控制设备

        Args:
            device_id: 设备ID
            command: 控制命令
            value: 参数值

        Returns:
            Dict: 操作结果
        """
        # 命令映射到MCP工具
        command_map = {
            "turn_on": "lampControl",
            "turn_off": "lampControl",
            "set_brightness": "lampControl",
            "set_temperature": "airConditionerControl",
            "curtain_control": "curtainControl",
        }

        tool_name = command_map.get(command, command)

        # 构建参数
        arguments = {"deviceIds": [device_id]}
        if value is not None:
            if command == "set_brightness":
                arguments["brightness"] = str(value)
            elif command == "set_temperature":
                arguments["temperature"] = str(value)
            elif command == "curtain_control":
                arguments["openness"] = str(value)

        # 调用MCP工具
        result = await self.call_tool(tool_name, arguments)

        return {
            "success": not result.is_error,
            "device_id": device_id,
            "command": command,
            "result": result.get_text_content()
        }

    async def get_scenes(self, home_id: str = None) -> Dict[str, HaierSceneInfo]:
        """
        获取场景列表

        Args:
            home_id: 家庭ID

        Returns:
            Dict[str, HaierSceneInfo]: 场景列表
        """
        # 场景功能暂不支持MCP
        return {}

    async def run_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scene_id: 场景ID

        Returns:
            Dict: 执行结果
        """
        # 场景功能暂不支持MCP
        return {"success": False, "error": "场景功能暂不支持"}

    async def authenticate(self, username: str, password: str) -> bool:
        """
        用户认证（MCP通过initialize完成）

        Args:
            username: 用户名/手机号
            password: 密码

        Returns:
            bool: 认证是否成功
        """
        # MCP不需要显式认证，通过initialize完成
        return await self.initialize()

    async def batch_control(
        self,
        operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量控制设备

        Args:
            operations: 操作列表

        Returns:
            List[Dict]: 操作结果列表
        """
        results = []
        for op in operations:
            try:
                result = await self.control_device(
                    op.get("device_id"),
                    op.get("action"),
                    op.get("value")
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "device_id": op.get("device_id")
                })
        return results
