# NapCat-QCE Python SDK

一个用于与 [NapCat-QCE](https://github.com/shuakami/qq-chat-exporter) (QQ聊天记录导出工具) API 交互的 Python 库。

## 功能特性

- 🚀 **完整 API 封装** - 支持所有 NapCat-QCE 功能
- 🔑 **自动令牌获取** - 无需手动复制令牌
- 🎮 **服务启动器** - 通过 Python 启动/停止 NapCat-QCE
- 📦 **类型提示** - 完整的类型注解，IDE 友好
- 🔄 **WebSocket 支持** - 实时事件监听
- ⏰ **定时导出** - 自动备份聊天记录
- 😀 **表情包导出** - 导出收藏的表情
- 📁 **批量导出** - 一键导出多个群/好友的记录
- ⚙️ **配置管理** - 自定义导出格式和保存位置

## 安装

```bash
pip install napcat-qce

# 完整安装（包含 WebSocket 支持）
pip install napcat-qce[websocket]

# 开发安装
pip install -e ".[dev]"
```

## 目录

- [快速开始](#快速开始)
- [连接方式](#连接方式)
- [启动器 - 自动启动服务](#启动器---自动启动服务)
- [配置管理](#配置管理)
- [批量导出](#批量导出)
- [API 详解](#api-详解)
  - [群组管理](#群组管理)
  - [好友管理](#好友管理)
  - [消息导出](#消息导出)
  - [任务管理](#任务管理)
  - [定时导出](#定时导出)
  - [表情包导出](#表情包导出)
  - [文件管理](#文件管理)
  - [WebSocket 实时监听](#websocket-实时监听)
- [API 参考](#api-参考)
- [示例文件](#示例文件)

---

## 快速开始

```python
from napcat_qce import connect

# 一行代码连接（自动获取令牌）
client = connect()

# 获取登录信息
info = client.system.get_info()
print(f"已登录: {info.self_nick} ({info.self_uin})")

# 获取群组列表
groups = client.groups.get_all()
print(f"共有 {len(groups)} 个群组")

# 导出聊天记录（一行搞定！）
task = client.export_group(groups[0].group_code, days=7)
print(f"导出完成: {task.message_count} 条消息")
```

---

## 连接方式

### 方式1: 自动连接（推荐）

```python
from napcat_qce import connect

# 自动从以下位置获取令牌:
#   1. 环境变量 NAPCAT_QCE_TOKEN
#   2. 本地配置文件 ~/.qq-chat-exporter/security.json
client = connect()
```

### 方式2: 连接远程服务器

```python
client = connect(host="192.168.1.100", port=40653)
```

### 方式3: 手动指定令牌

```python
from napcat_qce import NapCatQCE

client = NapCatQCE(token="your_access_token")
```

### 方式4: 从配置文件读取令牌

```python
from napcat_qce import NapCatQCE, get_token_from_config

token = get_token_from_config()
client = NapCatQCE(token=token)
```

### 方式5: 使用环境变量

```bash
export NAPCAT_QCE_TOKEN="your_token"
```

```python
client = connect()  # 自动读取环境变量
```

---

## 启动器 - 自动启动服务

无需手动启动 NapCat-QCE，通过 Python 自动管理服务生命周期。

### 使用上下文管理器（推荐）

```python
from napcat_qce import NapCatQCELauncher

with NapCatQCELauncher() as launcher:
    client = launcher.get_client()

    # 使用客户端...
    groups = client.groups.get_all()
    print(f"共有 {len(groups)} 个群组")

# 退出 with 块时自动停止服务
```

### 手动控制

```python
from napcat_qce import NapCatQCELauncher, start_napcat_qce

# 方式1: 使用启动器类
launcher = NapCatQCELauncher(
    napcat_path="D:/NapCat-QCE-Windows-x64",  # 可选，自动查找
    use_user_mode=True,  # 用户模式，无需管理员权限
)

# 设置回调
launcher.on_output(lambda line: print(f"[NapCat] {line}"))
launcher.on_ready(lambda token: print(f"令牌: {token}"))

# 启动
launcher.start(wait_for_ready=True, timeout=120)

# 获取客户端
client = launcher.get_client()

# ... 使用客户端 ...

# 停止
launcher.stop()

# 方式2: 快速启动函数
launcher = start_napcat_qce(wait_for_ready=True)
client = launcher.get_client()
# ...
launcher.stop()
```

### 执行单次任务

```python
from napcat_qce import run_with_napcat

def my_task(client):
    """自动启动服务，执行任务，然后停止"""
    groups = client.groups.get_all()
    for group in groups:
        print(f"- {group.group_name}")

run_with_napcat(my_task)
```

### 查找路径

```python
from napcat_qce import find_napcat_qce_path, find_qq_path

# 自动查找 NapCat-QCE 安装路径
napcat_path = find_napcat_qce_path()
print(f"NapCat-QCE: {napcat_path}")

# 自动查找 QQ 安装路径
qq_path = find_qq_path()
print(f"QQ: {qq_path}")
```

---

## 配置管理

### 设置导出目录和格式

```python
from napcat_qce import set_export_dir, set_export_format, get_export_config

# 设置导出目录
set_export_dir("D:/我的QQ聊天记录")

# 设置导出格式: HTML, JSON, TXT, EXCEL
set_export_format("HTML")

# 查看当前配置
config = get_export_config()
print(f"导出目录: {config.output_dir}")
print(f"导出格式: {config.format}")
print(f"包含资源: {config.include_resources}")
```

### 自定义导出配置

```python
from napcat_qce import ExportConfig

config = ExportConfig(
    format="JSON",
    output_dir="D:/备份/QQ",
    file_name_template="{type}_{name}_{date}",  # 支持变量
    include_resources=True,      # 下载图片/视频
    resource_folder="resources", # 资源文件夹名
    batch_size=5000,            # 每批处理消息数
    include_system_messages=True,
    include_recalled_messages=False,
    pretty_format=True,         # JSON 美化
    encoding="utf-8",
    export_as_zip=True,         # 打包为 ZIP
)

# 获取输出路径
output_path = config.get_output_path("我的群", "group")
print(f"输出路径: {output_path}")
```

### 使用配置管理器

```python
from napcat_qce import ConfigManager

manager = ConfigManager()

# 获取配置
config = manager.get_export_config()

# 修改配置
config.format = "JSON"
config.output_dir = "D:/导出"

# 保存配置
manager.save_export_config(config)

# 重置为默认
manager.reset_export_config()
```

---

## 批量导出

### 便捷方法（推荐）

```python
from napcat_qce import connect

client = connect()

# 导出单个群聊（最近7天）
task = client.export_group("123456789", days=7)
print(f"导出了 {task.message_count} 条消息")

# 导出单个私聊
task = client.export_friend("111222333", days=30)

# 批量导出多个目标
results = client.batch_export(
    targets=[
        {"type": "group", "id": "123456789"},
        {"type": "group", "id": "987654321"},
        {"type": "friend", "id": "111222333"},
    ],
    days=7,
    format="HTML",
    output_dir="D:/QQ聊天记录",  # 可选，指定输出目录
    on_progress=lambda id, task: print(f"  {task.session_name}: {task.message_count} 条"),
    on_error=lambda id, e: print(f"  {id}: 失败 - {e}"),
)

print(f"成功: {results['success']}, 失败: {results['failed']}")
print(f"消息总数: {results['total_messages']} 条")
```

### 使用时间筛选器

```python
from napcat_qce import MessageFilter

# 最近7天
filter = MessageFilter.last_days(7)

# 最近24小时
filter = MessageFilter.last_hours(24)

# 自定义时间范围
from datetime import datetime
filter = MessageFilter(
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 12, 31),
)

# 使用筛选器导出
task = client.export_group("123456789", filter=filter)
```

### 更多示例

参见 `examples/batch_export.py` 和 `examples/quick_export.py`。

---

## API 详解

### 群组管理

```python
# 获取所有群组
groups = client.groups.get_all()
for group in groups:
    print(f"{group.group_name} ({group.group_code})")
    print(f"  成员数: {group.member_count}/{group.max_member}")

# 获取群组详情
detail = client.groups.get("123456789")

# 获取群成员
members = client.groups.get_members("123456789")
for member in members:
    role = ["成员", "管理员", "群主"][member.role]
    print(f"  {member.nick} - {role}")

# 强制刷新缓存
groups = client.groups.get_all(force_refresh=True)
```

### 好友管理

```python
# 获取所有好友
friends = client.friends.get_all()
for friend in friends:
    name = friend.remark or friend.nick
    status = "在线" if friend.is_online else "离线"
    print(f"{name} ({friend.uin}) - {status}")

# 获取好友详情
detail = client.friends.get("u_xxxx")

# 获取用户信息
user = client.users.get("u_xxxx")
print(f"昵称: {user.nick}")
print(f"等级: {user.qq_level}")
```

### 消息导出

```python
from napcat_qce import MessageFilter, ExportOptions, ChatType

# 创建筛选条件
filter = MessageFilter(
    start_time=1704067200000,  # 开始时间（毫秒时间戳）
    end_time=1735689600000,    # 结束时间
    sender_uids=["u_xxx"],     # 指定发送者（可选）
    keywords=["关键词"],        # 关键词筛选（可选）
    include_recalled=False,    # 包含撤回消息
    include_system=True,       # 包含系统消息
)

# 创建导出选项
options = ExportOptions(
    batch_size=5000,
    include_resource_links=True,
    include_system_messages=True,
    pretty_format=True,
    export_as_zip=False,
)

# 导出群聊
task = client.messages.export(
    chat_type=ChatType.GROUP.value,  # 2
    peer_uid="123456789",
    format="HTML",  # HTML, JSON, TXT, EXCEL
    filter=filter,
    options=options,
    session_name="我的群聊",
)

print(f"任务ID: {task.id}")

# 等待完成（带进度回调）
result = client.tasks.wait_for_completion(
    task.id,
    timeout=600,
    poll_interval=2,
    on_progress=lambda t: print(f"\r进度: {t.progress}%", end=""),
)

print(f"\n导出完成!")
print(f"消息数: {result.message_count}")
print(f"文件名: {result.file_name}")
print(f"下载地址: {result.download_url}")
```

### 获取消息（不导出）

```python
# 分页获取消息
result = client.messages.fetch(
    chat_type=2,
    peer_uid="123456789",
    page=1,
    limit=50,
)

print(f"总消息数: {result['total_count']}")
print(f"当前页: {result['current_page']}/{result['total_pages']}")

for msg in result["messages"]:
    print(f"[{msg.sender_name}] {msg.msg_id}")

# 使用生成器获取所有消息
for messages in client.messages.fetch_all(chat_type=2, peer_uid="123456789"):
    for msg in messages:
        # 处理消息
        pass
```

### 任务管理

```python
# 获取所有任务
tasks = client.tasks.get_all()
for task in tasks:
    print(f"{task.session_name}: {task.status.value}")

# 获取指定任务
task = client.tasks.get("task_id")

# 删除任务
client.tasks.delete("task_id")

# 删除 ZIP 任务的原始文件
client.tasks.delete_original_files("task_id")

# 等待任务完成
result = client.tasks.wait_for_completion(
    "task_id",
    timeout=300,
    on_progress=lambda t: print(f"进度: {t.progress}%"),
)
```

### 定时导出

```python
from napcat_qce import (
    ScheduledExportConfig,
    Peer,
    ScheduleType,
    TimeRangeType,
    ExportFormat,
)

# 创建定时导出配置
config = ScheduledExportConfig(
    name="每日备份-我的群聊",
    peer=Peer(chat_type=2, peer_uid="123456789"),
    schedule_type=ScheduleType.DAILY,    # DAILY, WEEKLY, MONTHLY, CUSTOM
    execute_time="06:00",                # 执行时间
    time_range_type=TimeRangeType.YESTERDAY,  # 导出昨天的消息
    format=ExportFormat.HTML,
    enabled=True,
)

# 创建定时任务
scheduled = client.scheduled_exports.create(config)
print(f"任务ID: {scheduled.id}")
print(f"下次执行: {scheduled.next_run}")

# 获取所有定时任务
all_scheduled = client.scheduled_exports.get_all()

# 更新任务
client.scheduled_exports.update(scheduled.id, {"enabled": False})

# 启用/禁用
client.scheduled_exports.enable(scheduled.id)
client.scheduled_exports.disable(scheduled.id)

# 手动触发执行
client.scheduled_exports.trigger(scheduled.id)

# 获取执行历史
history = client.scheduled_exports.get_history(scheduled.id, limit=10)

# 删除任务
client.scheduled_exports.delete(scheduled.id)
```

### 表情包导出

```python
# 获取所有表情包
packs = client.sticker_packs.get_all()
for pack in packs:
    print(f"{pack.pack_name}: {pack.sticker_count} 个表情")

# 按类型筛选
# 类型: favorite_emoji(收藏), market_pack(商店), system_pack(系统)
favorite = client.sticker_packs.get_all(types=["favorite_emoji"])

# 导出单个表情包
result = client.sticker_packs.export(pack.pack_id)
print(f"导出路径: {result.get('exportPath')}")

# 导出所有表情包
result = client.sticker_packs.export_all()
print(f"导出了 {result.get('packCount')} 个表情包")

# 获取导出记录
records = client.sticker_packs.get_export_records(limit=50)
```

### 文件管理

```python
# 获取所有导出文件
files = client.export_files.get_all()
for f in files:
    print(f"{f.display_name}")
    print(f"  格式: {f.format}")
    print(f"  消息数: {f.message_count}")
    print(f"  大小: {f.size} bytes")

# 获取文件信息
info = client.export_files.get_info("filename.html")

# 获取预览/下载链接
preview_url = client.export_files.get_preview_url("filename.html")
download_url = client.export_files.get_download_url("filename.html")

# 删除文件
client.export_files.delete("filename.html")
```

### WebSocket 实时监听

```python
from napcat_qce.websocket import WebSocketClient, ExportProgressMonitor

# 方式1: WebSocketClient
ws = WebSocketClient(host="localhost", port=40653)

# 注册事件处理器
ws.on_export_progress(lambda data: print(f"进度: {data['progress']}%"))
ws.on_export_complete(lambda data: print(f"完成: {data['fileName']}"))
ws.on_export_error(lambda data: print(f"错误: {data['error']}"))
ws.on_connected(lambda data: print("已连接"))
ws.on_disconnected(lambda data: print("已断开"))

# 连接
ws.connect(blocking=False)  # 非阻塞

# ... 执行导出任务 ...

# 断开
ws.disconnect()

# 方式2: ExportProgressMonitor（更简单）
with ExportProgressMonitor() as monitor:
    task = client.messages.export(...)

    result = monitor.wait_for_task(
        task.id,
        timeout=300,
        on_progress=lambda s: print(f"进度: {s['progress']}%"),
    )
```

### 系统信息

```python
# 获取系统信息
info = client.system.get_info()
print(f"版本: {info.version}")
print(f"在线: {info.online}")
print(f"昵称: {info.self_nick}")
print(f"QQ号: {info.self_uin}")

# 获取系统状态
status = client.system.get_status()

# 健康检查
health = client.system.health_check()

# 安全状态
security = client.system.get_security_status()
```

---

## API 参考

### 主客户端 `NapCatQCE`

| 属性 | 类型 | 描述 |
|------|------|------|
| `groups` | `GroupsAPI` | 群组管理 |
| `friends` | `FriendsAPI` | 好友管理 |
| `users` | `UsersAPI` | 用户信息 |
| `messages` | `MessagesAPI` | 消息获取和导出 |
| `tasks` | `TasksAPI` | 导出任务管理 |
| `scheduled_exports` | `ScheduledExportsAPI` | 定时导出管理 |
| `sticker_packs` | `StickerPacksAPI` | 表情包管理 |
| `export_files` | `ExportFilesAPI` | 导出文件管理 |
| `system` | `SystemAPI` | 系统信息 |

### 便捷导出方法（NapCatQCE 客户端）

| 方法 | 描述 |
|------|------|
| `export_group(group_id, days=7)` | 快速导出群聊记录 |
| `export_friend(friend_id, days=7)` | 快速导出私聊记录 |
| `batch_export(targets, days=7)` | 批量导出多个目标 |
| `messages.quick_export(...)` | 创建导出任务并等待完成 |

### MessageFilter 便捷方法

| 方法 | 描述 |
|------|------|
| `MessageFilter.last_days(n)` | 创建最近N天的筛选器 |
| `MessageFilter.last_hours(n)` | 创建最近N小时的筛选器 |

### 便捷函数

| 函数 | 描述 |
|------|------|
| `connect()` | 自动获取令牌并连接 |
| `get_token_from_config()` | 从配置文件读取令牌 |
| `auto_discover_token()` | 自动发现令牌 |
| `set_export_dir()` | 设置导出目录 |
| `set_export_format()` | 设置导出格式 |
| `get_export_config()` | 获取导出配置 |

### 启动器

| 类/函数 | 描述 |
|---------|------|
| `NapCatQCELauncher` | 服务启动器类 |
| `start_napcat_qce()` | 快速启动函数 |
| `run_with_napcat()` | 执行单次任务 |
| `find_napcat_qce_path()` | 查找 NapCat-QCE 路径 |
| `find_qq_path()` | 查找 QQ 路径 |

### 枚举类型

```python
from napcat_qce import (
    ChatType,        # PRIVATE=1, GROUP=2, TEMP=3
    ExportFormat,    # TXT, JSON, HTML, EXCEL
    TaskStatus,      # PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    ScheduleType,    # DAILY, WEEKLY, MONTHLY, CUSTOM
    TimeRangeType,   # YESTERDAY, LAST_WEEK, LAST_MONTH, LAST_7_DAYS, LAST_30_DAYS, CUSTOM
    ResourceType,    # IMAGE, VIDEO, AUDIO, FILE
    ResourceStatus,  # PENDING, DOWNLOADING, DOWNLOADED, FAILED, CORRUPTED, SKIPPED
)
```

### 数据类型

```python
from napcat_qce import (
    Group,           # 群组信息
    GroupMember,     # 群成员信息
    Friend,          # 好友信息
    UserInfo,        # 用户详细信息
    Message,         # 消息
    ExportTask,      # 导出任务
    ScheduledExport, # 定时导出任务
    StickerPack,     # 表情包
    ExportFile,      # 导出文件
    SystemInfo,      # 系统信息
)
```

### 配置类型

```python
from napcat_qce import (
    MessageFilter,         # 消息筛选条件
    ExportOptions,         # 导出选项
    ExportConfig,          # 导出配置
    ScheduledExportConfig, # 定时导出配置
    Peer,                  # 聊天对象
)
```

### 异常类型

```python
from napcat_qce import (
    NapCatQCEError,       # 基础异常
    AuthenticationError,   # 认证失败
    ValidationError,       # 参数验证失败
    APIError,             # API 调用失败
    NetworkError,         # 网络错误
    TaskNotFoundError,    # 任务不存在
)
```

---

## 示例文件

| 文件 | 描述 |
|------|------|
| `examples/basic_usage.py` | 基本用法示例 |
| `examples/export_chat.py` | 导出聊天记录示例 |
| `examples/scheduled_export.py` | 定时导出示例 |
| `examples/websocket_monitor.py` | WebSocket 监控示例 |
| `examples/launcher_example.py` | 启动器和配置示例 |
| `examples/batch_export.py` | 批量导出工具 |
| `examples/quick_export.py` | 快速导出脚本 |

---

## 环境变量

| 变量 | 描述 |
|------|------|
| `NAPCAT_QCE_TOKEN` | 访问令牌 |
| `NAPCAT_QCE_PATH` | NapCat-QCE 安装路径 |

---

## 许可证

GPL-3.0 License

## 相关项目

- [qq-chat-exporter](https://github.com/shuakami/qq-chat-exporter) - QQ聊天记录导出工具
- [NapCat](https://napneko.github.io/) - QQ 机器人框架
