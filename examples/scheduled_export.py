"""
NapCat-QCE Python SDK 定时导出示例
================================

演示如何创建和管理定时导出任务。
"""

from napcat_qce import (
    connect,
    ScheduledExportConfig,
    Peer,
    ScheduleType,
    TimeRangeType,
    ExportFormat,
    ChatType,
)


def main():
    with connect() as client:
        if not client.is_connected():
            print("无法连接到服务器")
            return

        # 获取群组
        groups = client.groups.get_all()
        if not groups:
            print("没有找到任何群组")
            return

        group = groups[0]
        print(f"使用群组: {group.group_name}")

        # 查看现有定时任务
        print("\n现有定时任务:")
        exports = client.scheduled_exports.get_all()
        if not exports:
            print("  暂无")
        else:
            for e in exports:
                status = "启用" if e.enabled else "禁用"
                print(f"  {e.name} ({status}) - {e.schedule_type.value} {e.execute_time}")

        # 创建每日备份任务
        print("\n创建每日备份任务...")
        config = ScheduledExportConfig(
            name=f"每日备份-{group.group_name}",
            peer=Peer(chat_type=ChatType.GROUP.value, peer_uid=group.group_code),
            schedule_type=ScheduleType.DAILY,
            execute_time="06:00",
            time_range_type=TimeRangeType.YESTERDAY,
            format=ExportFormat.HTML,
        )
        scheduled = client.scheduled_exports.create(config)
        print(f"  已创建: {scheduled.id}")
        print(f"  下次执行: {scheduled.next_run}")

        # 管理任务
        print("\n管理任务:")
        print("  禁用...")
        client.scheduled_exports.disable(scheduled.id)
        print("  启用...")
        client.scheduled_exports.enable(scheduled.id)
        print("  手动触发...")
        client.scheduled_exports.trigger(scheduled.id)

        # 查看执行历史
        print("\n执行历史:")
        history = client.scheduled_exports.get_history(scheduled.id, limit=5)
        if not history:
            print("  暂无记录")
        else:
            for h in history:
                status = "成功" if h.get("success") else "失败"
                print(f"  {h.get('executedAt', '未知')} - {status}")

        print("\n演示完成!")
        print("提示: 定时任务会在指定时间自动执行")


if __name__ == "__main__":
    main()
