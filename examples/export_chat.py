"""
NapCat-QCE Python SDK 导出聊天记录示例
====================================

演示如何导出聊天记录到各种格式。
"""

from napcat_qce import connect, MessageFilter, ExportOptions


def main():
    with connect() as client:
        if not client.is_connected():
            print("无法连接到服务器")
            return

        # 获取群组列表
        groups = client.groups.get_all()
        if not groups:
            print("没有找到任何群组")
            return

        # 显示群组列表
        print("可用群组:")
        for i, g in enumerate(groups[:10], 1):
            print(f"  {i}. {g.group_name} ({g.group_code})")

        group = groups[0]
        print(f"\n使用群组: {group.group_name}")

        # 演示1: 基本导出
        print("\n" + "=" * 40)
        print("演示1: 基本导出")
        print("=" * 40)
        task = client.export_group(group.group_code)
        print(f"完成! {task.message_count} 条消息 -> {task.file_name}")

        # 演示2: 导出最近7天
        print("\n" + "=" * 40)
        print("演示2: 导出最近7天")
        print("=" * 40)
        task = client.export_group(group.group_code, days=7)
        print(f"完成! {task.message_count} 条消息")

        # 演示3: 导出为JSON
        print("\n" + "=" * 40)
        print("演示3: 导出为JSON")
        print("=" * 40)
        task = client.export_group(group.group_code, format="JSON", days=3)
        print(f"完成! {task.message_count} 条消息")

        # 演示4: 使用自定义筛选器
        print("\n" + "=" * 40)
        print("演示4: 自定义筛选（最近24小时）")
        print("=" * 40)
        task = client.export_group(
            group.group_code,
            filter=MessageFilter.last_hours(24),
        )
        print(f"完成! {task.message_count} 条消息")

        # 演示5: 纯文字导出（不含图片）
        print("\n" + "=" * 40)
        print("演示5: 纯文字导出")
        print("=" * 40)
        task = client.messages.quick_export(
            chat_type=2,
            peer_uid=group.group_code,
            days=7,
            options=ExportOptions(
                filter_pure_image_messages=True,
                include_resource_links=False,
            ),
        )
        print(f"完成! {task.message_count} 条消息")

        print("\n所有演示完成!")


if __name__ == "__main__":
    main()
