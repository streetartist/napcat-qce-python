"""
NapCat-QCE 主客户端
==================

提供与 NapCat-QCE API 交互的主要接口。
"""

import json
import time
import threading
from typing import Optional, Dict, Any, List, Callable, Generator
from urllib.parse import urljoin

import requests

from .types import (
    ChatType,
    ExportFormat,
    TaskStatus,
    Group,
    GroupMember,
    Friend,
    UserInfo,
    Message,
    ExportTask,
    ScheduledExport,
    StickerPack,
    ExportFile,
    SystemInfo,
    Peer,
    MessageFilter,
    ExportOptions,
    ScheduledExportConfig,
    ScheduleType,
    TimeRangeType,
)
from .exceptions import (
    NapCatQCEError,
    AuthenticationError,
    ValidationError,
    APIError,
    NetworkError,
    TaskNotFoundError,
)


class BaseAPI:
    """API 基类"""

    def __init__(self, client: "NapCatQCE"):
        self._client = client

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._client._request(method, endpoint, params, json_data, **kwargs)


class GroupsAPI(BaseAPI):
    """群组 API"""

    def get_all(
        self,
        page: int = 1,
        limit: int = 999,
        force_refresh: bool = False,
    ) -> List[Group]:
        """
        获取所有群组

        Args:
            page: 页码
            limit: 每页数量
            force_refresh: 是否强制刷新缓存

        Returns:
            群组列表
        """
        data = self._request(
            "GET",
            "/api/groups",
            params={
                "page": page,
                "limit": limit,
                "forceRefresh": str(force_refresh).lower(),
            },
        )
        groups_data = data.get("groups", [])
        return [Group.from_dict(g) for g in groups_data]

    def get(self, group_code: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取群组详情

        Args:
            group_code: 群号
            force_refresh: 是否强制刷新

        Returns:
            群组详细信息
        """
        return self._request(
            "GET",
            f"/api/groups/{group_code}",
            params={"forceRefresh": str(force_refresh).lower()},
        )

    def get_members(
        self,
        group_code: str,
        force_refresh: bool = False,
    ) -> List[GroupMember]:
        """
        获取群成员列表

        Args:
            group_code: 群号
            force_refresh: 是否强制刷新

        Returns:
            群成员列表
        """
        data = self._request(
            "GET",
            f"/api/groups/{group_code}/members",
            params={"forceRefresh": str(force_refresh).lower()},
        )
        # API 直接返回成员数组
        if isinstance(data, list):
            return [GroupMember.from_dict(m) for m in data]
        return []


class FriendsAPI(BaseAPI):
    """好友 API"""

    def get_all(self, page: int = 1, limit: int = 999) -> List[Friend]:
        """
        获取所有好友

        Args:
            page: 页码
            limit: 每页数量

        Returns:
            好友列表
        """
        data = self._request(
            "GET",
            "/api/friends",
            params={"page": page, "limit": limit},
        )
        friends_data = data.get("friends", [])
        return [Friend.from_dict(f) for f in friends_data]

    def get(self, uid: str, no_cache: bool = False) -> Dict[str, Any]:
        """
        获取好友详情

        Args:
            uid: 好友 UID
            no_cache: 是否禁用缓存

        Returns:
            好友详细信息
        """
        return self._request(
            "GET",
            f"/api/friends/{uid}",
            params={"no_cache": str(no_cache).lower()},
        )


class UsersAPI(BaseAPI):
    """用户 API"""

    def get(self, uid: str, no_cache: bool = False) -> UserInfo:
        """
        获取用户信息

        Args:
            uid: 用户 UID
            no_cache: 是否禁用缓存

        Returns:
            用户信息
        """
        data = self._request(
            "GET",
            f"/api/users/{uid}",
            params={"no_cache": str(no_cache).lower()},
        )
        return UserInfo.from_dict(data)


class MessagesAPI(BaseAPI):
    """消息 API"""

    def fetch(
        self,
        chat_type: int,
        peer_uid: str,
        filter: Optional[MessageFilter] = None,
        batch_size: int = 5000,
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        批量获取消息

        Args:
            chat_type: 聊天类型 (1=私聊, 2=群聊)
            peer_uid: 对方 UID 或群号
            filter: 消息筛选条件
            batch_size: 批量大小
            page: 页码
            limit: 每页数量

        Returns:
            包含消息列表和分页信息的字典
        """
        peer = {"chatType": chat_type, "peerUid": peer_uid}
        body = {
            "peer": peer,
            "batchSize": batch_size,
            "page": page,
            "limit": limit,
        }
        if filter:
            body["filter"] = filter.to_dict()

        data = self._request("POST", "/api/messages/fetch", json_data=body)

        # 解析消息
        messages = [Message.from_dict(m) for m in data.get("messages", [])]

        return {
            "messages": messages,
            "total_count": data.get("totalCount", 0),
            "current_page": data.get("currentPage", 1),
            "total_pages": data.get("totalPages", 1),
            "has_next": data.get("hasNext", False),
            "cache_hit": data.get("cacheHit", False),
        }

    def fetch_all(
        self,
        chat_type: int,
        peer_uid: str,
        filter: Optional[MessageFilter] = None,
        batch_size: int = 5000,
    ) -> Generator[List[Message], None, None]:
        """
        获取所有消息（生成器）

        Args:
            chat_type: 聊天类型
            peer_uid: 对方 UID 或群号
            filter: 消息筛选条件
            batch_size: 批量大小

        Yields:
            消息列表（每页）
        """
        page = 1
        while True:
            result = self.fetch(
                chat_type=chat_type,
                peer_uid=peer_uid,
                filter=filter,
                batch_size=batch_size,
                page=page,
                limit=100,
            )
            messages = result["messages"]
            if messages:
                yield messages

            if not result["has_next"]:
                break
            page += 1

    def export(
        self,
        chat_type: int,
        peer_uid: str,
        format: str = "JSON",
        filter: Optional[MessageFilter] = None,
        options: Optional[ExportOptions] = None,
        session_name: Optional[str] = None,
    ) -> ExportTask:
        """
        创建导出任务

        Args:
            chat_type: 聊天类型 (1=私聊, 2=群聊)
            peer_uid: 对方 UID 或群号
            format: 导出格式 (TXT, JSON, HTML, EXCEL)
            filter: 消息筛选条件
            options: 导出选项
            session_name: 会话名称（可选）

        Returns:
            导出任务
        """
        peer = {"chatType": chat_type, "peerUid": peer_uid}
        body: Dict[str, Any] = {
            "peer": peer,
            "format": format.upper(),
        }
        if filter:
            body["filter"] = filter.to_dict()
        if options:
            body["options"] = options.to_dict()
        if session_name:
            body["sessionName"] = session_name

        data = self._request("POST", "/api/messages/export", json_data=body)
        return ExportTask.from_dict(data)


class TasksAPI(BaseAPI):
    """任务 API"""

    def get_all(self) -> List[ExportTask]:
        """
        获取所有导出任务

        Returns:
            任务列表
        """
        data = self._request("GET", "/api/tasks")
        tasks_data = data.get("tasks", [])
        return [ExportTask.from_dict(t) for t in tasks_data]

    def get(self, task_id: str) -> ExportTask:
        """
        获取指定任务

        Args:
            task_id: 任务 ID

        Returns:
            任务详情
        """
        data = self._request("GET", f"/api/tasks/{task_id}")
        return ExportTask.from_dict(data)

    def delete(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        self._request("DELETE", f"/api/tasks/{task_id}")
        return True

    def delete_original_files(self, task_id: str) -> bool:
        """
        删除 ZIP 导出任务的原始文件

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        self._request("DELETE", f"/api/tasks/{task_id}/original-files")
        return True

    def wait_for_completion(
        self,
        task_id: str,
        timeout: float = 300,
        poll_interval: float = 2,
        on_progress: Optional[Callable[[ExportTask], None]] = None,
    ) -> ExportTask:
        """
        等待任务完成

        Args:
            task_id: 任务 ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            on_progress: 进度回调函数

        Returns:
            完成的任务

        Raises:
            TimeoutError: 超时
            APIError: 任务失败
        """
        start_time = time.time()
        while True:
            task = self.get(task_id)

            if on_progress:
                on_progress(task)

            if task.status == TaskStatus.COMPLETED:
                return task
            elif task.status == TaskStatus.FAILED:
                raise APIError(
                    message=f"任务失败: {task.error}",
                    code="TASK_FAILED",
                    details={"task_id": task_id, "error": task.error},
                )
            elif task.status == TaskStatus.CANCELLED:
                raise APIError(
                    message="任务已取消",
                    code="TASK_CANCELLED",
                    details={"task_id": task_id},
                )

            if time.time() - start_time > timeout:
                raise TimeoutError(f"等待任务完成超时: {task_id}")

            time.sleep(poll_interval)


class ScheduledExportsAPI(BaseAPI):
    """定时导出 API"""

    def create(self, config: ScheduledExportConfig) -> ScheduledExport:
        """
        创建定时导出任务

        Args:
            config: 定时导出配置

        Returns:
            创建的定时导出任务
        """
        data = self._request("POST", "/api/scheduled-exports", json_data=config.to_dict())
        return ScheduledExport.from_dict(data)

    def get_all(self) -> List[ScheduledExport]:
        """
        获取所有定时导出任务

        Returns:
            定时导出任务列表
        """
        data = self._request("GET", "/api/scheduled-exports")
        exports_data = data.get("scheduledExports", [])
        return [ScheduledExport.from_dict(e) for e in exports_data]

    def get(self, export_id: str) -> ScheduledExport:
        """
        获取指定定时导出任务

        Args:
            export_id: 任务 ID

        Returns:
            定时导出任务
        """
        data = self._request("GET", f"/api/scheduled-exports/{export_id}")
        return ScheduledExport.from_dict(data)

    def update(self, export_id: str, updates: Dict[str, Any]) -> ScheduledExport:
        """
        更新定时导出任务

        Args:
            export_id: 任务 ID
            updates: 更新内容

        Returns:
            更新后的任务
        """
        data = self._request("PUT", f"/api/scheduled-exports/{export_id}", json_data=updates)
        return ScheduledExport.from_dict(data)

    def delete(self, export_id: str) -> bool:
        """
        删除定时导出任务

        Args:
            export_id: 任务 ID

        Returns:
            是否成功
        """
        self._request("DELETE", f"/api/scheduled-exports/{export_id}")
        return True

    def trigger(self, export_id: str) -> Dict[str, Any]:
        """
        手动触发定时导出任务

        Args:
            export_id: 任务 ID

        Returns:
            触发结果
        """
        return self._request("POST", f"/api/scheduled-exports/{export_id}/trigger")

    def get_history(self, export_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取执行历史

        Args:
            export_id: 任务 ID
            limit: 返回数量限制

        Returns:
            执行历史列表
        """
        data = self._request(
            "GET",
            f"/api/scheduled-exports/{export_id}/history",
            params={"limit": limit},
        )
        return data.get("history", [])

    def enable(self, export_id: str) -> ScheduledExport:
        """启用定时导出任务"""
        return self.update(export_id, {"enabled": True})

    def disable(self, export_id: str) -> ScheduledExport:
        """禁用定时导出任务"""
        return self.update(export_id, {"enabled": False})


class StickerPacksAPI(BaseAPI):
    """表情包 API"""

    def get_all(self, types: Optional[List[str]] = None) -> List[StickerPack]:
        """
        获取所有表情包

        Args:
            types: 类型筛选 (favorite_emoji, market_pack, system_pack)

        Returns:
            表情包列表
        """
        params = {}
        if types:
            params["types"] = ",".join(types)

        data = self._request("GET", "/api/sticker-packs", params=params if params else None)
        packs_data = data.get("packs", [])
        return [StickerPack.from_dict(p) for p in packs_data]

    def export(self, pack_id: str) -> Dict[str, Any]:
        """
        导出指定表情包

        Args:
            pack_id: 表情包 ID

        Returns:
            导出结果
        """
        return self._request("POST", "/api/sticker-packs/export", json_data={"packId": pack_id})

    def export_all(self) -> Dict[str, Any]:
        """
        导出所有表情包

        Returns:
            导出结果
        """
        return self._request("POST", "/api/sticker-packs/export-all")

    def get_export_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取导出记录

        Args:
            limit: 返回数量限制

        Returns:
            导出记录列表
        """
        data = self._request("GET", "/api/sticker-packs/export-records", params={"limit": limit})
        return data.get("records", [])


class ExportFilesAPI(BaseAPI):
    """导出文件 API"""

    def get_all(self) -> List[ExportFile]:
        """
        获取所有导出文件

        Returns:
            导出文件列表
        """
        data = self._request("GET", "/api/exports/files")
        files_data = data.get("files", [])
        return [ExportFile.from_dict(f) for f in files_data]

    def get_info(self, file_name: str) -> ExportFile:
        """
        获取文件详细信息

        Args:
            file_name: 文件名

        Returns:
            文件信息
        """
        data = self._request("GET", f"/api/exports/files/{file_name}/info")
        return ExportFile.from_dict(data)

    def delete(self, file_name: str) -> bool:
        """
        删除导出文件

        Args:
            file_name: 文件名

        Returns:
            是否成功
        """
        self._request("DELETE", f"/api/exports/files/{file_name}")
        return True

    def get_preview_url(self, file_name: str) -> str:
        """
        获取文件预览 URL

        Args:
            file_name: 文件名

        Returns:
            预览 URL
        """
        return f"{self._client.base_url}/api/exports/files/{file_name}/preview"

    def get_download_url(self, file_name: str, is_scheduled: bool = False) -> str:
        """
        获取文件下载 URL

        Args:
            file_name: 文件名
            is_scheduled: 是否为定时导出文件

        Returns:
            下载 URL
        """
        prefix = "scheduled-downloads" if is_scheduled else "downloads"
        return f"{self._client.base_url}/{prefix}/{file_name}"


class SystemAPI(BaseAPI):
    """系统 API"""

    def get_info(self) -> SystemInfo:
        """
        获取系统信息

        Returns:
            系统信息
        """
        data = self._request("GET", "/api/system/info")
        return SystemInfo.from_dict(data)

    def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态

        Returns:
            系统状态
        """
        return self._request("GET", "/api/system/status")

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态
        """
        return self._client._request("GET", "/health")

    def get_security_status(self) -> Dict[str, Any]:
        """
        获取安全状态

        Returns:
            安全状态
        """
        return self._client._request("GET", "/security-status")


class NapCatQCE:
    """
    NapCat-QCE Python SDK 主客户端

    用于与 NapCat-QCE API 进行交互。

    Example:
        >>> client = NapCatQCE(token="your_token")
        >>> groups = client.groups.get_all()
        >>> for group in groups:
        ...     print(f"{group.group_name} ({group.group_code})")
    """

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 40653

    def __init__(
        self,
        token: Optional[str] = None,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        初始化客户端

        Args:
            token: 访问令牌
            host: 服务器地址
            port: 服务器端口
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证 SSL 证书
        """
        self.host = host
        self.port = port
        self.token = token
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.base_url = f"http://{host}:{port}"

        # 创建 session
        self._session = requests.Session()
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

        # 初始化各 API 模块
        self.groups = GroupsAPI(self)
        self.friends = FriendsAPI(self)
        self.users = UsersAPI(self)
        self.messages = MessagesAPI(self)
        self.tasks = TasksAPI(self)
        self.scheduled_exports = ScheduledExportsAPI(self)
        self.sticker_packs = StickerPacksAPI(self)
        self.export_files = ExportFilesAPI(self)
        self.system = SystemAPI(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            json_data: JSON 请求体
            **kwargs: 其他请求参数

        Returns:
            响应数据

        Raises:
            AuthenticationError: 认证失败
            ValidationError: 参数验证失败
            APIError: API 调用失败
            NetworkError: 网络错误
        """
        url = urljoin(self.base_url, endpoint)

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"无法连接到服务器: {self.base_url}") from e
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"请求超时: {url}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"请求失败: {e}") from e

        # 处理响应
        if response.status_code == 401:
            raise AuthenticationError("认证失败，请检查访问令牌")
        elif response.status_code == 403:
            raise AuthenticationError("访问被拒绝，令牌无效或已过期")

        try:
            data = response.json()
        except json.JSONDecodeError:
            if response.status_code >= 400:
                raise APIError(
                    message=f"服务器返回错误: {response.status_code}",
                    status_code=response.status_code,
                )
            return {}

        # 检查 API 响应
        if not data.get("success", True):
            error = data.get("error", {})
            error_type = error.get("type", "UNKNOWN_ERROR")
            error_message = error.get("message", "未知错误")
            error_code = error.get("context", {}).get("code", error_type)

            if error_type == "AUTH_ERROR":
                raise AuthenticationError(error_message, code=error_code)
            elif error_type == "VALIDATION_ERROR":
                raise ValidationError(error_message, code=error_code)
            elif error_code == "TASK_NOT_FOUND":
                raise TaskNotFoundError(error.get("context", {}).get("taskId", "unknown"))
            else:
                raise APIError(
                    message=error_message,
                    code=error_code,
                    status_code=response.status_code,
                    details=error,
                )

        return data.get("data", data)

    def authenticate(self, token: str) -> bool:
        """
        验证令牌

        Args:
            token: 访问令牌

        Returns:
            是否验证成功
        """
        try:
            response = self._session.post(
                f"{self.base_url}/auth",
                json={"token": token},
                timeout=self.timeout,
            )
            data = response.json()
            if data.get("success") and data.get("data", {}).get("authenticated"):
                self.token = token
                self._session.headers["Authorization"] = f"Bearer {token}"
                return True
            return False
        except Exception:
            return False

    def is_connected(self) -> bool:
        """
        检查是否已连接到服务器

        Returns:
            是否已连接
        """
        try:
            self.system.health_check()
            return True
        except Exception:
            return False

    def close(self):
        """关闭客户端连接"""
        self._session.close()

    def __enter__(self) -> "NapCatQCE":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self) -> str:
        return f"NapCatQCE(host={self.host!r}, port={self.port})"
