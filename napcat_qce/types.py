"""
NapCat-QCE 类型定义
==================

包含所有 API 使用的数据类型、枚举和配置类。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# 枚举类型
# ============================================================================

class ChatType(Enum):
    """聊天类型"""
    PRIVATE = 1  # 私聊
    GROUP = 2    # 群聊
    TEMP = 3     # 临时会话


class ExportFormat(Enum):
    """导出格式"""
    TXT = "txt"
    JSON = "json"
    HTML = "html"
    EXCEL = "excel"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class ResourceType(Enum):
    """资源类型"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"


class ResourceStatus(Enum):
    """资源状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    SKIPPED = "skipped"


class ScheduleType(Enum):
    """定时类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class TimeRangeType(Enum):
    """时间范围类型"""
    YESTERDAY = "yesterday"
    LAST_WEEK = "last-week"
    LAST_MONTH = "last-month"
    LAST_7_DAYS = "last-7-days"
    LAST_30_DAYS = "last-30-days"
    CUSTOM = "custom"


class StickerPackType(Enum):
    """表情包类型"""
    FAVORITE_EMOJI = "favorite_emoji"  # 收藏表情
    MARKET_PACK = "market_pack"        # 市场表情包
    SYSTEM_PACK = "system_pack"        # 系统表情包


# ============================================================================
# 数据类型
# ============================================================================

@dataclass
class Group:
    """群组信息"""
    group_code: str
    group_name: str
    member_count: int
    max_member: int = 0
    remark: Optional[str] = None
    avatar_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Group":
        return cls(
            group_code=str(data.get("groupCode", "")),
            group_name=data.get("groupName", ""),
            member_count=data.get("memberCount", 0),
            max_member=data.get("maxMember", 0),
            remark=data.get("remark"),
            avatar_url=data.get("avatarUrl"),
        )


@dataclass
class GroupMember:
    """群成员信息"""
    uid: str
    uin: str
    nick: str
    card_name: Optional[str] = None
    role: int = 0  # 0=普通成员, 1=管理员, 2=群主
    join_time: Optional[int] = None
    last_speak_time: Optional[int] = None
    avatar_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroupMember":
        return cls(
            uid=data.get("uid", ""),
            uin=str(data.get("uin", "")),
            nick=data.get("nick", ""),
            card_name=data.get("cardName"),
            role=data.get("role", 0),
            join_time=data.get("joinTime"),
            last_speak_time=data.get("lastSpeakTime"),
            avatar_url=data.get("avatarUrl"),
        )


@dataclass
class Friend:
    """好友信息"""
    uid: str
    uin: str
    nick: str
    remark: Optional[str] = None
    avatar_url: Optional[str] = None
    is_online: bool = False
    status: int = 0
    category_id: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Friend":
        return cls(
            uid=data.get("uid", ""),
            uin=str(data.get("uin", "")),
            nick=data.get("nick", ""),
            remark=data.get("remark"),
            avatar_url=data.get("avatarUrl"),
            is_online=data.get("isOnline", False),
            status=data.get("status", 0),
            category_id=data.get("categoryId", 1),
        )


@dataclass
class UserInfo:
    """用户详细信息"""
    uid: str
    uin: str
    nick: str
    avatar_url: Optional[str] = None
    long_nick: Optional[str] = None
    sex: Optional[int] = None
    age: Optional[int] = None
    qq_level: Optional[int] = None
    vip_flag: bool = False
    svip_flag: bool = False
    vip_level: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserInfo":
        return cls(
            uid=data.get("uid", ""),
            uin=str(data.get("uin", "")),
            nick=data.get("nick", ""),
            avatar_url=data.get("avatarUrl"),
            long_nick=data.get("longNick"),
            sex=data.get("sex"),
            age=data.get("age"),
            qq_level=data.get("qqLevel"),
            vip_flag=data.get("vipFlag", False),
            svip_flag=data.get("svipFlag", False),
            vip_level=data.get("vipLevel", 0),
        )


@dataclass
class MessageElement:
    """消息元素"""
    type: str
    content: Any
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class Message:
    """消息"""
    msg_id: str
    msg_seq: str
    msg_time: int
    sender_uid: str
    sender_uin: Optional[str] = None
    sender_name: Optional[str] = None
    sender_member_name: Optional[str] = None  # 群昵称
    elements: List[MessageElement] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        elements = []
        for elem in data.get("elements", []):
            elements.append(MessageElement(
                type=elem.get("elementType", "unknown"),
                content=elem,
                raw_data=elem,
            ))

        return cls(
            msg_id=data.get("msgId", ""),
            msg_seq=data.get("msgSeq", ""),
            msg_time=int(data.get("msgTime", 0)),
            sender_uid=data.get("senderUid", ""),
            sender_uin=data.get("senderUin"),
            sender_name=data.get("sendNickName"),
            sender_member_name=data.get("sendMemberName"),
            elements=elements,
            raw_data=data,
        )


@dataclass
class Peer:
    """聊天对象"""
    chat_type: int
    peer_uid: str
    guild_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "chatType": self.chat_type,
            "peerUid": self.peer_uid,
        }
        if self.guild_id:
            result["guildId"] = self.guild_id
        return result


@dataclass
class ExportTask:
    """导出任务"""
    id: str
    peer: Peer
    session_name: str
    status: TaskStatus
    progress: int
    format: str
    message_count: int = 0
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportTask":
        peer_data = data.get("peer", {})
        peer = Peer(
            chat_type=peer_data.get("chatType", 1),
            peer_uid=peer_data.get("peerUid", ""),
        )

        status_str = data.get("status", "pending")
        try:
            status = TaskStatus(status_str)
        except ValueError:
            status = TaskStatus.PENDING

        # 尝试多个可能的字段名
        task_id = data.get("id") or data.get("taskId") or data.get("task_id") or ""

        return cls(
            id=task_id,
            peer=peer,
            session_name=data.get("sessionName", ""),
            status=status,
            progress=data.get("progress", 0),
            format=data.get("format", "JSON"),
            message_count=data.get("messageCount", 0),
            file_name=data.get("fileName"),
            file_path=data.get("filePath"),
            download_url=data.get("downloadUrl"),
            created_at=data.get("createdAt"),
            completed_at=data.get("completedAt"),
            error=data.get("error"),
            start_time=data.get("startTime"),
            end_time=data.get("endTime"),
        )


@dataclass
class ScheduledExport:
    """定时导出任务"""
    id: str
    name: str
    peer: Peer
    enabled: bool
    schedule_type: ScheduleType
    execute_time: str
    time_range_type: TimeRangeType
    format: str
    cron_expression: Optional[str] = None
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledExport":
        peer_data = data.get("peer", {})
        peer = Peer(
            chat_type=peer_data.get("chatType", 1),
            peer_uid=peer_data.get("peerUid", ""),
        )

        try:
            schedule_type = ScheduleType(data.get("scheduleType", "daily"))
        except ValueError:
            schedule_type = ScheduleType.DAILY

        try:
            time_range_type = TimeRangeType(data.get("timeRangeType", "yesterday"))
        except ValueError:
            time_range_type = TimeRangeType.YESTERDAY

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            peer=peer,
            enabled=data.get("enabled", True),
            schedule_type=schedule_type,
            execute_time=data.get("executeTime", ""),
            time_range_type=time_range_type,
            format=data.get("format", "HTML"),
            cron_expression=data.get("cronExpression"),
            next_run=data.get("nextRun"),
            last_run=data.get("lastRun"),
            options=data.get("options", {}),
        )


@dataclass
class StickerPack:
    """表情包"""
    pack_id: str
    pack_name: str
    pack_type: StickerPackType
    sticker_count: int
    description: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StickerPack":
        try:
            pack_type = StickerPackType(data.get("packType", "favorite_emoji"))
        except ValueError:
            pack_type = StickerPackType.FAVORITE_EMOJI

        return cls(
            pack_id=data.get("packId", ""),
            pack_name=data.get("packName", ""),
            pack_type=pack_type,
            sticker_count=data.get("stickerCount", 0),
            description=data.get("description"),
            raw_data=data.get("rawData"),
        )


@dataclass
class ExportFile:
    """导出文件"""
    file_name: str
    file_path: str
    relative_path: str
    size: int
    create_time: str
    modify_time: str
    chat_type: str
    chat_id: str
    display_name: Optional[str] = None
    message_count: Optional[int] = None
    format: str = "HTML"
    is_scheduled: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportFile":
        return cls(
            file_name=data.get("fileName", ""),
            file_path=data.get("filePath", ""),
            relative_path=data.get("relativePath", ""),
            size=data.get("size", 0),
            create_time=data.get("createTime", ""),
            modify_time=data.get("modifyTime", ""),
            chat_type=data.get("chatType", ""),
            chat_id=data.get("chatId", ""),
            display_name=data.get("displayName"),
            message_count=data.get("messageCount"),
            format=data.get("format", "HTML"),
            is_scheduled=data.get("isScheduled", False),
        )


@dataclass
class SystemInfo:
    """系统信息"""
    version: str
    online: bool
    self_uid: str
    self_uin: str
    self_nick: str
    avatar_url: Optional[str] = None
    node_version: Optional[str] = None
    platform: Optional[str] = None
    uptime: float = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemInfo":
        napcat = data.get("napcat", {})
        self_info = napcat.get("selfInfo", {})
        runtime = data.get("runtime", {})

        return cls(
            version=data.get("version", ""),
            online=napcat.get("online", False),
            self_uid=self_info.get("uid", ""),
            self_uin=str(self_info.get("uin", "")),
            self_nick=self_info.get("nick", ""),
            avatar_url=self_info.get("avatarUrl"),
            node_version=runtime.get("nodeVersion"),
            platform=runtime.get("platform"),
            uptime=runtime.get("uptime", 0),
        )


# ============================================================================
# 配置类型
# ============================================================================

@dataclass
class MessageFilter:
    """消息筛选条件"""
    start_time: Optional[int] = None  # Unix时间戳（毫秒）
    end_time: Optional[int] = None    # Unix时间戳（毫秒）
    sender_uids: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    include_recalled: bool = False
    include_system: bool = True
    filter_pure_image_messages: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.start_time is not None:
            result["startTime"] = self.start_time
        if self.end_time is not None:
            result["endTime"] = self.end_time
        if self.sender_uids:
            result["senderUids"] = self.sender_uids
        if self.keywords:
            result["keywords"] = self.keywords
        result["includeRecalled"] = self.include_recalled
        result["includeSystem"] = self.include_system
        result["filterPureImageMessages"] = self.filter_pure_image_messages
        return result


@dataclass
class ExportOptions:
    """导出选项"""
    batch_size: int = 5000
    include_resource_links: bool = True
    include_system_messages: bool = True
    filter_pure_image_messages: bool = False
    pretty_format: bool = True
    export_as_zip: bool = False
    output_dir: Optional[str] = None  # 输出目录

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "batchSize": self.batch_size,
            "includeResourceLinks": self.include_resource_links,
            "includeSystemMessages": self.include_system_messages,
            "filterPureImageMessages": self.filter_pure_image_messages,
            "prettyFormat": self.pretty_format,
            "exportAsZip": self.export_as_zip,
        }
        if self.output_dir:
            result["outputDir"] = self.output_dir
        return result


@dataclass
class ScheduledExportConfig:
    """定时导出配置"""
    name: str
    peer: Peer
    schedule_type: ScheduleType
    execute_time: str
    time_range_type: TimeRangeType
    format: ExportFormat = ExportFormat.HTML
    enabled: bool = True
    cron_expression: Optional[str] = None
    options: Optional[ExportOptions] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "peer": self.peer.to_dict(),
            "scheduleType": self.schedule_type.value,
            "executeTime": self.execute_time,
            "timeRangeType": self.time_range_type.value,
            "format": self.format.value.upper(),
            "enabled": self.enabled,
        }
        if self.cron_expression:
            result["cronExpression"] = self.cron_expression
        if self.options:
            result["options"] = self.options.to_dict()
        return result
