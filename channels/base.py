"""
Smart Home Channel 抽象基类
定义多品牌智能家居渠道的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ChannelStatus:
    """渠道状态"""
    name: str
    available: bool          # CLI 是否安装
    configured: bool         # 是否已配置/认证
    message: str             # 状态说明
    suggestion: Optional[str] = None  # 修复建议


@dataclass
class Device:
    """设备信息"""
    id: str                  # 设备ID
    name: str                # 设备名称
    type: str                # 设备类型
    brand: str               # 品牌
    room: Optional[str] = None  # 房间
    online: bool = True      # 是否在线
    model: Optional[str] = None  # 型号


@dataclass
class Scene:
    """场景信息"""
    id: str                  # 场景ID
    name: str                # 场景名称
    enabled: bool = True     # 是否启用


class SmartHomeChannel(ABC):
    """
    智能家居渠道抽象基类
    
    所有品牌渠道（小米、海尔等）必须实现此接口
    只提供原子操作，不做任何智能封装
    """
    
    # 渠道标识
    name: str = ""           # 渠道名称: xiaomi/haier
    display_name: str = ""   # 显示名称: 小米/海尔
    cli_command: str = ""    # CLI 命令: miot/haier-cli
    
    @abstractmethod
    def check(self) -> ChannelStatus:
        """
        检查渠道状态
        
        Returns:
            ChannelStatus: 渠道可用性和配置状态
        """
        pass
    
    @abstractmethod
    def configure(self) -> bool:
        """
        引导配置渠道
        
        Returns:
            bool: 配置是否成功
        """
        pass
    
    @abstractmethod
    def list_devices(self) -> List[Device]:
        """
        列出所有设备
        
        Returns:
            List[Device]: 设备列表
        """
        pass
    
    @abstractmethod
    def get_device(self, device_id: str) -> Optional[Device]:
        """
        获取设备详情
        
        Args:
            device_id: 设备ID
            
        Returns:
            Optional[Device]: 设备信息，不存在返回 None
        """
        pass
    
    @abstractmethod
    def control_device(self, device_id: str, action: str, value: Any = None) -> Dict[str, Any]:
        """
        控制设备（原子操作）
        
        Args:
            device_id: 设备ID
            action: 动作 (turn_on/turn_off/set_brightness/set_temperature等)
            value: 动作参数值
            
        Returns:
            Dict: 操作结果
        """
        pass
    
    @abstractmethod
    def list_scenes(self) -> List[Scene]:
        """
        列出所有场景
        
        Returns:
            List[Scene]: 场景列表
        """
        pass
    
    @abstractmethod
    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        执行场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            Dict: 执行结果
        """
        pass
