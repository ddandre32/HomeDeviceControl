"""
小米智能家居渠道
封装 miot SDK，提供原子操作
"""

import sys
import os
import asyncio
import json
from typing import Dict, List, Optional, Any

# 添加 miot 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base import SmartHomeChannel, ChannelStatus, Device, Scene

# 导入 miot SDK
try:
    from miot import MIoTClient
    from miot.error import MIoTError
    MIOT_AVAILABLE = True
except ImportError as e:
    MIOT_AVAILABLE = False


class XiaomiChannel(SmartHomeChannel):
    """
    小米智能家居渠道
    
    基于 XMIoT SDK 封装，只提供原子操作
    """
    
    name = "xiaomi"
    display_name = "小米"
    cli_command = "miot"

    # 已知型号的 Intelligent Speaker SIID 映射
    # 不同音箱型号的智能语音服务 SIID 不同，基于实测结果维护
    _SPEAKER_SIID_MAP = {
        "xiaomi.wifispeaker.oh2p": 7,   # Xiaomi 智能音箱 Pro
        "xiaomi.wifispeaker.l05b": 5,   # 小爱音箱 Play
    }
    _SPEAKER_SIID_FALLBACKS = [7, 5]    # 未知型号的尝试顺序

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client = None
        self._device_model_cache: Dict[str, str] = {}  # did -> model
    
    def _get_client(self) -> Optional[MIoTClient]:
        """获取 MIoT 客户端"""
        if not MIOT_AVAILABLE:
            return None
        if self._client is None:
            try:
                # 从配置文件读取
                import json
                import os
                config_path = os.path.expanduser("~/.miot/config.json")
                if not os.path.exists(config_path):
                    return None
                
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                uuid = config.get('uuid')
                redirect_uri = config.get('redirect_uri')
                cache_path = config.get('cache_path')
                cloud_server = config.get('cloud_server', 'cn')
                oauth_info = config.get('oauth_info')
                
                if not uuid or not redirect_uri:
                    return None
                
                self._client = MIoTClient(
                    uuid=uuid,
                    redirect_uri=redirect_uri,
                    cache_path=cache_path,
                    cloud_server=cloud_server,
                    oauth_info=oauth_info
                )
            except Exception:
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
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(coro)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check(self) -> ChannelStatus:
        """
        检查小米渠道状态
        
        Returns:
            ChannelStatus: 渠道可用性和配置状态
        """
        if not MIOT_AVAILABLE:
            return ChannelStatus(
                name=self.name,
                available=False,
                configured=False,
                message="miot SDK 未安装",
                suggestion="运行: pip install -e ."
            )
        
        try:
            client = self._get_client()
            if not client:
                return ChannelStatus(
                    name=self.name,
                    available=False,
                    configured=False,
                    message="无法初始化 miot 客户端",
                    suggestion="检查配置文件 ~/.miot/config.json"
                )
            
            # 检查是否已认证
            if hasattr(client, '_oauth_info') and client._oauth_info:
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
                    suggestion="运行: home-device auth 完成认证"
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
        引导配置小米渠道
        
        Returns:
            bool: 配置是否成功
        """
        print("小米智能家居配置")
        print("==================")
        print("1. 运行: home-device oauth-url")
        print("2. 访问输出的 URL，登录小米账号")
        print("3. 获取授权码后运行: home-device auth <授权码>")
        print("")
        return False
    
    def list_devices(self) -> List[Device]:
        """
        列出所有设备
        
        Returns:
            List[Device]: 设备列表
        """
        if not MIOT_AVAILABLE:
            return []
        
        client = self._get_client()
        if not client:
            return []
        
        async def _get_devices():
            """获取设备列表"""
            # 初始化客户端
            await client.init()
            
            # 获取设备列表
            devices = await client.get_devices()
            
            # 转换为 Device 对象列表
            device_list = []
            for did, info in devices.items():
                # 处理 MIoTDeviceInfo 对象
                if hasattr(info, 'name'):
                    # 是 MIoTDeviceInfo 对象
                    model = getattr(info, 'model', '')
                    if model:
                        self._device_model_cache[did] = model
                    device = Device(
                        id=did,
                        name=info.name,
                        type=self._infer_type(model),
                        brand=self.name,
                        room=getattr(info, 'room_name', None),
                        online=getattr(info, 'online', False),
                        model=model or None
                    )
                    device_list.append(device)
                elif isinstance(info, dict):
                    # 是字典
                    model = info.get("model", "")
                    if model:
                        self._device_model_cache[did] = model
                    device = Device(
                        id=did,
                        name=info.get("name", "Unknown"),
                        type=self._infer_type(model),
                        brand=self.name,
                        room=info.get("room_name"),
                        online=info.get("online", False),
                        model=model or None
                    )
                    device_list.append(device)
            return device_list
        
        try:
            result = self._run_async(_get_devices())
            # 检查是否是错误返回
            if isinstance(result, dict) and "error" in result:
                return []
            return result
        except Exception:
            return []
    
    def _get_speaker_siid(self, did: str) -> Optional[int]:
        """根据设备型号获取 Intelligent Speaker 服务的 SIID"""
        model = self._device_model_cache.get(did)
        if model and model in self._SPEAKER_SIID_MAP:
            return self._SPEAKER_SIID_MAP[model]
        return None

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
        if not MIOT_AVAILABLE:
            return {"success": False, "error": "miot SDK not available"}
        
        client = self._get_client()
        if not client:
            return {"success": False, "error": "client not initialized"}
        
        async def _do_control():
            """执行控制"""
            await client.init()
            
            # 解析子设备: "parentDid.sXX" → did=parentDid, siid_offset=XX
            did = device_id
            siid_offset = 0
            if '.' in device_id:
                parts = device_id.rsplit('.', 1)
                suffix = parts[1]
                if suffix.startswith('s') and suffix[1:].isdigit():
                    did = parts[0]
                    siid_offset = int(suffix[1:])
            
            # 动作映射 (基于 MIoT SPEC 定义)
            # 灯光控制
            if action == "turn_on":
                siid = siid_offset if siid_offset else 2
                result = await client.set_prop(did, siid, 1, True)
            elif action == "turn_off":
                siid = siid_offset if siid_offset else 2
                result = await client.set_prop(did, siid, 1, False)
            elif action == "set_brightness":
                result = await client.set_prop(did, 2, 2, int(value))
            elif action == "set_color_temperature":
                result = await client.set_prop(did, 2, 3, int(value))
            # 播放控制 (siid=3: Play Control)
            elif action == "speaker_play":
                result = await client.action(did, 3, 2, [])
            elif action == "speaker_pause":
                result = await client.action(did, 3, 3, [])
            elif action == "speaker_stop":
                result = await client.action(did, 3, 3, [])
            elif action == "speaker_previous":
                result = await client.action(did, 3, 5, [])
            elif action == "speaker_next":
                result = await client.action(did, 3, 6, [])
            # 音箱属性 (siid=2: Speaker)
            elif action == "speaker_set_volume":
                result = await client.set_prop(did, 2, 1, int(value))
            elif action == "speaker_get_volume":
                vol = await client.get_prop(did, 2, 1)
                return {"success": True, "volume": vol}
            # 智能语音 (Intelligent Speaker, SIID因型号而异)
            elif action in ("voice_command", "execute_text_directive"):
                aiid = 3 if action == "voice_command" else 4
                params = [str(value)] if value else []
                if aiid == 4 and value:
                    params = [str(value), False]
                siid = self._get_speaker_siid(did)
                if siid:
                    result = await client.action(did, siid, aiid, params)
                else:
                    # 未知型号：依次尝试已知 SIID
                    result = None
                    for try_siid in self._SPEAKER_SIID_FALLBACKS:
                        r = await client.action(did, try_siid, aiid, params)
                        if r.get("code") == 0:
                            self._SPEAKER_SIID_MAP[self._device_model_cache.get(did, '')] = try_siid
                            result = r
                            break
                    if result is None:
                        return {"success": False, "error": "No compatible Intelligent Speaker SIID found"}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            return result
        
        try:
            result = self._run_async(_do_control())
            
            if isinstance(result, dict) and "code" in result:
                # MIoT 返回格式
                if result.get("code") == 0:
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "error": f"Error code: {result.get('code')}"}
            elif isinstance(result, dict) and "success" in result:
                return result
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
        if not MIOT_AVAILABLE:
            return []
        
        client = self._get_client()
        if not client:
            return []
        
        try:
            result = self._run_async(client.get_scenes())
            if not isinstance(result, dict):
                return []
            
            scenes = []
            for scene_id, info in result.items():
                if isinstance(info, dict):
                    scene = Scene(
                        id=str(scene_id),
                        name=info.get("name", "Unknown"),
                        enabled=info.get("enabled", True)
                    )
                    scenes.append(scene)
            return scenes
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
        if not MIOT_AVAILABLE:
            return {"success": False, "error": "miot SDK not available"}
        
        client = self._get_client()
        if not client:
            return {"success": False, "error": "client not initialized"}
        
        try:
            result = self._run_async(client.run_scene(scene_id))
            if isinstance(result, dict):
                return result
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _infer_type(self, model: str) -> str:
        """
        从型号推断设备类型
        
        Args:
            model: 设备型号
            
        Returns:
            str: 设备类型
        """
        model_lower = model.lower()
        
        type_keywords = {
            "light": ["light", "lamp", "灯"],
            "switch": ["switch", "开关"],
            "curtain": ["curtain", "窗帘"],
            "camera": ["camera", "摄像头", "摄像机"],
            "air_conditioner": ["aircondition", "空调"],
            "purifier": ["purifier", "净化器"],
            "speaker": ["speaker", "音箱", "wifispeaker"],
            "control_panel": ["controller", "中控"],
        }
        
        for device_type, keywords in type_keywords.items():
            if any(kw in model_lower for kw in keywords):
                return device_type
        
        return "unknown"
