"""
NapCat-QCE Python SDK 批量导出示例
================================

批量导出多个群聊/私聊记录。
"""

from napcat_qce import connect


# ============================================================================
# 配置区域
# ============================================================================

# 要导出的群号列表
GROUP_IDS = [
    # "123456789",  # 取消注释并替换为实际群号
    # "987654321",
]

# 要导出的好友QQ号列表
FRIEND_IDS = [
    # "111222333",  # 取消注释并替换为实际QQ号
]

# 导出最近多少天
DAYS = 7

# 导出格式: HTML, JSON, TXT, EXCEL
FORMAT = "HTML"


# ============================================================================
# 示例函数
# ============================================================================

def example_batch_export():
    """批量导出指定列表"""
    print("=" * 50)
    print("批量导出示例")
    print("=" * 50)

    client = connect()
    if not client.is_connected():
        print("无法连接到服务器")
        return

    info = client.system.get_info()
    print(f"已登录: {info.self_nick} ({info.self_uin})")

    # 构建目标列表
    targets = []
    for gid in GROUP_IDS:
        targets.append({"type": "group", "id": gid})
    for fid in FRIEND_IDS:
        targets.append({"type": "friend", "id": fid})

    if not targets:
        print("请先配置 GROUP_IDS 或 FRIEND_IDS")
        client.close()
        return

    # 批量导出
    results = client.batch_export(
        targets=targets,
        format=FORMAT,
        days=DAYS,
        on_progress=lambda id, task: print(f"  {task.session_name}: {task.message_count} 条"),
        on_error=lambda id, e: print(f"  {id}: 失败 - {e}"),
    )

    print(f"\n完成! 成功: {results['success']}, 失败: {results['failed']}")
    print(f"消息总数: {results['total_messages']} 条")
    client.close()


def example_export_all_groups():
    """导出所有群的最近记录"""
    print("=" * 50)
    print("导出所有群")
    print("=" * 50)

    client = connect()
    if not client.is_connected():
        print("无法连接")
        return

    groups = client.groups.get_all()
    print(f"共有 {len(groups)} 个群")

    confirm = input(f"是否导出所有群的最近 {DAYS} 天记录? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        client.close()
        return

    # 构建目标列表
    targets = [{"type": "group", "id": g.group_code, "name": g.group_name} for g in groups]

    results = client.batch_export(
        targets=targets,
        format=FORMAT,
        days=DAYS,
        on_progress=lambda id, task: print(f"  {task.session_name}: {task.message_count} 条"),
        on_error=lambda id, e: print(f"  {id}: 失败 - {e}"),
    )

    print(f"\n完成! 成功: {results['success']}, 失败: {results['failed']}")
    print(f"消息总数: {results['total_messages']} 条")
    client.close()


def interactive_export():
    """交互式导出"""
    print("=" * 50)
    print("交互式导出")
    print("=" * 50)

    client = connect()
    if not client.is_connected():
        print("无法连接")
        return

    info = client.system.get_info()
    print(f"已连接: {info.self_nick}")

    # 显示列表
    groups = client.groups.get_all()
    friends = client.friends.get_all()

    print(f"\n群组 ({len(groups)} 个):")
    for i, g in enumerate(groups[:10], 1):
        print(f"  {i}. {g.group_name} ({g.group_code})")

    print(f"\n好友 ({len(friends)} 个):")
    for i, f in enumerate(friends[:10], 1):
        print(f"  {i}. {f.remark or f.nick} ({f.uin})")

    # 输入
    ids_input = input("\n输入群号/QQ号（逗号分隔，回车导出全部群）: ").strip()
    days = int(input("最近多少天 (默认7): ").strip() or "7")
    fmt = input("格式 (HTML/JSON/TXT/EXCEL, 默认HTML): ").strip().upper() or "HTML"

    # 构建目标
    if ids_input:
        target_ids = [id.strip() for id in ids_input.split(",")]
        group_codes = {g.group_code for g in groups}
        targets = []
        for tid in target_ids:
            if tid in group_codes:
                targets.append({"type": "group", "id": tid})
            else:
                targets.append({"type": "friend", "id": tid})
    else:
        targets = [{"type": "group", "id": g.group_code} for g in groups]

    # 导出
    results = client.batch_export(
        targets=targets,
        format=fmt,
        days=days,
        on_progress=lambda id, task: print(f"  {task.session_name}: {task.message_count} 条"),
        on_error=lambda id, e: print(f"  {id}: 失败 - {e}"),
    )

    print(f"\n完成! 成功: {results['success']}, 失败: {results['failed']}")
    client.close()


def main():
    print("批量导出工具")
    print("1. 导出指定列表")
    print("2. 导出所有群")
    print("3. 交互式导出")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == "1":
        example_batch_export()
    elif choice == "2":
        example_export_all_groups()
    elif choice == "3":
        interactive_export()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
