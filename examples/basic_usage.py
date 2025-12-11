"""
NapCat-QCE Python SDK 基本用法示例
================================

演示如何使用 SDK 进行基本操作。
"""

from napcat_qce import (
    NapCatQCE,
    MessageFilter,
    ExportOptions,
    ChatType,
    ExportFormat,
    # 自动令牌相关
    connect,
    AutoTokenClient,
    auto_discover_token,
    get_token_from_config,
)


def main():
    # ========================================
    # 1. 创建客户端并连接
    # ========================================

    # 方式1: 最简单 - 自动获取令牌（推荐）
    # 自动从以下位置获取令牌:
    #   - 环境变量 NAPCAT_QCE_TOKEN
    #   - 本地配置文件 ~/.qq-chat-exporter/security.json
    client = connect()

    # 方式2: 使用 AutoTokenClient（功能同上）
    # client = AutoTokenClient()

    # 方式3: 指定服务器地址，自动获取令牌
    # client = connect(host="192.168.1.100", port=40653)

    # 方式4: 手动指定令牌
    # client = NapCatQCE(token="your_token_here")

    # 方式5: 手动获取令牌后使用
    # token = get_token_from_config()  # 从本地配置读取
    # token = auto_discover_token()    # 自动发现
    # client = NapCatQCE(token=token)

    # 检查连接
    if not client.is_connected():
        print("❌ 无法连接到 NapCat-QCE 服务器")
        print("请确保:")
        print("  1. NapCat-QCE 服务正在运行")
        print("  2. 访问令牌正确")
        return

    print("✅ 已连接到 NapCat-QCE 服务器")

    # ========================================
    # 2. 获取系统信息
    # ========================================

    info = client.system.get_info()
    print(f"\n📱 当前登录账号:")
    print(f"   昵称: {info.self_nick}")
    print(f"   QQ号: {info.self_uin}")
    print(f"   在线: {'是' if info.online else '否'}")

    # ========================================
    # 3. 获取群组列表
    # ========================================

    print("\n📋 群组列表:")
    groups = client.groups.get_all()

    for i, group in enumerate(groups[:5], 1):  # 只显示前5个
        print(f"   {i}. {group.group_name}")
        print(f"      群号: {group.group_code}")
        print(f"      成员: {group.member_count} 人")

    if len(groups) > 5:
        print(f"   ... 还有 {len(groups) - 5} 个群组")

    # ========================================
    # 4. 获取好友列表
    # ========================================

    print("\n👥 好友列表:")
    friends = client.friends.get_all()

    for i, friend in enumerate(friends[:5], 1):  # 只显示前5个
        name = friend.remark or friend.nick
        status = "🟢" if friend.is_online else "⚪"
        print(f"   {i}. {status} {name} ({friend.uin})")

    if len(friends) > 5:
        print(f"   ... 还有 {len(friends) - 5} 个好友")

    # ========================================
    # 5. 获取消息（不导出）
    # ========================================

    if groups:
        group = groups[0]
        print(f"\n💬 获取 [{group.group_name}] 的最近消息:")

        result = client.messages.fetch(
            chat_type=ChatType.GROUP.value,
            peer_uid=group.group_code,
            page=1,
            limit=5,
        )

        for msg in result["messages"]:
            sender = msg.sender_member_name or msg.sender_name or msg.sender_uid
            print(f"   [{sender}]: (消息ID: {msg.msg_id})")

    # ========================================
    # 6. 查看现有导出任务
    # ========================================

    print("\n📦 导出任务列表:")
    tasks = client.tasks.get_all()

    if not tasks:
        print("   暂无导出任务")
    else:
        for task in tasks[:5]:
            status_emoji = {
                "completed": "✅",
                "running": "🔄",
                "failed": "❌",
                "pending": "⏳",
            }.get(task.status.value, "❓")

            print(f"   {status_emoji} {task.session_name}")
            print(f"      状态: {task.status.value}")
            print(f"      消息数: {task.message_count}")

    # ========================================
    # 7. 查看导出文件
    # ========================================

    print("\n📁 导出文件列表:")
    files = client.export_files.get_all()

    if not files:
        print("   暂无导出文件")
    else:
        for f in files[:5]:
            name = f.display_name or f.chat_id
            print(f"   📄 {name}")
            print(f"      格式: {f.format}")
            print(f"      消息数: {f.message_count or '未知'}")

    # ========================================
    # 8. 关闭客户端
    # ========================================

    client.close()
    print("\n✅ 示例完成!")


if __name__ == "__main__":
    main()
