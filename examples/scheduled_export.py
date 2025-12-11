"""
NapCat-QCE Python SDK 定时导出示例
================================

演示如何创建和管理定时导出任务。
"""

from napcat_qce import (
    NapCatQCE,
    ScheduledExportConfig,
    Peer,
    ScheduleType,
    TimeRangeType,
    ExportFormat,
    ExportOptions,
    ChatType,
)


def create_daily_backup(client: NapCatQCE, group_code: str, group_name: str):
    """创建每日备份任务"""
    print(f"\n📅 创建每日备份任务: {group_name}")

    config = ScheduledExportConfig(
        name=f"每日备份-{group_name}",
        peer=Peer(chat_type=ChatType.GROUP.value, peer_uid=group_code),
        schedule_type=ScheduleType.DAILY,
        execute_time="06:00",  # 每天早上6点执行
        time_range_type=TimeRangeType.YESTERDAY,  # 导出昨天的消息
        format=ExportFormat.HTML,
        enabled=True,
    )

    scheduled = client.scheduled_exports.create(config)

    print(f"   ✅ 任务已创建!")
    print(f"   任务ID: {scheduled.id}")
    print(f"   执行时间: 每天 {scheduled.execute_time}")
    print(f"   下次执行: {scheduled.next_run}")

    return scheduled


def create_weekly_backup(client: NapCatQCE, group_code: str, group_name: str):
    """创建每周备份任务"""
    print(f"\n📅 创建每周备份任务: {group_name}")

    config = ScheduledExportConfig(
        name=f"每周备份-{group_name}",
        peer=Peer(chat_type=ChatType.GROUP.value, peer_uid=group_code),
        schedule_type=ScheduleType.WEEKLY,
        execute_time="00:00",  # 每周日凌晨执行
        time_range_type=TimeRangeType.LAST_WEEK,  # 导出上周的消息
        format=ExportFormat.HTML,
        enabled=True,
    )

    scheduled = client.scheduled_exports.create(config)

    print(f"   ✅ 任务已创建!")
    print(f"   任务ID: {scheduled.id}")
    print(f"   下次执行: {scheduled.next_run}")

    return scheduled


def list_scheduled_exports(client: NapCatQCE):
    """列出所有定时导出任务"""
    print("\n📋 定时导出任务列表:")

    exports = client.scheduled_exports.get_all()

    if not exports:
        print("   暂无定时导出任务")
        return []

    for i, export in enumerate(exports, 1):
        status = "🟢 启用" if export.enabled else "⚪ 禁用"
        schedule_text = {
            ScheduleType.DAILY: "每天",
            ScheduleType.WEEKLY: "每周",
            ScheduleType.MONTHLY: "每月",
            ScheduleType.CUSTOM: "自定义",
        }.get(export.schedule_type, "未知")

        print(f"   {i}. {export.name}")
        print(f"      状态: {status}")
        print(f"      周期: {schedule_text} {export.execute_time}")
        print(f"      格式: {export.format}")
        if export.next_run:
            print(f"      下次执行: {export.next_run}")
        print()

    return exports


def manage_scheduled_export(client: NapCatQCE, export_id: str):
    """管理定时导出任务"""
    print(f"\n⚙️ 管理任务: {export_id}")

    # 获取任务详情
    export = client.scheduled_exports.get(export_id)
    print(f"   任务名称: {export.name}")
    print(f"   当前状态: {'启用' if export.enabled else '禁用'}")

    # 禁用任务
    print("\n   正在禁用任务...")
    client.scheduled_exports.disable(export_id)
    print("   ✅ 任务已禁用")

    # 启用任务
    print("\n   正在启用任务...")
    client.scheduled_exports.enable(export_id)
    print("   ✅ 任务已启用")

    # 手动触发执行
    print("\n   正在手动触发执行...")
    result = client.scheduled_exports.trigger(export_id)
    print(f"   ✅ 已触发执行")

    # 获取执行历史
    print("\n   执行历史:")
    history = client.scheduled_exports.get_history(export_id, limit=5)
    if not history:
        print("      暂无执行记录")
    else:
        for record in history:
            status = "✅" if record.get("success") else "❌"
            print(f"      {status} {record.get('executedAt', '未知时间')}")


def delete_scheduled_export(client: NapCatQCE, export_id: str):
    """删除定时导出任务"""
    print(f"\n🗑️ 删除任务: {export_id}")

    client.scheduled_exports.delete(export_id)
    print("   ✅ 任务已删除")


def main():
    # 自动获取令牌连接
    from napcat_qce import connect

    with connect() as client:
        if not client.is_connected():
            print("❌ 无法连接到服务器")
            return

        # 获取群组列表
        groups = client.groups.get_all()
        if not groups:
            print("❌ 没有找到任何群组")
            return

        group = groups[0]
        print(f"📌 使用群组: {group.group_name}")

        # 列出现有任务
        print("\n" + "=" * 50)
        print("查看现有定时任务")
        print("=" * 50)
        existing = list_scheduled_exports(client)

        # 创建每日备份
        print("\n" + "=" * 50)
        print("创建每日备份任务")
        print("=" * 50)
        daily = create_daily_backup(client, group.group_code, group.group_name)

        # 管理任务
        print("\n" + "=" * 50)
        print("管理定时任务")
        print("=" * 50)
        manage_scheduled_export(client, daily.id)

        # 再次列出任务
        print("\n" + "=" * 50)
        print("更新后的任务列表")
        print("=" * 50)
        list_scheduled_exports(client)

        print("\n✅ 演示完成!")
        print("💡 提示: 定时任务会在指定时间自动执行")


if __name__ == "__main__":
    main()
