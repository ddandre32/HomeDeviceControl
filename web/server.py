# -*- coding: utf-8 -*-
"""
智能家居地图 Web 服务器
提供 Web 界面用于展示户型图和设备位置
"""
import asyncio
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

from aiohttp import web
import aiohttp_cors

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miot import MIoTClient
from miot.types import MIoTDeviceInfo, MIoTHomeInfo

# 导入 channels 模块
try:
    from channels import get_channel, list_channels
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False


# 静态文件路径
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"
DATA_DIR = Path.home() / ".miot" / "web"


@dataclass
class Room:
    """房间定义"""
    room_id: str  # 使用 room_id 避免与 Python 内置 id 冲突
    name: str
    x: float  # 左上角x坐标
    y: float  # 左上角y坐标
    width: float  # 宽度
    height: float  # 高度
    color: str = "#e3f2fd"  # 房间背景色
    type: str = "room"  # 房间类型

    def to_dict(self) -> dict:
        """转换为字典 - 兼容前端格式"""
        return {
            "id": self.room_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "type": self.type
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        """从字典创建 - 兼容前端格式"""
        # 前端使用 "id" 字段，后端使用 "room_id"
        room_id = data.get("id") or data.get("room_id", "")
        return cls(
            room_id=room_id,
            name=data.get("name", "未命名房间"),
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", 100)),
            height=float(data.get("height", 100)),
            color=data.get("color", "#e3f2fd"),
            type=data.get("type", "room")
        )


@dataclass
class DevicePosition:
    """设备在地图上的位置"""
    device_id: str
    room_id: Optional[str]
    x: float  # 在户型图上的x坐标
    y: float  # 在户型图上的y坐标

    def to_dict(self) -> dict:
        """转换为字典 - 兼容前端格式（前端只需要 x 和 y）"""
        return {
            "x": self.x,
            "y": self.y
        }

    @classmethod
    def from_dict(cls, data: dict, device_id: str = "") -> "DevicePosition":
        """从字典创建 - 兼容前端格式"""
        return cls(
            device_id=data.get("device_id") or device_id,
            room_id=data.get("room_id"),
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0))
        )


@dataclass
class FloorPlan:
    """户型图定义"""
    home_id: str
    home_name: str
    width: int = 800  # 画布宽度
    height: int = 600  # 画布高度
    rooms: List[Room] = None
    device_positions: Dict[str, DevicePosition] = None

    def __post_init__(self):
        if self.rooms is None:
            self.rooms = []
        if self.device_positions is None:
            self.device_positions = {}

    def to_dict(self) -> dict:
        """转换为字典 - 兼容前端格式"""
        return {
            "home_id": self.home_id,
            "home_name": self.home_name,
            "width": self.width,
            "height": self.height,
            "rooms": [r.to_dict() for r in self.rooms],
            "device_positions": {k: v.to_dict() for k, v in self.device_positions.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FloorPlan":
        """从字典创建 - 兼容前端格式"""
        rooms = []
        for r in data.get("rooms", []):
            try:
                rooms.append(Room.from_dict(r))
            except Exception as e:
                print(f"解析房间数据失败: {e}, 数据: {r}")

        device_positions = {}
        for k, v in data.get("device_positions", {}).items():
            try:
                # 兼容前端格式：前端只发送 {x, y}
                device_positions[k] = DevicePosition.from_dict(v, device_id=k)
            except Exception as e:
                print(f"解析设备位置失败: {e}, 数据: {v}")

        return cls(
            home_id=data.get("home_id", ""),
            home_name=data.get("home_name", ""),
            width=data.get("width", 800),
            height=data.get("height", 600),
            rooms=rooms,
            device_positions=device_positions
        )


class FloorPlanManager:
    """户型图管理器"""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._plans: Dict[str, FloorPlan] = {}
        self._load_all()

    def _get_file_path(self, home_id: str) -> Path:
        """获取户型图文件路径"""
        return self.data_dir / f"floorplan_{home_id}.json"

    def _load_all(self):
        """加载所有户型图"""
        for file_path in self.data_dir.glob("floorplan_*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    plan = FloorPlan.from_dict(data)
                    self._plans[plan.home_id] = plan
            except Exception as e:
                print(f"加载户型图失败 {file_path}: {e}")

    def get(self, home_id: str) -> Optional[FloorPlan]:
        """获取户型图"""
        return self._plans.get(home_id)

    def get_or_create(self, home_id: str, home_name: str = "") -> FloorPlan:
        """获取或创建户型图"""
        if home_id not in self._plans:
            self._plans[home_id] = FloorPlan(
                home_id=home_id,
                home_name=home_name or f"家 {home_id[:8]}"
            )
            self.save(home_id)
        return self._plans[home_id]

    def save(self, home_id: str):
        """保存户型图"""
        if home_id in self._plans:
            file_path = self._get_file_path(home_id)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._plans[home_id].to_dict(), f, ensure_ascii=False, indent=2)

    def update(self, plan: FloorPlan):
        """更新户型图"""
        self._plans[plan.home_id] = plan
        self.save(plan.home_id)

    def list_all(self) -> List[FloorPlan]:
        """列出所有户型图"""
        return list(self._plans.values())


class SmartHomeWebServer:
    """智能家居 Web 服务器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.floor_plan_manager = FloorPlanManager()
        self._client: Optional[MIoTClient] = None
        self._setup_routes()
        self._setup_cors()

    def _setup_cors(self):
        """设置 CORS"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        # 为所有路由添加 CORS
        for route in list(self.app.router.routes()):
            cors.add(route)

    def _setup_routes(self):
        """设置路由"""
        # 静态文件 - 禁用缓存以避免前端更新问题
        self.app.router.add_static(
            "/static",
            STATIC_DIR,
            name="static",
            append_version=True,  # 添加版本号强制刷新缓存
            show_index=False
        )

        # 页面路由
        self.app.router.add_get("/", self.index_handler)
        self.app.router.add_get("/test", self.test_handler)
        self.app.router.add_get("/api/homes", self.get_homes_handler)
        self.app.router.add_get("/api/homes/{home_id}/floorplan", self.get_floorplan_handler)
        self.app.router.add_post("/api/homes/{home_id}/floorplan", self.save_floorplan_handler)
        self.app.router.add_get("/api/homes/{home_id}/devices", self.get_devices_handler)
        self.app.router.add_post("/api/devices/{device_id}/control", self.control_device_handler)
        self.app.router.add_get("/api/devices/{device_id}/status", self.get_device_status_handler)
        self.app.router.add_post("/api/homes/{home_id}/device-position", self.update_device_position_handler)

    async def index_handler(self, request: web.Request) -> web.Response:
        """主页"""
        index_file = TEMPLATE_DIR / "index.html"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(text=content, content_type="text/html")

        # 如果模板文件不存在，返回简单的提示页面
        fallback_html = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>智能家居地图</title></head>
<body>
    <h1>🏠 智能家居地图服务器已启动</h1>
    <p>服务器运行正常，但前端文件未找到。</p>
    <p>请确保 static 和 templates 目录存在。</p>
    <hr>
    <h2>API 端点：</h2>
    <ul>
        <li><a href="/api/homes">/api/homes</a> - 获取家庭列表</li>
        <li><a href="/api/devices">/api/devices</a> - 获取设备列表</li>
    </ul>
</body>
</html>'''
        return web.Response(text=fallback_html, content_type="text/html")

    async def test_handler(self, request: web.Request) -> web.Response:
        """测试页面"""
        test_file = TEMPLATE_DIR / "test.html"
        if test_file.exists():
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(text=content, content_type="text/html")
        return web.Response(text="Test page not found", status=404)

    async def get_homes_handler(self, request: web.Request) -> web.Response:
        """获取家庭列表 - 未认证时返回演示数据"""
        try:
            client = await self._get_client()
            if not client:
                # 返回演示家庭数据
                demo_home = {
                    "home_id": "demo",
                    "home_name": "我的家（演示模式）",
                    "room_count": 6,
                    "device_count": 8,
                    "floor_plan": None
                }
                return web.json_response({"homes": [demo_home]})

            homes = await client.get_homes()
            result = []
            for home_id, home in homes.items():
                # 获取或创建户型图
                floor_plan = self.floor_plan_manager.get_or_create(home_id, home.home_name)
                result.append({
                    "home_id": home_id,
                    "home_name": home.home_name,
                    "room_count": len(home.room_list),
                    "device_count": len(home.dids),
                    "floor_plan": floor_plan.to_dict()
                })

            return web.json_response({"homes": result})
        except Exception as e:
            # 出错时返回演示数据
            demo_home = {
                "home_id": "demo",
                "home_name": "我的家（演示模式）",
                "room_count": 6,
                "device_count": 8,
                "floor_plan": None
            }
            return web.json_response({"homes": [demo_home]})

    async def get_floorplan_handler(self, request: web.Request) -> web.Response:
        """获取户型图 - 如果没有则返回空户型"""
        try:
            home_id = request.match_info["home_id"]
            floor_plan = self.floor_plan_manager.get(home_id)
            if floor_plan:
                return web.json_response(floor_plan.to_dict())
            else:
                # 返回空户型图
                return web.json_response({
                    "home_id": home_id,
                    "home_name": "未命名",
                    "width": 900,
                    "height": 600,
                    "rooms": [],
                    "device_positions": {}
                })
        except Exception as e:
            # 出错时返回空户型图
            return web.json_response({
                "home_id": request.match_info.get("home_id", "demo"),
                "home_name": "未命名",
                "width": 900,
                "height": 600,
                "rooms": [],
                "device_positions": {}
            })

    async def save_floorplan_handler(self, request: web.Request) -> web.Response:
        """保存户型图"""
        try:
            home_id = request.match_info["home_id"]
            data = await request.json()

            print(f"[保存户型图] home_id: {home_id}, rooms数量: {len(data.get('rooms', []))}, device_positions数量: {len(data.get('device_positions', {}))}")

            # 验证数据
            if not data.get("rooms"):
                print("[警告] 保存的户型图没有房间数据")
            else:
                for i, room in enumerate(data.get("rooms", [])):
                    print(f"[房间 {i}] id: {room.get('id')}, name: {room.get('name')}, x: {room.get('x')}, y: {room.get('y')}")

            floor_plan = FloorPlan.from_dict(data)
            floor_plan.home_id = home_id

            print(f"[解析后] rooms数量: {len(floor_plan.rooms)}")

            self.floor_plan_manager.update(floor_plan)

            print(f"[保存成功] 户型图已保存到: {self.floor_plan_manager._get_file_path(home_id)}")

            return web.json_response({"success": True, "rooms_count": len(floor_plan.rooms)})
        except Exception as e:
            print(f"[保存失败] 错误: {e}")
            import traceback
            traceback.print_exc()
            return web.json_response({"error": str(e)}, status=500)

    async def get_devices_handler(self, request: web.Request) -> web.Response:
        """获取设备列表 - 优先从channels获取真实设备，并获取设备状态"""
        home_id = request.match_info.get("home_id")

        try:
            # 首先尝试从channels获取真实设备
            real_devices = await self._get_real_devices(home_id)
            if real_devices:
                # 获取channels设备的实际状态
                for device in real_devices:
                    await self._enrich_device_status(device)
                return web.json_response({"devices": real_devices})
        except Exception as e:
            print(f"从channels获取设备失败: {e}")

        # 如果channels获取失败，尝试从MIoT客户端获取
        try:
            client = await self._get_client()
            if client:
                devices = await client.get_devices()
                result = []
                for device_id, device in devices.items():
                    if home_id and device.home_id != home_id:
                        continue

                    position = None
                    if self.floor_plan_manager and home_id:
                        floor_plan = self.floor_plan_manager.get(home_id)
                        if floor_plan and floor_plan.device_positions:
                            pos = floor_plan.device_positions.get(device_id)
                            if pos:
                                position = {"x": pos.x, "y": pos.y, "room_id": pos.room_id}

                    # 构建设备基础信息
                    device_data = {
                        "did": device.did,
                        "name": device.name,
                        "model": device.model,
                        "online": device.online,
                        "home_id": device.home_id,
                        "home_name": device.home_name,
                        "room_id": device.room_id,
                        "room_name": device.room_name,
                        "position": position,
                    }

                    # 尝试获取设备状态（power等）
                    await self._enrich_device_status_from_miot(client, device_data)
                    result.append(device_data)

                if result:
                    return web.json_response({"devices": result})
        except Exception as e:
            print(f"从MIoT获取设备失败: {e}")

        # 最后返回演示数据（也添加power状态）
        demo_devices = self._generate_demo_devices(home_id)
        return web.json_response({"devices": demo_devices})

    async def _get_real_devices(self, home_id: str) -> list:
        """从channels获取真实设备"""
        if not CHANNELS_AVAILABLE:
            return None

        devices = []
        channel_status = list_channels()

        # 获取MIoT客户端用于补充设备状态
        miot_client = None
        try:
            miot_client = await self._get_client()
        except Exception:
            pass

        for channel_name, status in channel_status.items():
            if status.configured:
                try:
                    channel = get_channel(channel_name)
                    channel_devices = channel.list_devices()
                    for device in channel_devices:
                        # 获取设备位置
                        position = None
                        if self.floor_plan_manager and home_id:
                            floor_plan = self.floor_plan_manager.get(home_id)
                            if floor_plan and floor_plan.device_positions:
                                pos = floor_plan.device_positions.get(device.id)
                                if pos:
                                    position = {"x": pos.x, "y": pos.y, "room_id": pos.room_id}

                        device_data = {
                            "did": device.id,
                            "name": device.name,
                            "model": device.model or "unknown",
                            "online": device.online,
                            "home_id": home_id,
                            "home_name": "我的家",
                            "room_id": None,
                            "room_name": device.room,
                            "position": position,
                            "channel": channel_name
                        }

                        # 尝试从MIoT获取设备状态
                        if miot_client:
                            await self._enrich_device_status_from_miot(miot_client, device_data)

                        devices.append(device_data)
                except Exception as e:
                    print(f"从{channel_name}获取设备失败: {e}")

        return devices if devices else None

    def _generate_demo_devices(self, home_id: str) -> list:
        """生成演示设备数据"""
        return [
            {"did": "demo_1", "name": "客厅主灯", "model": "light", "online": True, "power": True, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_2", "name": "卧室灯", "model": "light", "online": True, "power": False, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_3", "name": "餐厅灯", "model": "light", "online": True, "power": True, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_4", "name": "客厅空调", "model": "air_conditioner", "online": True, "power": True, "temperature": 24, "mode": "cool", "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_5", "name": "智能音箱", "model": "speaker", "online": True, "power": True, "volume": 50, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_6", "name": "智能窗帘", "model": "curtain", "online": True, "power": True, "position": 80, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_7", "name": "门口摄像头", "model": "camera", "online": True, "power": True, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
            {"did": "demo_8", "name": "智能门锁", "model": "lock", "online": True, "power": True, "lock_state": "locked", "battery": 85, "home_id": home_id, "home_name": "演示家庭", "room_id": None, "room_name": None, "position": None},
        ]

    async def _enrich_device_status(self, device: dict):
        """从channels获取设备状态并 enrich 到设备数据中"""
        try:
            if not CHANNELS_AVAILABLE:
                return

            channel_name = device.get("channel", "xiaomi")
            channel = get_channel(channel_name)

            # 获取设备详细信息
            device_detail = channel.get_device(device["did"])
            if device_detail:
                # 复制状态属性
                if hasattr(device_detail, "power"):
                    device["power"] = device_detail.power
                if hasattr(device_detail, "brightness"):
                    device["brightness"] = device_detail.brightness
                if hasattr(device_detail, "temperature"):
                    device["temperature"] = device_detail.temperature
                if hasattr(device_detail, "mode"):
                    device["mode"] = device_detail.mode
        except Exception as e:
            print(f"获取设备 {device.get('did')} 状态失败: {e}")

    async def _enrich_device_status_from_miot(self, client, device: dict):
        """从MIoT客户端获取设备状态并 enrich 到设备数据中"""
        try:
            did = device.get("did")
            if not did or not device.get("online"):
                return

            # 尝试获取 power 状态 (siid=2, piid=1 是常见的开关属性)
            try:
                power = await client.get_prop(did, 2, 1)
                if power is not None:
                    device["power"] = power
            except Exception:
                pass  # 设备可能不支持这个属性

            # 尝试获取亮度 (灯光设备)
            try:
                brightness = await client.get_prop(did, 2, 2)
                if brightness is not None:
                    device["brightness"] = brightness
            except Exception:
                pass

            # 尝试获取色温
            try:
                color_temp = await client.get_prop(did, 2, 3)
                if color_temp is not None:
                    device["color_temperature"] = color_temp
            except Exception:
                pass

            # 尝试获取当前温度 (空调/传感器)
            try:
                temperature = await client.get_prop(did, 3, 1)
                if temperature is not None:
                    device["temperature"] = temperature
            except Exception:
                pass

            # 尝试获取目标温度 (空调)
            try:
                target_temp = await client.get_prop(did, 2, 4)
                if target_temp is not None:
                    device["target_temperature"] = target_temp
            except Exception:
                pass

            # 尝试获取模式
            try:
                mode = await client.get_prop(did, 2, 3)
                if mode is not None:
                    device["mode"] = mode
            except Exception:
                pass

            # 尝试获取风速
            try:
                fan_speed = await client.get_prop(did, 2, 5)
                if fan_speed is not None:
                    device["fan_speed"] = fan_speed
            except Exception:
                pass

            # 尝试获取湿度
            try:
                humidity = await client.get_prop(did, 3, 2)
                if humidity is not None:
                    device["humidity"] = humidity
            except Exception:
                pass

        except Exception as e:
            print(f"获取MIoT设备 {device.get('did')} 状态失败: {e}")

    async def control_device_handler(self, request: web.Request) -> web.Response:
        """控制设备"""
        try:
            device_id = request.match_info["device_id"]
            data = await request.json()
            action = data.get("action")
            value = data.get("value")

            client = await self._get_client()
            if not client:
                return web.json_response({"error": "Not authenticated"}, status=401)

            # 根据 action 执行不同操作
            if action == "turn_on":
                result = await client.set_prop(device_id, 2, 1, True)
            elif action == "turn_off":
                result = await client.set_prop(device_id, 2, 1, False)
            elif action == "set_brightness":
                result = await client.set_prop(device_id, 2, 2, int(value))
            elif action == "speaker_pause":
                result = await client.action(device_id, 3, 2, [])
            elif action == "speaker_next":
                result = await client.action(device_id, 3, 3, [])
            elif action == "speaker_previous":
                result = await client.action(device_id, 3, 4, [])
            else:
                return web.json_response({"error": f"Unknown action: {action}"}, status=400)

            return web.json_response({"success": True, "result": result})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def get_device_status_handler(self, request: web.Request) -> web.Response:
        """获取设备状态 - 获取所有属性"""
        try:
            device_id = request.match_info["device_id"]
            client = await self._get_client()
            if not client:
                # 返回演示数据
                return web.json_response({
                    "did": device_id,
                    "name": "设备",
                    "online": True,
                    "power": True,
                    "brightness": 80,
                    "temperature": 22,
                    "mode": "制冷",
                    "fan_speed": "自动",
                    "humidity": 45,
                    "volume": 30,
                    "battery": 85,
                    "color_temperature": 4000,
                    "properties": {"power": True, "brightness": 80}
                })

            # 获取设备信息
            device = await client.get_device(device_id)
            if not device:
                return web.json_response({"error": "Device not found"}, status=404)

            result = {
                "did": device.did,
                "name": device.name,
                "model": device.model,
                "online": device.online,
                "power": None,
                "brightness": None,
                "temperature": None,
                "mode": None,
                "fan_speed": None,
                "humidity": None,
                "volume": None,
                "battery": None,
                "color_temperature": None,
                "properties": {}
            }

            # 只有当设备在线时才尝试获取状态
            if device.online:
                # 获取设备SPEC以了解支持的属性
                try:
                    spec = await client.get_device_spec_lite(device.urn)
                    if spec:
                        result["properties"] = {}
                        # 尝试获取所有可读属性
                        for prop_id, prop_info in spec.items():
                            if prop_info.readable and "prop." in prop_id:
                                parts = prop_id.split(".")
                                if len(parts) >= 4:
                                    siid = int(parts[2])
                                    piid = int(parts[3])
                                    try:
                                        value = await client.get_prop(device_id, siid, piid)
                                        result["properties"][prop_info.description or f"prop_{siid}_{piid}"] = value

                                        # 根据属性名称映射到标准字段
                                        desc_lower = (prop_info.description or "").lower()
                                        if "开关" in desc_lower or "电源" in desc_lower or "on" in desc_lower:
                                            result["power"] = bool(value) if value is not None else None
                                        elif "亮度" in desc_lower or "brightness" in desc_lower:
                                            result["brightness"] = value
                                        elif "温度" in desc_lower and "设定" in desc_lower:
                                            result["temperature"] = value
                                        elif "模式" in desc_lower or "mode" in desc_lower:
                                            result["mode"] = value
                                        elif "风速" in desc_lower or "fan" in desc_lower:
                                            result["fan_speed"] = value
                                        elif "湿度" in desc_lower or "humidity" in desc_lower:
                                            result["humidity"] = value
                                        elif "音量" in desc_lower or "volume" in desc_lower:
                                            result["volume"] = value
                                        elif "色温" in desc_lower or "color temp" in desc_lower:
                                            result["color_temperature"] = value
                                    except:
                                        pass
                except:
                    pass

                # 如果SPEC获取失败，尝试常见属性
                if not result["properties"]:
                    # 尝试获取开关状态
                    try:
                        power = await client.get_prop(device_id, 2, 1)
                        result["power"] = power
                        result["properties"]["电源"] = power
                    except:
                        pass

                    # 尝试获取亮度
                    try:
                        brightness = await client.get_prop(device_id, 2, 2)
                        result["brightness"] = brightness
                        result["properties"]["亮度"] = brightness
                    except:
                        pass

            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def update_device_position_handler(self, request: web.Request) -> web.Response:
        """更新设备位置"""
        try:
            home_id = request.match_info["home_id"]
            data = await request.json()

            device_id = data.get("device_id")
            x = data.get("x")
            y = data.get("y")
            room_id = data.get("room_id")

            floor_plan = self.floor_plan_manager.get_or_create(home_id)
            floor_plan.device_positions[device_id] = DevicePosition(
                device_id=device_id,
                room_id=room_id,
                x=x,
                y=y
            )
            self.floor_plan_manager.update(floor_plan)

            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _get_client(self) -> Optional[MIoTClient]:
        """获取 MIoT 客户端"""
        if self._client is None:
            config_path = Path.home() / ".miot" / "config.json"
            if not config_path.exists():
                return None

            with open(config_path, "r") as f:
                config = json.load(f)

            uuid = config.get("uuid")
            redirect_uri = config.get("redirect_uri")
            oauth_info = config.get("oauth_info")

            if not uuid or not oauth_info:
                return None

            self._client = MIoTClient(
                uuid=uuid,
                redirect_uri=redirect_uri,
                oauth_info=oauth_info,
                cloud_server=config.get("cloud_server", "cn")
            )
            await self._client.init()

        return self._client

    async def start(self):
        """启动服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"🌐 Web 服务器已启动: http://{self.host}:{self.port}")
        return runner


async def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="智能家居 Web 服务器")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    parser.add_argument("--port", type=int, default=8080, help="端口")
    args = parser.parse_args()

    server = SmartHomeWebServer(host=args.host, port=args.port)
    runner = await server.start()

    # 保持运行
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
