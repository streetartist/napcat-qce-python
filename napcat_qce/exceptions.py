"""
NapCat-QCE 异常定义
==================

包含所有 API 可能抛出的异常类型。
"""

from typing import Optional, Dict, Any


class NapCatQCEError(Exception):
    """NapCat-QCE 基础异常类"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(NapCatQCEError):
    """认证错误 - Token 无效或缺失"""

    def __init__(self, message: str = "认证失败", code: str = "AUTH_ERROR", **kwargs):
        super().__init__(message, code, **kwargs)


class ValidationError(NapCatQCEError):
    """验证错误 - 参数无效"""

    def __init__(self, message: str = "参数验证失败", code: str = "VALIDATION_ERROR", **kwargs):
        super().__init__(message, code, **kwargs)


class APIError(NapCatQCEError):
    """API 错误 - 服务器返回错误"""

    def __init__(
        self,
        message: str = "API 调用失败",
        code: str = "API_ERROR",
        status_code: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, code, **kwargs)
        self.status_code = status_code


class NetworkError(NapCatQCEError):
    """网络错误 - 连接失败"""

    def __init__(self, message: str = "网络连接失败", code: str = "NETWORK_ERROR", **kwargs):
        super().__init__(message, code, **kwargs)


class TaskNotFoundError(NapCatQCEError):
    """任务不存在错误"""

    def __init__(self, task_id: str, **kwargs):
        super().__init__(
            message=f"任务不存在: {task_id}",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id},
            **kwargs,
        )
        self.task_id = task_id


class ResourceNotFoundError(NapCatQCEError):
    """资源不存在错误"""

    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        super().__init__(
            message=f"{resource_type} 不存在: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs,
        )


class TimeoutError(NapCatQCEError):
    """超时错误"""

    def __init__(self, message: str = "请求超时", timeout: Optional[float] = None, **kwargs):
        super().__init__(message, code="TIMEOUT_ERROR", **kwargs)
        self.timeout = timeout


class WebSocketError(NapCatQCEError):
    """WebSocket 错误"""

    def __init__(self, message: str = "WebSocket 连接错误", **kwargs):
        super().__init__(message, code="WEBSOCKET_ERROR", **kwargs)
