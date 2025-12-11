"""
NapCat-QCE Python SDK 基本用法示例
================================

演示如何使用 SDK 进行基本操作。
"""

from napcat_qce import connect, ChatType


def main():
    # 连接（自动获取令牌）
    client = connect()

    if not client.is_connected():
        print("无法连接到 NapCat-QCE 服务器")
        return

    # 获取系统信息
    info = client.system.get_info()
    print(f"已登录: {info.self_nick} ({info.self_uin})")

    # 获取群组列表
    print("\n群组列表:")
    for group in client.groups.get_all()[:5]:
        print(f"  {group.group_name} ({group.group_code}) - {group.member_count}人")

    # 获取好友列表
    print("\n好友列表:")
    for friend in client.friends.get_all()[:5]:
        name = friend.remark or friend.nick
        print(f"  {name} ({friend.uin})")

    # 获取最近消息
    groups = client.groups.get_all()
    if groups:
        print(f"\n[{groups[0].group_name}] 最近消息:")
        result = client.messages.fetch(ChatType.GROUP, groups[0].group_code, limit=3)
        for msg in result["messages"]:
            sender = msg.sender_member_name or msg.sender_name or "未知"
            print(f"  [{sender}]: (ID: {msg.msg_id})")

    # 查看导出任务
    print("\n导出任务:")
    tasks = client.tasks.get_all()
    if not tasks:
        print("  暂无任务")
    else:
        for task in tasks[:3]:
            print(f"  {task.session_name}: {task.status.value} ({task.message_count}条)")

    client.close()
    print("\n完成!")


if __name__ == "__main__":
    main()
