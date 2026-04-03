"""
海尔IoT错误定义
"""

from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    """海尔错误码"""
    # 通用错误
    UNKNOWN_ERROR = "unknown_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"

    # 认证错误
    AUTH_FAILED = "auth_failed"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    NOT_AUTHENTICATED = "not_authenticated"

    # 设备错误
    DEVICE_NOT_FOUND = "device_not_found"
    DEVICE_OFFLINE = "device_offline"
    DEVICE_ERROR = "device_error"
    CONTROL_FAILED = "control_failed"

    # API错误
    API_ERROR = "api_error"
    RATE_LIMITED = "rate_limited"
    INVALID_PARAM = "invalid_param"


class HaierError(Exception):
    """海尔基础异常"""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, data: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data or {}

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": False,
            "error": self.message,
            "code": self.code.value,
            "data": self.data,
        }

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


class HaierAuthError(HaierError):
    """海尔认证异常"""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.AUTH_FAILED, data: Optional[dict] = None):
        super().__init__(message, code, data)


class HaierAPIError(HaierError):
    """海尔API异常"""

    def __init__(self, message: str, status_code: int = 0, data: Optional[dict] = None):
        code = ErrorCode.API_ERROR
        if status_code == 401:
            code = ErrorCode.TOKEN_EXPIRED
        elif status_code == 429:
            code = ErrorCode.RATE_LIMITED
        super().__init__(message, code, data)
        self.status_code = status_code


class HaierDeviceError(HaierError):
    """海尔设备异常"""

    def __init__(self, message: str, device_id: str = "", code: ErrorCode = ErrorCode.DEVICE_ERROR):
        super().__init__(message, code, {"device_id": device_id})
        self.device_id = device_id
