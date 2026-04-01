"""
小米智能家居渠道
封装 miot CLI，提供原子操作
"""

import subprocess
import json
import shutil
from typing import Dict, List, Optional, Any

from .base import SmartHomeChannel, ChannelStatus, Device, Scene


class XiaomiChannel(SmartHomeChannel):
    """
    小米智能家居渠道
    
    基于 XMIoT CLI 封装，只提供原子操作
    """
    
    name = "xiaomi"
    display_name = "小米"
    cli_command = "miot"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def _run(self, args: List[str]) -> Dict[str, Any]:
        """
        运行 miot CLI 命令
        
        Args:
            args: 命令参数
            
        Returns:
            Dict: 命令输出
        """
        cmd = [self.cli_command, "--format", "json"] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"success": False, "error": "Failed to parse output"}
            
            if result.stderr:
                return {"success": False, "error": result.stderr.strip()}
            
            return {"success": False, "error": "No output"}
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {self.timeout}s"}
        except FileNotFoundError:
            return {"success": False, "error": "miot not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check(self) -> ChannelStatus:
        """
        检查小米渠道状态
        
        Returns:
            ChannelStatus: 渠道状态
        """
        # 检查 miot 是否安装
        if not shutil.which(self.cli_command):
            return ChannelStatus(
                name=self.name,
                available=False,
                configured=False,
                message="miot CLI 未安装",
                suggestion="运行: pip install xiaomi-iot-manager"
            )
        
        # 检查是否已认证
        result = self._run(["device", "list"])
        if not result.get("success"):
            error = result.get("error", "")
            if "NOT_AUTHENTICATED" in str(error) or "未认证" in str(error):
                return ChannelStatus(
                    name=self.name,
                    available=True,
                    configured=False,
                    message="未认证",
                    suggestion="运行: miot system oauth-url 获取授权链接"
                )
            return ChannelStatus(
                name=self.name,
                available=True,
                configured=False,
                message=f"检查失败: {error}",
                suggestion="检查网络连接或重新认证"
            )
        
        return ChannelStatus(
            name=self.name,
            available=True,
            configured=True,
            message="可用"
        )
    
    def configure(self) -> bool:
        """
        引导配置小米渠道
        
        Returns:
            bool: 配置是否成功
        """
        # 输出配置指引
        print("小米智能家居配置")
        print("==================")
        print("1. 运行: miot system oauth-url")
        print("2. 访问输出的 URL，登录小米账号")
        print("3. 获取授权码后运行: miot system auth <授权码>")
        print("")
        
        # 实际配置需要用户手动完成
        return False
    
    def list_devices(self) -> List[Device]:
        """
        列出所有设备
        
        Returns:
            List[Device]: 设备列表
        """
        result = self._run(["device", "list"])
        
        if not result.get("success"):
            return []
        
        devices = []
        for item in result.get("data", []):
            device = Device(
                id=item.get("did", ""),
                name=item.get("name", "Unknown"),
                type=self._infer_type(item.get("model", "")),
                brand=self.name,
                room=item.get("room", {}).get("name") if isinstance(item.get("room"), dict) else None,
                online=item.get("online", False),
                model=item.get("model")
            )
            devices.append(device)
        
        return devices
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """
        获取设备详情
        
        Args:
            device_id: 设备ID
            
        Returns:
            Optional[Device]: 设备信息
        """
        result = self._run(["device", "get", device_id])
        
        if not result.get("success"):
            return None
        
        item = result.get("data", {})
        return Device(
            id=item.get("did", device_id),
            name=item.get("name", "Unknown"),
            type=self._infer_type(item.get("model", "")),
            brand=self.name,
            room=item.get("room", {}).get("name") if isinstance(item.get("room"), dict) else None,
            online=item.get("online", False),
            model=item.get("model")
        )
    
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
        # 动作映射到 miot 命令
        action_map = {
            "turn_on": ("prop", "set", device_id, "2", "1", "true"),
            "turn_off": ("prop", "set", device_id, "2", "1", "false"),
            "set_brightness": ("prop", "set", device_id, "2", "2", str(value)) if value else None,
            "set_temperature": ("prop", "set", device_id, "2", "2", str(value)) if value else None,
        }
        
        args = action_map.get(action)
        if not args:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        return self._run(["device"] + list(args))
    
    def list_scenes(self) -> List[Scene]:
        """
        列出所有场景
        
        Returns:
            List[Scene]: 场景列表
        """
        result = self._run(["scene", "list"])
        
        if not result.get("success"):
            return []
        
        scenes = []
        for item in result.get("data", []):
            scene = Scene(
                id=item.get("scene_id", ""),
                name=item.get("scene_name", "Unknown"),
                enabled=item.get("enabled", False)
            )
            scenes.append(scene)
        
        return scenes
    
    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            Dict: 执行结果
        """
        return self._run(["scene", "run", scene_id])
    
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
        }
        
        for device_type, keywords in type_keywords.items():
            if any(kw in model_lower for kw in keywords):
                return device_type
        
        return "unknown"