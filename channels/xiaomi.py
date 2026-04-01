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
    from miot_sdk import MIoTClient
    from miot_sdk.error import MIoTError
    MIOT_AVAILABLE = True
except ImportError:
    MIOT_AVAILABLE = False


class XiaomiChannel(SmartHomeChannel):
    """
    小米智能家居渠道
    
    基于 XMIoT SDK 封装，只提供原子操作
    """
    
    name = "xiaomi"
    display_name = "小米"
    cli_command = "miot"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client = None
    
    def _get_client(self) -> Optional[MIoTClient]:
        """获取 MIoT 客户端"""
        if not MIOT_AVAILABLE:
            return None
        if self._client is None:
            try:
                self._client = MIoTClient()
            except Exception:
                return None
        return self._client
    
    def _run_async(self, coro):
        """运行异步代码"""
        try:
            return asyncio.run(coro)
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
        
        try:
            result = self._run_async(client.get_devices())
            if not isinstance(result, dict) or not result.get("success", True):
                return []
            
            devices = []
            for did, info in result.items():
                if isinstance(info, dict):
                    device = Device(
                        id=did,
                        name=info.get("name", "Unknown"),
                        type=self._infer_type(info.get("model", "")),
                        brand=self.name,
                        room=info.get("room_name"),
                        online=info.get("online", False),
                        model=info.get("model")
                    )
                    devices.append(device)
            return devices
        except Exception:
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
        if not MIOT_AVAILABLE:
            return {"success": False, "error": "miot SDK not available"}
        
        client = self._get_client()
        if not client:
            return {"success": False, "error": "client not initialized"}
        
        try:
            # 动作映射
            if action == "turn_on":
                result = self._run_async(client.set_prop(device_id, 2, 1, True))
            elif action == "turn_off":
                result = self._run_async(client.set_prop(device_id, 2, 1, False))
            elif action == "set_brightness":
                result = self._run_async(client.set_prop(device_id, 2, 2, value))
            elif action == "set_temperature":
                result = self._run_async(client.set_prop(device_id, 2, 2, value))
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            if isinstance(result, dict):
                return result
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
            "air_conditioner": ["air", "空调", "ac"],
            "purifier": ["purifier", "净化器"],
            "speaker": ["speaker", "音箱"],
            "camera": ["camera", "摄像头"],
        }
        
        for device_type, keywords in type_keywords.items():
            if any(kw in model_lower for kw in keywords):
                return device_type
        
        return "unknown"
