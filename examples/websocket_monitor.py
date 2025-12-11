"""
NapCat-QCE Python SDK WebSocket 监控示例
======================================

演示如何使用 WebSocket 实时监听导出进度。
"""

import time
from napcat_qce import NapCatQCE, ChatType

# 需要安装 websocket-client: pip install websocket-client
try:
    from napcat_qce.websocket import WebSocketClient, ExportProgressMonitor
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False
    print("⚠️ 请先安装 websocket-client: pip install websocket-client")


def example_websocket_client():
    """使用 WebSocketClient 监听事件"""
    print("\n📡 WebSocket 客户端示例")
    print("=" * 50)

    # 创建 WebSocket 客户端
    ws = WebSocketClient(
        host="localhost",
        port=40653,
        auto_reconnect=True,
    )

    # 注册事件处理器
    @ws.on("connected")
    def on_connected(data):
        print(f"✅ WebSocket 已连接")
        print(f"   消息: {data.get('message')}")

    @ws.on("export_progress")
    def on_progress(data):
        task_id = data.get("taskId", "")[:8]
        progress = data.get("progress", 0)
        message = data.get("message", "")
        count = data.get("messageCount", 0)
        print(f"📊 [{task_id}...] 进度: {progress}% - {count} 条消息 - {message}")

    @ws.on("export_complete")
    def on_complete(data):
        task_id = data.get("taskId", "")[:8]
        count = data.get("messageCount", 0)
        file_name = data.get("fileName", "")
        print(f"✅ [{task_id}...] 导出完成!")
        print(f"   消息数: {count}")
        print(f"   文件: {file_name}")

    @ws.on("export_error")
    def on_error(data):
        task_id = data.get("taskId", "")[:8]
        error = data.get("error", "未知错误")
        print(f"❌ [{task_id}...] 导出失败: {error}")

    # 连接（非阻塞）
    print("正在连接...")
    ws.connect(blocking=False)

    # 等待连接建立
    time.sleep(1)

    if ws.is_connected:
        print("\n💡 WebSocket 已就绪，等待事件...")
        print("   现在可以在另一个终端创建导出任务")
        print("   按 Ctrl+C 退出\n")

        try:
            # 保持运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在断开连接...")
    else:
        print("❌ 连接失败")

    ws.disconnect()
    print("已断开连接")


def example_progress_monitor():
    """使用 ExportProgressMonitor 监控导出任务"""
    print("\n📊 导出进度监控器示例")
    print("=" * 50)

    # 自动获取令牌连接
    from napcat_qce import connect
    client = connect()

    if not client.is_connected():
        print("❌ 无法连接到服务器")
        return

    # 获取群组
    groups = client.groups.get_all()
    if not groups:
        print("❌ 没有找到群组")
        return

    group = groups[0]
    print(f"📌 将导出群组: {group.group_name}")

    # 创建进度监控器
    with ExportProgressMonitor(host="localhost", port=40653) as monitor:
        print("📡 进度监控器已启动")

        # 创建导出任务
        print("\n🚀 创建导出任务...")
        task = client.messages.export(
            chat_type=ChatType.GROUP.value,
            peer_uid=group.group_code,
            format="HTML",
            session_name=group.group_name,
        )
        print(f"   任务ID: {task.id}")

        # 定义进度回调
        def on_progress(status):
            progress = status.get("progress", 0)
            count = status.get("message_count", 0)
            print(f"\r   进度: {progress}% ({count} 条消息)", end="", flush=True)

        # 等待任务完成
        print("\n⏳ 等待任务完成...")
        try:
            result = monitor.wait_for_task(
                task.id,
                timeout=600,
                on_progress=on_progress,
            )

            print()  # 换行
            if result.get("status") == "completed":
                print(f"✅ 导出完成!")
                print(f"   消息数: {result.get('message_count')}")
                print(f"   文件: {result.get('file_name')}")
            else:
                print(f"❌ 导出失败: {result.get('error')}")

        except TimeoutError:
            print("\n❌ 等待超时")

    client.close()


def example_multiple_tasks():
    """同时监控多个导出任务"""
    print("\n📊 多任务监控示例")
    print("=" * 50)

    # 自动获取令牌连接
    from napcat_qce import connect
    client = connect()

    if not client.is_connected():
        print("❌ 无法连接到服务器")
        return

    groups = client.groups.get_all()[:3]  # 取前3个群
    if len(groups) < 2:
        print("❌ 需要至少2个群组")
        return

    # 创建 WebSocket 客户端
    ws = WebSocketClient(host="localhost", port=40653)

    # 跟踪任务状态
    task_status = {}

    @ws.on("export_progress")
    def on_progress(data):
        task_id = data.get("taskId")
        if task_id in task_status:
            task_status[task_id]["progress"] = data.get("progress", 0)
            task_status[task_id]["count"] = data.get("messageCount", 0)

            # 显示所有任务进度
            print("\r", end="")
            for tid, status in task_status.items():
                name = status["name"][:10]
                prog = status["progress"]
                print(f"[{name}:{prog}%] ", end="")
            print("", end="", flush=True)

    @ws.on("export_complete")
    def on_complete(data):
        task_id = data.get("taskId")
        if task_id in task_status:
            task_status[task_id]["status"] = "completed"
            print(f"\n✅ {task_status[task_id]['name']} 导出完成!")

    ws.connect(blocking=False)
    time.sleep(1)

    # 创建多个导出任务
    print("🚀 创建多个导出任务...")
    for group in groups:
        task = client.messages.export(
            chat_type=ChatType.GROUP.value,
            peer_uid=group.group_code,
            format="HTML",
            session_name=group.group_name,
        )
        task_status[task.id] = {
            "name": group.group_name,
            "progress": 0,
            "count": 0,
            "status": "running",
        }
        print(f"   创建任务: {group.group_name}")

    print("\n⏳ 等待所有任务完成...")

    # 等待所有任务完成
    timeout = 600
    start = time.time()
    while time.time() - start < timeout:
        all_done = all(s["status"] == "completed" for s in task_status.values())
        if all_done:
            break
        time.sleep(1)

    print("\n\n📋 最终结果:")
    for tid, status in task_status.items():
        emoji = "✅" if status["status"] == "completed" else "⏳"
        print(f"   {emoji} {status['name']}: {status['progress']}%")

    ws.disconnect()
    client.close()


def main():
    if not HAS_WEBSOCKET:
        print("❌ 请先安装 websocket-client:")
        print("   pip install websocket-client")
        return

    print("NapCat-QCE WebSocket 监控示例")
    print("=" * 50)
    print("1. WebSocket 客户端 - 监听所有事件")
    print("2. 进度监控器 - 监控单个任务")
    print("3. 多任务监控 - 同时监控多个任务")
    print()

    choice = input("请选择示例 (1/2/3): ").strip()

    if choice == "1":
        example_websocket_client()
    elif choice == "2":
        example_progress_monitor()
    elif choice == "3":
        example_multiple_tasks()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
