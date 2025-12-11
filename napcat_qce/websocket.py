"""
NapCat-QCE WebSocket 客户端
==========================

提供实时事件监听和流式搜索功能。
"""

import json
import threading
import time
from typing import Optional, Dict, Any, Callable, List
from enum import Enum

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False


class WebSocketEventType(Enum):
    """WebSocket 事件类型"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPORT_PROGRESS = "export_progress"
    EXPORT_COMPLETE = "export_complete"
    EXPORT_ERROR = "export_error"
    SEARCH_RESULT = "search_result"
    SEARCH_PROGRESS = "search_progress"
    SEARCH_COMPLETE = "search_complete"
    SEARCH_ERROR = "search_error"
    MERGE_PROGRESS = "merge-progress"
    NOTIFICATION = "notification"
    ERROR = "error"


class WebSocketClient:
    """
    NapCat-QCE WebSocket 客户端

    用于接收实时事件通知，如导出进度、搜索结果等。

    Example:
        >>> ws_client = WebSocketClient(host="localhost", port=40653)
        >>> ws_client.on_export_progress(lambda data: print(f"进度: {data['progress']}%"))
        >>> ws_client.connect()
        >>> # ... 执行导出任务 ...
        >>> ws_client.disconnect()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 40653,
        token: Optional[str] = None,
        auto_reconnect: bool = True,
        reconnect_interval: float = 5.0,
    ):
        """
        初始化 WebSocket 客户端

        Args:
            host: 服务器地址
            port: 服务器端口
            token: 访问令牌（可选）
            auto_reconnect: 是否自动重连
            reconnect_interval: 重连间隔（秒）
        """
        if not HAS_WEBSOCKET:
            raise ImportError(
                "websocket-client 库未安装。请运行: pip install websocket-client"
            )

        self.host = host
        self.port = port
        self.token = token
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval

        self.ws_url = f"ws://{host}:{port}"
        self._ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._connected = False
        self._should_reconnect = True

        # 事件处理器
        self._handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def on(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> "WebSocketClient":
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数

        Returns:
            self（支持链式调用）
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        return self

    def off(self, event_type: str, handler: Optional[Callable] = None) -> "WebSocketClient":
        """
        移除事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数（为 None 时移除所有）

        Returns:
            self
        """
        if event_type in self._handlers:
            if handler is None:
                self._handlers[event_type] = []
            else:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]
        return self

    def on_export_progress(self, handler: Callable[[Dict[str, Any]], None]) -> "WebSocketClient":
        """注册导出进度处理器"""
        return self.on("export_progress", handler)

    def on_export_complete(self, handler: Callable[[Dict[str, Any]], None]) -> "WebSocketClient":
        """注册导出完成处理器"""
        return self.on("export_complete", handler)

    def on_export_error(self, handler: Callable[[Dict[str, Any]], None]) -> "WebSocketClient":
        """注册导出错误处理器"""
        return self.on("export_error", handler)

    def on_connected(self, handler: Callable[[Dict[str, Any]], None]) -> "WebSocketClient":
        """注册连接成功处理器"""
        return self.on("connected", handler)

    def on_disconnected(self, handler: Callable[[Dict[str, Any]], None]) -> "WebSocketClient":
        """注册断开连接处理器"""
        return self.on("disconnected", handler)

    def _emit(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"[WebSocket] 事件处理器错误 ({event_type}): {e}")

    def _on_message(self, ws, message: str):
        """处理收到的消息"""
        try:
            data = json.loads(message)
            event_type = data.get("type", "unknown")
            event_data = data.get("data", {})

            # 添加原始消息
            event_data["_raw"] = data

            self._emit(event_type, event_data)
        except json.JSONDecodeError as e:
            print(f"[WebSocket] 消息解析失败: {e}")

    def _on_error(self, ws, error):
        """处理错误"""
        print(f"[WebSocket] 错误: {error}")
        self._emit("error", {"error": str(error)})

    def _on_close(self, ws, close_status_code, close_msg):
        """处理连接关闭"""
        self._connected = False
        self._emit("disconnected", {
            "status_code": close_status_code,
            "message": close_msg,
        })

        # 自动重连
        if self.auto_reconnect and self._should_reconnect:
            print(f"[WebSocket] 将在 {self.reconnect_interval} 秒后重连...")
            time.sleep(self.reconnect_interval)
            if self._should_reconnect:
                self._connect_internal()

    def _on_open(self, ws):
        """处理连接打开"""
        self._connected = True
        print(f"[WebSocket] 已连接到 {self.ws_url}")

    def _connect_internal(self):
        """内部连接方法"""
        self._ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )
        self._ws.run_forever()

    def connect(self, blocking: bool = False):
        """
        连接到 WebSocket 服务器

        Args:
            blocking: 是否阻塞当前线程
        """
        self._should_reconnect = True

        if blocking:
            self._connect_internal()
        else:
            self._thread = threading.Thread(target=self._connect_internal, daemon=True)
            self._thread.start()
            # 等待连接建立
            time.sleep(0.5)

    def disconnect(self):
        """断开连接"""
        self._should_reconnect = False
        if self._ws:
            self._ws.close()
            self._ws = None
        self._connected = False

    def send(self, message: Dict[str, Any]):
        """
        发送消息

        Args:
            message: 消息内容
        """
        if self._ws and self._connected:
            self._ws.send(json.dumps(message))
        else:
            raise RuntimeError("WebSocket 未连接")

    def start_stream_search(
        self,
        chat_type: int,
        peer_uid: str,
        query: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> str:
        """
        启动流式搜索

        Args:
            chat_type: 聊天类型
            peer_uid: 对方 UID
            query: 搜索关键词
            start_time: 开始时间（毫秒时间戳）
            end_time: 结束时间（毫秒时间戳）

        Returns:
            搜索 ID
        """
        import uuid
        search_id = str(uuid.uuid4())

        message = {
            "type": "start_stream_search",
            "data": {
                "searchId": search_id,
                "peer": {
                    "chatType": chat_type,
                    "peerUid": peer_uid,
                },
                "searchQuery": query,
                "filter": {},
            },
        }

        if start_time is not None:
            message["data"]["filter"]["startTime"] = start_time
        if end_time is not None:
            message["data"]["filter"]["endTime"] = end_time

        self.send(message)
        return search_id

    def cancel_search(self, search_id: str):
        """
        取消搜索

        Args:
            search_id: 搜索 ID
        """
        self.send({
            "type": "cancel_search",
            "data": {"searchId": search_id},
        })

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    def __enter__(self) -> "WebSocketClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class ExportProgressMonitor:
    """
    导出进度监控器

    简化的进度监控工具，用于跟踪导出任务进度。

    Example:
        >>> monitor = ExportProgressMonitor(host="localhost", port=40653)
        >>> monitor.start()
        >>> # 创建导出任务...
        >>> task = monitor.wait_for_task("task_id", timeout=300)
        >>> print(f"导出完成: {task['messageCount']} 条消息")
        >>> monitor.stop()
    """

    def __init__(self, host: str = "localhost", port: int = 40653):
        self._ws_client = WebSocketClient(host=host, port=port, auto_reconnect=True)
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._task_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

        # 注册处理器
        self._ws_client.on_export_progress(self._handle_progress)
        self._ws_client.on_export_complete(self._handle_complete)
        self._ws_client.on_export_error(self._handle_error)

    def _handle_progress(self, data: Dict[str, Any]):
        task_id = data.get("taskId")
        if task_id:
            with self._lock:
                self._tasks[task_id] = {
                    "status": "running",
                    "progress": data.get("progress", 0),
                    "message": data.get("message", ""),
                    "message_count": data.get("messageCount", 0),
                }

    def _handle_complete(self, data: Dict[str, Any]):
        task_id = data.get("taskId")
        if task_id:
            with self._lock:
                self._tasks[task_id] = {
                    "status": "completed",
                    "progress": 100,
                    "message": "导出完成",
                    "message_count": data.get("messageCount", 0),
                    "file_name": data.get("fileName"),
                    "file_path": data.get("filePath"),
                    "download_url": data.get("downloadUrl"),
                }
                if task_id in self._task_events:
                    self._task_events[task_id].set()

    def _handle_error(self, data: Dict[str, Any]):
        task_id = data.get("taskId")
        if task_id:
            with self._lock:
                self._tasks[task_id] = {
                    "status": "failed",
                    "error": data.get("error", "未知错误"),
                }
                if task_id in self._task_events:
                    self._task_events[task_id].set()

    def start(self):
        """启动监控"""
        self._ws_client.connect()

    def stop(self):
        """停止监控"""
        self._ws_client.disconnect()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self._lock:
            return self._tasks.get(task_id)

    def wait_for_task(
        self,
        task_id: str,
        timeout: float = 300,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        等待任务完成

        Args:
            task_id: 任务 ID
            timeout: 超时时间（秒）
            on_progress: 进度回调

        Returns:
            任务最终状态

        Raises:
            TimeoutError: 超时
        """
        event = threading.Event()
        with self._lock:
            self._task_events[task_id] = event

        # 进度轮询
        if on_progress:
            def poll_progress():
                while not event.is_set():
                    status = self.get_task_status(task_id)
                    if status:
                        on_progress(status)
                    time.sleep(1)

            poll_thread = threading.Thread(target=poll_progress, daemon=True)
            poll_thread.start()

        # 等待完成
        if not event.wait(timeout):
            raise TimeoutError(f"等待任务 {task_id} 超时")

        with self._lock:
            del self._task_events[task_id]
            return self._tasks.get(task_id, {"status": "unknown"})

    def __enter__(self) -> "ExportProgressMonitor":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
