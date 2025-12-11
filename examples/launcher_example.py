"""
NapCat-QCE Python SDK 启动器示例
==============================

演示如何通过 Python 启动和管理 NapCat-QCE 服务。
"""

from napcat_qce import (
    # 启动器
    NapCatQCELauncher,
    start_napcat_qce,
    run_with_napcat,
    find_napcat_qce_path,
    find_qq_path,
    # 配置
    ExportConfig,
    set_export_dir,
    set_export_format,
    get_export_config,
    # 客户端
    connect,
    ChatType,
)


def example_basic_launcher():
    """基本启动器用法"""
    print("\n" + "=" * 50)
    print("示例 1: 基本启动器用法")
    print("=" * 50)

    # 检查路径
    napcat_path = find_napcat_qce_path()
    qq_path = find_qq_path()

    print(f"NapCat-QCE 路径: {napcat_path or '未找到'}")
    print(f"QQ 路径: {qq_path or '未找到'}")

    if not napcat_path or not qq_path:
        print("❌ 请确保 NapCat-QCE 和 QQ 已正确安装")
        return

    # 创建启动器
    launcher = NapCatQCELauncher(
        napcat_path=napcat_path,
        qq_path=qq_path,
        use_user_mode=True,  # 用户模式，不需要管理员权限
    )

    # 设置输出回调
    launcher.on_output(lambda line: print(f"  [NapCat] {line}"))
    launcher.on_ready(lambda token: print(f"  ✅ 服务就绪! 令牌: {token[:8]}..."))

    print("\n🚀 正在启动 NapCat-QCE...")

    try:
        # 启动并等待就绪
        launcher.start(wait_for_ready=True, timeout=120)

        if launcher.is_ready:
            print("\n✅ 服务已就绪!")

            # 获取客户端
            client = launcher.get_client()

            # 使用客户端
            info = client.system.get_info()
            print(f"   当前登录: {info.self_nick} ({info.self_uin})")

            groups = client.groups.get_all()
            print(f"   群组数量: {len(groups)}")

            client.close()
        else:
            print("❌ 服务启动超时")

    finally:
        # 停止服务
        print("\n正在停止服务...")
        launcher.stop()
        print("✅ 服务已停止")


def example_context_manager():
    """使用上下文管理器"""
    print("\n" + "=" * 50)
    print("示例 2: 使用上下文管理器")
    print("=" * 50)

    napcat_path = find_napcat_qce_path()
    if not napcat_path:
        print("❌ 未找到 NapCat-QCE")
        return

    # 使用 with 语句自动管理生命周期
    with NapCatQCELauncher(napcat_path=napcat_path) as launcher:
        print("✅ 服务已启动")

        client = launcher.get_client()
        groups = client.groups.get_all()
        print(f"   共有 {len(groups)} 个群组")

        # with 块结束时自动停止服务

    print("✅ 服务已自动停止")


def example_quick_start():
    """快速启动函数"""
    print("\n" + "=" * 50)
    print("示例 3: 快速启动函数")
    print("=" * 50)

    # 使用 start_napcat_qce 快速启动
    launcher = start_napcat_qce(
        wait_for_ready=True,
        timeout=120,
        on_output=lambda line: print(f"  {line}") if "error" in line.lower() else None,
    )

    try:
        client = launcher.get_client()
        print(f"✅ 已连接，令牌: {launcher.token[:8]}...")

        # 执行操作
        friends = client.friends.get_all()
        print(f"   好友数量: {len(friends)}")

    finally:
        launcher.stop()


def example_run_with_napcat():
    """使用 run_with_napcat 执行任务"""
    print("\n" + "=" * 50)
    print("示例 4: 使用 run_with_napcat")
    print("=" * 50)

    def my_task(client):
        """要执行的任务"""
        print("✅ 任务开始执行")

        # 获取信息
        info = client.system.get_info()
        print(f"   登录账号: {info.self_nick}")

        groups = client.groups.get_all()
        print(f"   群组数量: {len(groups)}")

        # 列出前3个群
        for group in groups[:3]:
            print(f"   - {group.group_name}")

        print("✅ 任务执行完成")

    # 自动启动服务，执行任务，然后停止
    run_with_napcat(my_task)


def example_export_config():
    """配置导出设置"""
    print("\n" + "=" * 50)
    print("示例 5: 配置导出设置")
    print("=" * 50)

    # 设置导出目录
    set_export_dir("D:/我的QQ聊天记录")
    print("✅ 已设置导出目录: D:/我的QQ聊天记录")

    # 设置导出格式
    set_export_format("HTML")
    print("✅ 已设置导出格式: HTML")

    # 获取完整配置
    config = get_export_config()
    print(f"\n当前配置:")
    print(f"   格式: {config.format}")
    print(f"   目录: {config.output_dir}")
    print(f"   包含资源: {config.include_resources}")
    print(f"   批量大小: {config.batch_size}")

    # 创建自定义配置
    custom_config = ExportConfig(
        format="JSON",
        output_dir="D:/备份/QQ",
        file_name_template="{type}_{name}_{date}",
        include_resources=False,
        export_as_zip=True,
    )

    print(f"\n自定义配置:")
    print(f"   格式: {custom_config.format}")
    print(f"   目录: {custom_config.output_dir}")
    print(f"   文件名模板: {custom_config.file_name_template}")
    print(f"   打包ZIP: {custom_config.export_as_zip}")

    # 获取输出路径
    output_path = custom_config.get_output_path("测试群", "group")
    print(f"   示例输出路径: {output_path}")


def example_full_workflow():
    """完整工作流程"""
    print("\n" + "=" * 50)
    print("示例 6: 完整工作流程")
    print("=" * 50)

    # 1. 配置导出设置
    set_export_dir("D:/QQ导出")
    set_export_format("HTML")

    # 2. 启动服务
    napcat_path = find_napcat_qce_path()
    if not napcat_path:
        print("❌ 未找到 NapCat-QCE")
        return

    with NapCatQCELauncher(napcat_path=napcat_path) as launcher:
        client = launcher.get_client()

        # 3. 获取群组列表
        groups = client.groups.get_all()
        print(f"找到 {len(groups)} 个群组")

        if groups:
            # 4. 导出第一个群的聊天记录
            group = groups[0]
            print(f"\n正在导出: {group.group_name}")

            task = client.messages.export(
                chat_type=ChatType.GROUP.value,
                peer_uid=group.group_code,
                format="HTML",
                session_name=group.group_name,
            )

            # 5. 等待完成
            result = client.tasks.wait_for_completion(
                task.id,
                timeout=300,
                on_progress=lambda t: print(f"\r   进度: {t.progress}%", end=""),
            )

            print(f"\n✅ 导出完成!")
            print(f"   消息数: {result.message_count}")
            print(f"   文件: {result.file_name}")


def main():
    print("NapCat-QCE 启动器示例")
    print("=" * 50)
    print("1. 基本启动器用法")
    print("2. 使用上下文管理器")
    print("3. 快速启动函数")
    print("4. 使用 run_with_napcat")
    print("5. 配置导出设置（不需要启动服务）")
    print("6. 完整工作流程")
    print()

    choice = input("请选择示例 (1-6): ").strip()

    if choice == "1":
        example_basic_launcher()
    elif choice == "2":
        example_context_manager()
    elif choice == "3":
        example_quick_start()
    elif choice == "4":
        example_run_with_napcat()
    elif choice == "5":
        example_export_config()
    elif choice == "6":
        example_full_workflow()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
