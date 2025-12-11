"""
NapCat-QCE 快速导出脚本
=====================

一键启动并导出指定聊天记录。
直接修改下方配置后运行即可。
"""

from napcat_qce import (
    NapCatQCELauncher,
    connect,
    find_napcat_qce_path,
    ChatType,
    MessageFilter,
)
from datetime import datetime, timedelta
import shutil
import os


# ============================================================================
# 📝 配置区域 - 请根据需要修改
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

# 输出目录（None 使用默认目录）
OUTPUT_DIR = "D:/QQ聊天记录"

# 是否自动启动 NapCat-QCE（False 则连接已运行的服务）
AUTO_START = True


# ============================================================================
# 🚀 主程序 - 无需修改
# ============================================================================

def main():
    print("=" * 50)
    print("NapCat-QCE 快速导出")
    print("=" * 50)

    # 检查配置
    if not GROUPS_TO_EXPORT and not FRIENDS_TO_EXPORT:
        print("⚠️  未配置导出目标！")
        print("请编辑脚本顶部的 GROUPS_TO_EXPORT 或 FRIENDS_TO_EXPORT")
        return

    # 计算时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(days=EXPORT_DAYS)
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    print(f"📅 时间范围: 最近 {EXPORT_DAYS} 天")
    print(f"📁 导出格式: {EXPORT_FORMAT}")
    print(f"📋 群聊: {len(GROUPS_TO_EXPORT)} 个")
    print(f"👤 私聊: {len(FRIENDS_TO_EXPORT)} 个")
    print()

    # 获取客户端
    launcher = None
    if AUTO_START:
        napcat_path = find_napcat_qce_path()
        if not napcat_path:
            print("❌ 未找到 NapCat-QCE")
            print("请设置环境变量 NAPCAT_QCE_PATH 或将 AUTO_START 设为 False")
            return

        print("🚀 正在启动 NapCat-QCE...")
        launcher = NapCatQCELauncher(napcat_path=napcat_path)
        launcher.on_output(lambda line: print(line))  # 显示输出（包括二维码）
        launcher.start(wait_for_ready=True, timeout=120)
        client = launcher.get_client()
    else:
        print("🔗 连接到已运行的服务...")
        client = connect()

    if not client.is_connected():
        print("❌ 连接失败")
        return

    # 显示登录信息
    info = client.system.get_info()
    print(f"✅ 已登录: {info.self_nick} ({info.self_uin})")

    # 获取名称映射
    groups = {g.group_code: g.group_name for g in client.groups.get_all()}
    friends = {f.uin: f.remark or f.nick for f in client.friends.get_all()}

    # 创建筛选器
    msg_filter = MessageFilter(start_time=start_ts, end_time=end_ts)

    # 确保输出目录存在
    if OUTPUT_DIR:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 导出结果统计
    success = 0
    failed = 0
    total_messages = 0

    # 导出群聊
    for group_id in GROUPS_TO_EXPORT:
        name = groups.get(group_id, group_id)
        print(f"\n📤 导出群聊: {name}")

        try:
            task = client.messages.export(
                chat_type=ChatType.GROUP.value,
                peer_uid=group_id,
                format=EXPORT_FORMAT,
                filter=msg_filter,
                session_name=name,
            )

            result = client.tasks.wait_for_completion(
                task.id,
                timeout=600,
                on_progress=lambda t: print(f"\r   进度: {t.progress}%", end=""),
            )

            # 移动文件到指定目录
            # 文件保存在 %USERPROFILE%\.qq-chat-exporter\exports\ 目录
            moved = False
            if OUTPUT_DIR and result.file_name:
                user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
                src_path = os.path.join(user_profile, ".qq-chat-exporter", "exports", result.file_name)
                if os.path.exists(src_path):
                    dest_path = os.path.join(OUTPUT_DIR, result.file_name)
                    shutil.move(src_path, dest_path)
                    print(f"\n   ✅ {result.message_count} 条消息 -> {dest_path}")
                    moved = True
                else:
                    print(f"\n   [DEBUG] 文件不存在: {src_path}")
            if not moved:
                print(f"\n   ✅ {result.message_count} 条消息")
            success += 1
            total_messages += result.message_count

        except Exception as e:
            print(f"\n   ❌ 失败: {e}")
            failed += 1

    # 导出私聊
    for friend_id in FRIENDS_TO_EXPORT:
        name = friends.get(friend_id, friend_id)
        print(f"\n📤 导出私聊: {name}")

        try:
            task = client.messages.export(
                chat_type=ChatType.PRIVATE.value,
                peer_uid=friend_id,
                format=EXPORT_FORMAT,
                filter=msg_filter,
                session_name=name,
            )

            result = client.tasks.wait_for_completion(
                task.id,
                timeout=600,
                on_progress=lambda t: print(f"\r   进度: {t.progress}%", end=""),
            )

            # 移动文件到指定目录
            # 文件保存在 %USERPROFILE%\.qq-chat-exporter\exports\ 目录
            moved = False
            if OUTPUT_DIR and result.file_name:
                user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
                src_path = os.path.join(user_profile, ".qq-chat-exporter", "exports", result.file_name)
                if os.path.exists(src_path):
                    dest_path = os.path.join(OUTPUT_DIR, result.file_name)
                    shutil.move(src_path, dest_path)
                    print(f"\n   ✅ {result.message_count} 条消息 -> {dest_path}")
                    moved = True
                else:
                    print(f"\n   [DEBUG] 文件不存在: {src_path}")
            if not moved:
                print(f"\n   ✅ {result.message_count} 条消息")
            success += 1
            total_messages += result.message_count

        except Exception as e:
            print(f"\n   ❌ 失败: {e}")
            failed += 1

    # 打印摘要
    print("\n" + "=" * 50)
    print("📊 导出完成!")
    print(f"   成功: {success} 个")
    print(f"   失败: {failed} 个")
    print(f"   消息总数: {total_messages} 条")
    print("=" * 50)

    # 清理
    client.close()
    if launcher:
        launcher.stop()
        print("✅ 服务已停止")


if __name__ == "__main__":
    main()
