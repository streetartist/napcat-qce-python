"""
NapCat-QCE Python SDK WebSocket 监控示例
======================================

演示如何使用 WebSocket 实时监听导出进度。
需要安装: pip install websocket-client
"""

import time

try:
    from napcat_qce.websocket import WebSocketClient, ExportProgressMonitor
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

from napcat_qce import connect, ChatType


def example_websocket_client():
    """监听所有事件"""
    print("=" * 40)
    print("WebSocket 客户端")
    print("=" * 40)

    ws = WebSocketClient(host="localhost", port=40653, auto_reconnect=True)

    @ws.on("connected")
    def on_connected(data):
        print(f"已连接: {data.get('message')}")

    @ws.on("export_progress")
    def on_progress(data):
        print(f"进度: {data.get('progress')}% - {data.get('messageCount')} 条")

    @ws.on("export_complete")
    def on_complete(data):
        print(f"完成! {data.get('messageCount')} 条 -> {data.get('fileName')}")

    @ws.on("export_error")
    def on_error(data):
        print(f"失败: {data.get('error')}")

    ws.connect(blocking=False)
    time.sleep(1)

    if ws.is_connected:
        print("\n等待事件... (Ctrl+C 退出)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    ws.disconnect()
    print("已断开")


def example_progress_monitor():
    """监控单个任务"""
    print("=" * 40)
    print("进度监控器")
    print("=" * 40)

    client = connect()
    if not client.is_connected():
        print("无法连接")
        return

    groups = client.groups.get_all()
    if not groups:
        print("没有群组")
        return

    group = groups[0]
    print(f"导出: {group.group_name}")

    with ExportProgressMonitor(host="localhost", port=40653) as monitor:
        task = client.messages.export(
            chat_type=ChatType.GROUP.value,
            peer_uid=group.group_code,
            format="HTML",
        )

        result = monitor.wait_for_task(
            task.id,
            timeout=600,
            on_progress=lambda s: print(f"\r进度: {s.get('progress')}%", end=""),
        )

        print()
        if result.get("status") == "completed":
            print(f"完成! {result.get('message_count')} 条")
        else:
            print(f"失败: {result.get('error')}")

    client.close()


def example_multiple_tasks():
    """同时监控多个任务"""
    print("=" * 40)
    print("多任务监控")
    print("=" * 40)

    client = connect()
    if not client.is_connected():
        print("无法连接")
        return

    groups = client.groups.get_all()[:3]
    if len(groups) < 2:
        print("需要至少2个群组")
        return

    ws = WebSocketClient(host="localhost", port=40653)
    task_status = {}

    @ws.on("export_progress")
    def on_progress(data):
        tid = data.get("taskId")
        if tid in task_status:
            task_status[tid]["progress"] = data.get("progress", 0)
            # 显示进度
            print("\r" + " ".join(
                f"[{s['name'][:8]}:{s['progress']}%]"
                for s in task_status.values()
            ), end="", flush=True)

    @ws.on("export_complete")
    def on_complete(data):
        tid = data.get("taskId")
        if tid in task_status:
            task_status[tid]["done"] = True
            print(f"\n完成: {task_status[tid]['name']}")

    ws.connect(blocking=False)
    time.sleep(1)

    # 创建任务
    for group in groups:
        task = client.messages.export(
            chat_type=ChatType.GROUP.value,
            peer_uid=group.group_code,
            format="HTML",
        )
        task_status[task.id] = {"name": group.group_name, "progress": 0, "done": False}
        print(f"创建: {group.group_name}")

    # 等待完成
    print("\n等待完成...")
    for _ in range(600):
        if all(s["done"] for s in task_status.values()):
            break
        time.sleep(1)

    print("\n结果:")
    for s in task_status.values():
        print(f"  {'✓' if s['done'] else '○'} {s['name']}: {s['progress']}%")

    ws.disconnect()
    client.close()


def main():
    if not HAS_WEBSOCKET:
        print("请先安装: pip install websocket-client")
        return

    print("WebSocket 监控示例")
    print("1. 监听所有事件")
    print("2. 监控单个任务")
    print("3. 多任务监控")

    choice = input("\n选择 (1-3): ").strip()

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
