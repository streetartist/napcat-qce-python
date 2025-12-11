"""
NapCat-QCE Python SDK
=====================

一个用于与 NapCat-QCE (QQ聊天记录导出工具) API 交互的 Python 库。

基本用法:
    from napcat_qce import NapCatQCE

    client = NapCatQCE(token="your_access_token")

    # 获取群组列表
    groups = client.groups.get_all()

    # 导出聊天记录
    task = client.messages.export(
        chat_type=2,  # 群聊
        peer_uid="123456789",
        format="HTML"
    )

GitHub: https://github.com/shuakami/qq-chat-exporter
"""

__version__ = "1.0.0"
__author__ = "NapCat-QCE Contributors"

from .client import NapCatQCE
from .auto_token import (
    AutoTokenClient,
    connect,
    auto_discover_token,
    get_token_from_config,
    get_config_dir,
)
from .launcher import (
    NapCatQCELauncher,
    start_napcat_qce,
    run_with_napcat,
    find_napcat_qce_path,
    find_qq_path,
)
from .config import (
    ExportConfig,
    ConfigManager,
    get_config_manager,
    get_export_config,
    set_export_dir,
    set_export_format,
)
from .types import (
    # 枚举类型
    ChatType,
    ExportFormat,
    TaskStatus,
    ResourceType,
    ResourceStatus,
    ScheduleType,
    TimeRangeType,

    # 数据类型
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

    # 配置类型
    MessageFilter,
    ExportOptions,
    ScheduledExportConfig,
)
from .exceptions import (
    NapCatQCEError,
    AuthenticationError,
    ValidationError,
    APIError,
    NetworkError,
    TaskNotFoundError,
)

__all__ = [
    # 主客户端
    "NapCatQCE",
    "AutoTokenClient",
    "connect",
    "auto_discover_token",
    "get_token_from_config",
    "get_config_dir",

    # 启动器
    "NapCatQCELauncher",
    "start_napcat_qce",
    "run_with_napcat",
    "find_napcat_qce_path",
    "find_qq_path",

    # 配置管理
    "ExportConfig",
    "ConfigManager",
    "get_config_manager",
    "get_export_config",
    "set_export_dir",
    "set_export_format",

    # 枚举类型
    "ChatType",
    "ExportFormat",
    "TaskStatus",
    "ResourceType",
    "ResourceStatus",
    "ScheduleType",
    "TimeRangeType",

    # 数据类型
    "Group",
    "GroupMember",
    "Friend",
    "UserInfo",
    "Message",
    "ExportTask",
    "ScheduledExport",
    "StickerPack",
    "ExportFile",
    "SystemInfo",

    # 配置类型
    "MessageFilter",
    "ExportOptions",
    "ScheduledExportConfig",

    # 异常类型
    "NapCatQCEError",
    "AuthenticationError",
    "ValidationError",
    "APIError",
    "NetworkError",
    "TaskNotFoundError",
]
