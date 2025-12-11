"""
NapCat-QCE Python SDK 导出聊天记录示例
====================================

演示如何导出聊天记录到各种格式。
"""

import time
from datetime import datetime, timedelta

from napcat_qce import (
    NapCatQCE,
    MessageFilter,
    ExportOptions,
    ChatType,
    ExportFormat,
    TaskStatus,
)


def export_group_chat(client: NapCatQCE, group_code: str, group_name: str):
    """导出群聊记录"""
    print(f"\n🚀 开始导出群聊: {group_name}")

    # 创建导出任务
    task = client.messages.export(
        chat_type=ChatType.GROUP.value,
        peer_uid=group_code,
        format="HTML",
        session_name=group_name,
    )

    print(f"   任务ID: {task.id}")

    # 等待完成（带进度显示）
    def show_progress(t):
        print(f"\r   进度: {t.progress}% - {t.message_count} 条消息", end="", flush=True)

    try:
        result = client.tasks.wait_for_completion(
            task.id,
            timeout=600,  # 10分钟超时
            poll_interval=2,
            on_progress=show_progress,
        )

        print()  # 换行
        print(f"   ✅ 导出完成!")
        print(f"   消息数: {result.message_count}")
        print(f"   文件名: {result.file_name}")
        print(f"   下载地址: {client.base_url}{result.download_url}")

        return result

    except TimeoutError:
        print(f"\n   ❌ 导出超时")
        return None
    except Exception as e:
        print(f"\n   ❌ 导出失败: {e}")
        return None


def export_with_time_filter(client: NapCatQCE, group_code: str, group_name: str):
    """导出指定时间范围的聊天记录"""
    print(f"\n🚀 导出最近7天的聊天记录: {group_name}")

    # 计算时间范围
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    # 转换为毫秒时间戳
    start_time = int(seven_days_ago.timestamp() * 1000)
    end_time = int(now.timestamp() * 1000)

    print(f"   时间范围: {seven_days_ago.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}")

    # 创建筛选条件
    filter = MessageFilter(
        start_time=start_time,
        end_time=end_time,
    )

    # 创建导出选项
    options = ExportOptions(
        include_resource_links=True,
        include_system_messages=True,
    )

    # 创建导出任务
    task = client.messages.export(
        chat_type=ChatType.GROUP.value,
        peer_uid=group_code,
        format="HTML",
        filter=filter,
        options=options,
        session_name=f"{group_name}_最近7天",
    )

    # 等待完成
    result = client.tasks.wait_for_completion(
        task.id,
        timeout=300,
        on_progress=lambda t: print(f"\r   进度: {t.progress}%", end="", flush=True),
    )

    print()
    print(f"   ✅ 导出完成! 共 {result.message_count} 条消息")

    return result


def export_to_json(client: NapCatQCE, group_code: str, group_name: str):
    """导出为 JSON 格式"""
    print(f"\n🚀 导出为 JSON 格式: {group_name}")

    task = client.messages.export(
        chat_type=ChatType.GROUP.value,
        peer_uid=group_code,
        format="JSON",
        session_name=group_name,
    )

    result = client.tasks.wait_for_completion(
        task.id,
        timeout=300,
        on_progress=lambda t: print(f"\r   进度: {t.progress}%", end="", flush=True),
    )

    print()
    print(f"   ✅ JSON 导出完成! 共 {result.message_count} 条消息")

    return result


def export_text_only(client: NapCatQCE, group_code: str, group_name: str):
    """导出纯文字（不下载图片等资源）"""
    print(f"\n🚀 导出纯文字版本: {group_name}")

    options = ExportOptions(
        filter_pure_image_messages=True,  # 跳过资源下载
        include_resource_links=False,
    )

    task = client.messages.export(
        chat_type=ChatType.GROUP.value,
        peer_uid=group_code,
        format="HTML",
        options=options,
        session_name=f"{group_name}_纯文字",
    )

    result = client.tasks.wait_for_completion(
        task.id,
        timeout=300,
        on_progress=lambda t: print(f"\r   进度: {t.progress}%", end="", flush=True),
    )

    print()
    print(f"   ✅ 纯文字导出完成! 共 {result.message_count} 条消息")

    return result


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

        # 显示群组列表供选择
        print("📋 可用群组:")
        for i, g in enumerate(groups[:10], 1):
            print(f"   {i}. {g.group_name} ({g.group_code})")

        # 使用第一个群组进行演示
        group = groups[0]
        print(f"\n📌 使用群组: {group.group_name}")

        # 演示各种导出方式
        print("\n" + "=" * 50)
        print("演示 1: 基本导出")
        print("=" * 50)
        export_group_chat(client, group.group_code, group.group_name)

        print("\n" + "=" * 50)
        print("演示 2: 按时间范围导出")
        print("=" * 50)
        export_with_time_filter(client, group.group_code, group.group_name)

        print("\n" + "=" * 50)
        print("演示 3: 导出为 JSON")
        print("=" * 50)
        export_to_json(client, group.group_code, group.group_name)

        print("\n" + "=" * 50)
        print("演示 4: 纯文字导出")
        print("=" * 50)
        export_text_only(client, group.group_code, group.group_name)

        print("\n✅ 所有演示完成!")


if __name__ == "__main__":
    main()
