"""
NapCat-QCE Python SDK 批量导出示例
================================

自动启动 NapCat-QCE 并导出指定 QQ 号列表的聊天记录。
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

from napcat_qce import (
    # 启动器
    NapCatQCELauncher,
    start_napcat_qce,
    find_napcat_qce_path,
    # 客户端
    NapCatQCE,
    connect,
    # 类型
    ChatType,
    MessageFilter,
    ExportOptions,
    ExportTask,
    TaskStatus,
    # 配置
    set_export_dir,
    set_export_format,
    ExportConfig,
)


@dataclass
class ExportTarget:
    """导出目标"""
    id: str  # QQ号或群号
    name: Optional[str] = None  # 名称（可选，用于显示）
    is_group: bool = True  # True=群聊, False=私聊


@dataclass
class ExportResult:
    """导出结果"""
    target: ExportTarget
    success: bool
    message_count: int = 0
    file_name: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0  # 耗时（秒）


def export_by_time_range(
    client: NapCatQCE,
    targets: List[Union[str, ExportTarget]],
    days: int = 7,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    format: str = "HTML",
    output_dir: Optional[str] = None,
    include_resources: bool = True,
    on_progress: Optional[callable] = None,
) -> List[ExportResult]:
    """
    按时间范围导出指定列表的聊天记录

    Args:
        client: NapCatQCE 客户端
        targets: 导出目标列表，可以是:
            - 字符串列表: ["123456", "789012"] (默认为群号)
            - ExportTarget 列表: [ExportTarget("123456", is_group=True)]
        days: 导出最近多少天的记录（当 start_time/end_time 未指定时使用）
        start_time: 开始时间（可选）
        end_time: 结束时间（可选，默认为当前时间）
        format: 导出格式 (HTML, JSON, TXT, EXCEL)
        output_dir: 输出目录（可选）
        include_resources: 是否包含图片等资源
        on_progress: 进度回调 (target, progress, message)

    Returns:
        导出结果列表
    """
    results: List[ExportResult] = []

    # 处理时间范围
    if end_time is None:
        end_time = datetime.now()
    if start_time is None:
        start_time = end_time - timedelta(days=days)

    # 转换为毫秒时间戳
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    print(f"\n📅 导出时间范围: {start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"📋 导出目标数量: {len(targets)}")
    print(f"📁 导出格式: {format}")
    if output_dir:
        print(f"📂 输出目录: {output_dir}")
    print()

    # 设置导出配置
    if output_dir:
        set_export_dir(output_dir)
    set_export_format(format)

    # 获取群组和好友列表用于匹配名称
    groups = {g.group_code: g for g in client.groups.get_all()}
    friends = {f.uin: f for f in client.friends.get_all()}

    # 处理目标列表
    normalized_targets: List[ExportTarget] = []
    for target in targets:
        if isinstance(target, str):
            # 字符串，尝试判断是群还是好友
            if target in groups:
                normalized_targets.append(ExportTarget(
                    id=target,
                    name=groups[target].group_name,
                    is_group=True,
                ))
            elif target in friends:
                normalized_targets.append(ExportTarget(
                    id=target,
                    name=friends[target].remark or friends[target].nick,
                    is_group=False,
                ))
            else:
                # 默认当作群号处理
                normalized_targets.append(ExportTarget(id=target, is_group=True))
        else:
            # 已经是 ExportTarget
            if target.name is None:
                if target.is_group and target.id in groups:
                    target.name = groups[target.id].group_name
                elif not target.is_group and target.id in friends:
                    target.name = friends[target.id].remark or friends[target.id].nick
            normalized_targets.append(target)

    # 创建消息筛选器
    msg_filter = MessageFilter(
        start_time=start_ts,
        end_time=end_ts,
    )

    # 创建导出选项
    options = ExportOptions(
        include_resource_links=include_resources,
        include_system_messages=True,
    )

    # 逐个导出
    for i, target in enumerate(normalized_targets, 1):
        target_name = target.name or target.id
        chat_type = ChatType.GROUP.value if target.is_group else ChatType.PRIVATE.value
        type_text = "群聊" if target.is_group else "私聊"

        print(f"[{i}/{len(normalized_targets)}] 正在导出 {type_text}: {target_name} ({target.id})")

        start_export_time = time.time()

        try:
            # 创建导出任务
            task = client.messages.export(
                chat_type=chat_type,
                peer_uid=target.id,
                format=format,
                filter=msg_filter,
                options=options,
                session_name=target_name,
            )

            # 等待完成
            def progress_callback(t: ExportTask):
                if on_progress:
                    on_progress(target, t.progress, f"{t.message_count} 条消息")
                print(f"\r   进度: {t.progress}% ({t.message_count} 条消息)", end="", flush=True)

            result = client.tasks.wait_for_completion(
                task.id,
                timeout=600,
                poll_interval=2,
                on_progress=progress_callback,
            )

            duration = time.time() - start_export_time
            print(f"\n   ✅ 完成! {result.message_count} 条消息, 耗时 {duration:.1f}s")

            results.append(ExportResult(
                target=target,
                success=True,
                message_count=result.message_count,
                file_name=result.file_name,
                duration=duration,
            ))

        except Exception as e:
            duration = time.time() - start_export_time
            print(f"\n   ❌ 失败: {e}")

            results.append(ExportResult(
                target=target,
                success=False,
                error=str(e),
                duration=duration,
            ))

    return results


def export_recent_chats(
    client: NapCatQCE,
    group_ids: Optional[List[str]] = None,
    friend_ids: Optional[List[str]] = None,
    days: int = 7,
    format: str = "HTML",
    output_dir: Optional[str] = None,
) -> List[ExportResult]:
    """
    导出最近的聊天记录（简化版）

    Args:
        client: NapCatQCE 客户端
        group_ids: 群号列表（None 表示不导出群聊）
        friend_ids: 好友QQ号列表（None 表示不导出私聊）
        days: 最近多少天
        format: 导出格式
        output_dir: 输出目录

    Returns:
        导出结果列表
    """
    targets: List[ExportTarget] = []

    if group_ids:
        for gid in group_ids:
            targets.append(ExportTarget(id=gid, is_group=True))

    if friend_ids:
        for fid in friend_ids:
            targets.append(ExportTarget(id=fid, is_group=False))

    return export_by_time_range(
        client=client,
        targets=targets,
        days=days,
        format=format,
        output_dir=output_dir,
    )


def print_export_summary(results: List[ExportResult]):
    """打印导出摘要"""
    print("\n" + "=" * 60)
    print("📊 导出摘要")
    print("=" * 60)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    total_messages = sum(r.message_count for r in results)
    total_duration = sum(r.duration for r in results)

    print(f"总计: {len(results)} 个目标")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"消息总数: {total_messages} 条")
    print(f"总耗时: {total_duration:.1f} 秒")

    if results:
        print("\n详细结果:")
        for r in results:
            status = "✅" if r.success else "❌"
            name = r.target.name or r.target.id
            type_text = "群" if r.target.is_group else "私"
            if r.success:
                print(f"  {status} [{type_text}] {name}: {r.message_count} 条消息")
            else:
                print(f"  {status} [{type_text}] {name}: {r.error}")


# ============================================================================
# 示例程序
# ============================================================================

def example_with_auto_start():
    """
    示例: 自动启动 NapCat-QCE 并导出指定列表
    """
    print("=" * 60)
    print("NapCat-QCE 批量导出示例 - 自动启动模式")
    print("=" * 60)

    # ========================================
    # 配置区域 - 根据需要修改
    # ========================================

    # 要导出的群号列表
    GROUP_IDS = [
        "123456789",  # 替换为实际群号
        "987654321",
    ]

    # 要导出的好友QQ号列表
    FRIEND_IDS = [
        "111222333",  # 替换为实际QQ号
    ]

    # 导出最近多少天
    DAYS = 7

    # 导出格式: HTML, JSON, TXT, EXCEL
    FORMAT = "HTML"

    # 输出目录
    OUTPUT_DIR = "D:/QQ聊天记录导出"

    # ========================================
    # 执行导出
    # ========================================

    # 检查 NapCat-QCE 路径
    napcat_path = find_napcat_qce_path()
    if not napcat_path:
        print("❌ 未找到 NapCat-QCE，请设置 NAPCAT_QCE_PATH 环境变量")
        return

    print(f"📁 NapCat-QCE 路径: {napcat_path}")

    # 使用启动器自动管理服务生命周期
    with NapCatQCELauncher(napcat_path=napcat_path) as launcher:
        print("✅ NapCat-QCE 服务已启动")

        # 获取客户端
        client = launcher.get_client()

        # 显示登录信息
        info = client.system.get_info()
        print(f"👤 当前登录: {info.self_nick} ({info.self_uin})")

        # 执行批量导出
        results = export_recent_chats(
            client=client,
            group_ids=GROUP_IDS,
            friend_ids=FRIEND_IDS,
            days=DAYS,
            format=FORMAT,
            output_dir=OUTPUT_DIR,
        )

        # 打印摘要
        print_export_summary(results)

        client.close()

    print("\n✅ NapCat-QCE 服务已自动停止")


def example_with_existing_service():
    """
    示例: 连接已运行的 NapCat-QCE 服务
    """
    print("=" * 60)
    print("NapCat-QCE 批量导出示例 - 连接已有服务")
    print("=" * 60)

    # ========================================
    # 配置区域
    # ========================================

    # 要导出的目标（混合群和好友）
    TARGETS = [
        ExportTarget("123456789", name="我的群1", is_group=True),
        ExportTarget("987654321", name="我的群2", is_group=True),
        ExportTarget("111222333", name="好友A", is_group=False),
    ]

    # 自定义时间范围
    START_TIME = datetime(2024, 1, 1)  # 从2024年1月1日开始
    END_TIME = datetime.now()  # 到现在

    FORMAT = "JSON"
    OUTPUT_DIR = "D:/QQ备份"

    # ========================================
    # 执行导出
    # ========================================

    # 自动连接（从配置文件读取令牌）
    client = connect()

    if not client.is_connected():
        print("❌ 无法连接到 NapCat-QCE 服务")
        print("请确保服务已启动，或使用 example_with_auto_start()")
        return

    print("✅ 已连接到 NapCat-QCE 服务")

    info = client.system.get_info()
    print(f"👤 当前登录: {info.self_nick} ({info.self_uin})")

    # 执行导出
    results = export_by_time_range(
        client=client,
        targets=TARGETS,
        start_time=START_TIME,
        end_time=END_TIME,
        format=FORMAT,
        output_dir=OUTPUT_DIR,
    )

    print_export_summary(results)
    client.close()


def example_export_all_groups():
    """
    示例: 导出所有群的最近聊天记录
    """
    print("=" * 60)
    print("NapCat-QCE 批量导出示例 - 导出所有群")
    print("=" * 60)

    DAYS = 3  # 最近3天
    FORMAT = "HTML"
    OUTPUT_DIR = "D:/QQ全部群导出"

    client = connect()

    if not client.is_connected():
        print("❌ 无法连接")
        return

    info = client.system.get_info()
    print(f"👤 当前登录: {info.self_nick}")

    # 获取所有群
    groups = client.groups.get_all()
    print(f"📋 共有 {len(groups)} 个群")

    # 确认
    confirm = input(f"是否导出所有 {len(groups)} 个群的最近 {DAYS} 天记录? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return

    # 转换为目标列表
    targets = [
        ExportTarget(g.group_code, name=g.group_name, is_group=True)
        for g in groups
    ]

    results = export_by_time_range(
        client=client,
        targets=targets,
        days=DAYS,
        format=FORMAT,
        output_dir=OUTPUT_DIR,
    )

    print_export_summary(results)
    client.close()


def interactive_export():
    """
    交互式导出
    """
    print("=" * 60)
    print("NapCat-QCE 批量导出 - 交互模式")
    print("=" * 60)

    # 连接
    client = connect()
    if not client.is_connected():
        print("❌ 无法连接，尝试启动服务...")

        napcat_path = find_napcat_qce_path()
        if not napcat_path:
            print("❌ 未找到 NapCat-QCE")
            return None, None

        launcher = NapCatQCELauncher(napcat_path=napcat_path)
        launcher.start(wait_for_ready=True)
        client = launcher.get_client()
    else:
        launcher = None

    info = client.system.get_info()
    print(f"✅ 已连接: {info.self_nick} ({info.self_uin})")

    # 获取列表
    groups = client.groups.get_all()
    friends = client.friends.get_all()

    print(f"\n📋 群组 ({len(groups)} 个):")
    for i, g in enumerate(groups[:10], 1):
        print(f"   {i}. {g.group_name} ({g.group_code})")
    if len(groups) > 10:
        print(f"   ... 还有 {len(groups) - 10} 个")

    print(f"\n👥 好友 ({len(friends)} 个):")
    for i, f in enumerate(friends[:10], 1):
        name = f.remark or f.nick
        print(f"   {i}. {name} ({f.uin})")
    if len(friends) > 10:
        print(f"   ... 还有 {len(friends) - 10} 个")

    # 输入要导出的ID
    print("\n请输入要导出的群号/QQ号（用逗号分隔，直接回车导出全部群）:")
    ids_input = input("> ").strip()

    if ids_input:
        target_ids = [id.strip() for id in ids_input.split(",")]
    else:
        target_ids = [g.group_code for g in groups]

    # 输入天数
    days_input = input("导出最近多少天的记录? (默认7): ").strip()
    days = int(days_input) if days_input else 7

    # 输入格式
    format_input = input("导出格式 (HTML/JSON/TXT/EXCEL, 默认HTML): ").strip().upper()
    format = format_input if format_input in ["HTML", "JSON", "TXT", "EXCEL"] else "HTML"

    # 输入目录
    output_dir = input("输出目录 (直接回车使用默认): ").strip()
    output_dir = output_dir if output_dir else None

    # 执行导出
    results = export_by_time_range(
        client=client,
        targets=target_ids,
        days=days,
        format=format,
        output_dir=output_dir,
    )

    print_export_summary(results)

    client.close()
    if launcher:
        launcher.stop()


def main():
    print("NapCat-QCE 批量导出工具")
    print("=" * 60)
    print("1. 自动启动服务并导出指定列表")
    print("2. 连接已有服务并导出")
    print("3. 导出所有群的最近记录")
    print("4. 交互式导出")
    print()

    choice = input("请选择 (1-4): ").strip()

    if choice == "1":
        example_with_auto_start()
    elif choice == "2":
        example_with_existing_service()
    elif choice == "3":
        example_export_all_groups()
    elif choice == "4":
        interactive_export()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
