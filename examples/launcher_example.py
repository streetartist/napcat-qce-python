"""
NapCat-QCE Python SDK 启动器示例
==============================

演示如何通过 Python 启动和管理 NapCat-QCE 服务。
"""

from napcat_qce import (
    NapCatQCELauncher,
    run_with_napcat,
    find_napcat_qce_path,
    set_export_dir,
    set_export_format,
    get_export_config,
    ExportConfig,
)


def example_context_manager():
    """使用上下文管理器（推荐）"""
    print("=" * 40)
    print("示例1: 上下文管理器")
    print("=" * 40)

    napcat_path = find_napcat_qce_path()
    if not napcat_path:
        print("未找到 NapCat-QCE")
        return

    with NapCatQCELauncher(napcat_path=napcat_path) as launcher:
        client = launcher.get_client()
        info = client.system.get_info()
        print(f"已登录: {info.self_nick}")

        groups = client.groups.get_all()
        print(f"群组数量: {len(groups)}")

    print("服务已自动停止")


def example_run_with_napcat():
    """使用 run_with_napcat 执行任务"""
    print("=" * 40)
    print("示例2: run_with_napcat")
    print("=" * 40)

    def my_task(client):
        info = client.system.get_info()
        print(f"登录账号: {info.self_nick}")

        groups = client.groups.get_all()
        print(f"群组数量: {len(groups)}")
        for g in groups[:3]:
            print(f"  - {g.group_name}")

    run_with_napcat(my_task)


def example_export_config():
    """配置导出设置（不需要启动服务）"""
    print("=" * 40)
    print("示例3: 导出配置")
    print("=" * 40)

    set_export_dir("D:/QQ聊天记录")
    set_export_format("HTML")

    config = get_export_config()
    print(f"格式: {config.format}")
    print(f"目录: {config.output_dir}")

    # 自定义配置
    custom = ExportConfig(
        format="JSON",
        output_dir="D:/备份",
        export_as_zip=True,
    )
    print(f"\n自定义配置: {custom.format}, ZIP={custom.export_as_zip}")


def example_full_workflow():
    """完整工作流程"""
    print("=" * 40)
    print("示例4: 完整工作流程")
    print("=" * 40)

    napcat_path = find_napcat_qce_path()
    if not napcat_path:
        print("未找到 NapCat-QCE")
        return

    with NapCatQCELauncher(napcat_path=napcat_path) as launcher:
        client = launcher.get_client()

        groups = client.groups.get_all()
        if not groups:
            print("没有群组")
            return

        group = groups[0]
        print(f"导出: {group.group_name}")

        task = client.export_group(group.group_code, days=7)
        print(f"完成! {task.message_count} 条消息 -> {task.file_name}")


def main():
    print("启动器示例")
    print("1. 上下文管理器")
    print("2. run_with_napcat")
    print("3. 导出配置（无需启动）")
    print("4. 完整工作流程")

    choice = input("\n选择 (1-4): ").strip()

    if choice == "1":
        example_context_manager()
    elif choice == "2":
        example_run_with_napcat()
    elif choice == "3":
        example_export_config()
    elif choice == "4":
        example_full_workflow()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
