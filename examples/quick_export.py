"""
NapCat-QCE 快速导出脚本
=====================

一键导出指定聊天记录。
直接修改下方配置后运行即可。
"""

from napcat_qce import connect

# ============================================================================
# 配置区域 - 请根据需要修改
# ============================================================================

# 要导出的群号列表（留空则不导出群聊）
GROUPS_TO_EXPORT = [
    # "123456789",  # 取消注释并替换为实际群号
    # "987654321",
]

# 要导出的好友QQ号列表（留空则不导出私聊）
FRIENDS_TO_EXPORT = [
    # "111222333",  # 取消注释并替换为实际QQ号
]

# 导出最近多少天的记录
EXPORT_DAYS = 7

# 导出格式: "HTML", "JSON", "TXT", "EXCEL"
EXPORT_FORMAT = "HTML"


# ============================================================================
# 主程序
# ============================================================================

def main():
    print("=" * 50)
    print("NapCat-QCE 快速导出")
    print("=" * 50)

    # 检查配置
    if not GROUPS_TO_EXPORT and not FRIENDS_TO_EXPORT:
        print("请编辑脚本顶部的 GROUPS_TO_EXPORT 或 FRIENDS_TO_EXPORT")
        return

    # 连接服务
    client = connect()
    if not client.is_connected():
        print("无法连接到 NapCat-QCE 服务器")
        return

    # 显示登录信息
    info = client.system.get_info()
    print(f"已登录: {info.self_nick} ({info.self_uin})")
    print(f"时间范围: 最近 {EXPORT_DAYS} 天 | 格式: {EXPORT_FORMAT}")
    print()

    # 构建导出目标列表
    targets = []
    for group_id in GROUPS_TO_EXPORT:
        targets.append({"type": "group", "id": group_id})
    for friend_id in FRIENDS_TO_EXPORT:
        targets.append({"type": "friend", "id": friend_id})

    # 批量导出
    results = client.batch_export(
        targets=targets,
        format=EXPORT_FORMAT,
        days=EXPORT_DAYS,
        on_progress=lambda id, task: print(f"  {task.session_name}: {task.message_count} 条消息"),
        on_error=lambda id, e: print(f"  {id}: 失败 - {e}"),
    )

    # 打印摘要
    print()
    print("=" * 50)
    print(f"导出完成! 成功: {results['success']}, 失败: {results['failed']}")
    print(f"消息总数: {results['total_messages']} 条")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    main()
