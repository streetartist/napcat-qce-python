"""
NapCat-QCE 启动器
================

通过 Python 启动和管理 NapCat-QCE 服务。
"""

import os
import sys
import time
import subprocess
import threading
import signal
import re
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
import ctypes

# Windows 命名管道支持
if sys.platform == "win32":
    import ctypes.wintypes

    # Windows API 常量
    GENERIC_READ = 0x80000000
    OPEN_EXISTING = 3
    FILE_FLAG_OVERLAPPED = 0x40000000
    INVALID_HANDLE_VALUE = -1
    ERROR_PIPE_BUSY = 231
    ERROR_MORE_DATA = 234

    kernel32 = ctypes.windll.kernel32

from .auto_token import get_token_from_config, get_config_dir
from .exceptions import NapCatQCEError


class LauncherError(NapCatQCEError):
    """启动器错误"""
    pass


def is_admin() -> bool:
    """检查是否以管理员权限运行"""
    if sys.platform == "win32":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def find_qq_path() -> Optional[str]:
    """
    自动查找 QQ 安装路径

    Returns:
        QQ.exe 路径，未找到返回 None
    """
    if sys.platform != "win32":
        return None

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\QQ"
        )
        uninstall_string, _ = winreg.QueryValueEx(key, "UninstallString")
        winreg.CloseKey(key)

        # 从卸载路径提取 QQ.exe 路径
        qq_dir = Path(uninstall_string).parent
        qq_exe = qq_dir / "QQ.exe"
        if qq_exe.exists():
            return str(qq_exe)
    except Exception:
        pass

    # 尝试常见路径
    common_paths = [
        Path(os.environ.get("ProgramFiles", "")) / "Tencent" / "QQNT" / "QQ.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Tencent" / "QQNT" / "QQ.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tencent" / "QQNT" / "QQ.exe",
    ]

    for path in common_paths:
        if path.exists():
            return str(path)

    return None


def find_napcat_qce_path() -> Optional[str]:
    """
    自动查找 NapCat-QCE 安装路径

    Returns:
        NapCat-QCE 目录路径，未找到返回 None
    """
    # 检查环境变量
    env_path = os.environ.get("NAPCAT_QCE_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # 检查常见位置
    search_paths = [
        # 当前目录
        Path.cwd() / "NapCat-QCE-Windows-x64",
        # 用户目录
        Path.home() / "NapCat-QCE-Windows-x64",
        # 上级目录
        Path.cwd().parent / "NapCat-QCE-Windows-x64",
        # D盘常见位置
        Path("D:/readqq/NapCat-QCE-Windows-x64"),
        Path("D:/NapCat-QCE-Windows-x64"),
    ]

    for path in search_paths:
        if path.exists() and (path / "NapCatWinBootMain.exe").exists():
            return str(path)

    return None


class NapCatQCELauncher:
    """
    NapCat-QCE 启动器

    用于启动、停止和管理 NapCat-QCE 服务。

    Example:
        >>> launcher = NapCatQCELauncher()
        >>> launcher.start()
        >>> # 等待服务就绪
        >>> launcher.wait_for_ready()
        >>> # 使用服务...
        >>> launcher.stop()
    """

    def __init__(
        self,
        napcat_path: Optional[str] = None,
        qq_path: Optional[str] = None,
        use_user_mode: bool = True,
        auto_login_uin: Optional[str] = None,
    ):
        """
        初始化启动器

        Args:
            napcat_path: NapCat-QCE 目录路径（None 时自动查找）
            qq_path: QQ.exe 路径（None 时自动查找）
            use_user_mode: 是否使用用户模式（不需要管理员权限）
            auto_login_uin: 自动登录的 QQ 号（可选）
        """
        self.napcat_path = napcat_path or find_napcat_qce_path()
        self.qq_path = qq_path or find_qq_path()
        self.use_user_mode = use_user_mode
        self.auto_login_uin = auto_login_uin

        self._process: Optional[subprocess.Popen] = None
        self._output_thread: Optional[threading.Thread] = None
        self._pipe_thread: Optional[threading.Thread] = None
        self._running = False
        self._ready = False
        self._token: Optional[str] = None
        self._pipe_name: Optional[str] = None
        self._pipe_handle = None

        # 输出回调
        self._on_output: Optional[Callable[[str], None]] = None
        self._on_ready: Optional[Callable[[str], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

        # 验证路径
        if not self.napcat_path:
            raise LauncherError(
                "未找到 NapCat-QCE 目录。请通过以下方式之一指定:\n"
                "1. 传入 napcat_path 参数\n"
                "2. 设置环境变量 NAPCAT_QCE_PATH\n"
                "3. 将 NapCat-QCE-Windows-x64 放在当前目录或用户目录"
            )

        if not self.qq_path:
            raise LauncherError(
                "未找到 QQ 安装路径。请通过以下方式之一指定:\n"
                "1. 传入 qq_path 参数\n"
                "2. 安装 QQ 客户端 (https://im.qq.com/)"
            )

    def on_output(self, callback: Callable[[str], None]) -> "NapCatQCELauncher":
        """设置输出回调"""
        self._on_output = callback
        return self

    def on_ready(self, callback: Callable[[str], None]) -> "NapCatQCELauncher":
        """设置就绪回调（收到令牌时触发）"""
        self._on_ready = callback
        return self

    def on_error(self, callback: Callable[[str], None]) -> "NapCatQCELauncher":
        """设置错误回调"""
        self._on_error = callback
        return self

    def _process_line(self, line: str):
        """处理单行输出"""
        line = line.strip()
        if not line:
            return

        # 检测命名管道重定向
        pipe_match = re.search(r'已重定向到命名管道:\s*(\\\\.\\pipe\\[^\s]+)', line)
        if pipe_match:
            self._pipe_name = pipe_match.group(1)
            # 启动命名管道读取线程
            self._pipe_thread = threading.Thread(target=self._read_named_pipe, daemon=True)
            self._pipe_thread.start()

        # 检测令牌输出
        if "访问令牌" in line or "Access Token" in line:
            # 尝试提取令牌
            parts = line.split(":")
            if len(parts) >= 2:
                self._token = parts[-1].strip()
                self._ready = True
                if self._on_ready:
                    self._on_ready(self._token)

        # 检测服务就绪（QQ聊天记录导出工具已启动）
        if "QQ聊天记录导出工具已启动" in line:
            self._ready = True
            if self._on_ready:
                self._on_ready(self._token)

        # 检测错误
        if "error" in line.lower() or "错误" in line:
            if self._on_error:
                self._on_error(line)

        # 输出回调
        if self._on_output:
            self._on_output(line)

    def _read_output(self):
        """读取进程输出"""
        if not self._process or not self._process.stdout:
            return

        for line in iter(self._process.stdout.readline, ""):
            if not self._running:
                break
            self._process_line(line)

    def _read_named_pipe(self):
        """从 Windows 命名管道读取输出"""
        if sys.platform != "win32" or not self._pipe_name:
            return

        # 等待管道可用
        time.sleep(0.5)

        try:
            # 打开命名管道
            handle = kernel32.CreateFileW(
                self._pipe_name,
                GENERIC_READ,
                0,
                None,
                OPEN_EXISTING,
                0,
                None
            )

            if handle == INVALID_HANDLE_VALUE:
                error = ctypes.get_last_error()
                if self._on_error:
                    self._on_error(f"无法连接到命名管道: 错误码 {error}")
                return

            self._pipe_handle = handle
            buffer = ctypes.create_string_buffer(4096)
            bytes_read = ctypes.wintypes.DWORD()
            partial_line = ""

            while self._running:
                success = kernel32.ReadFile(
                    handle,
                    buffer,
                    4096,
                    ctypes.byref(bytes_read),
                    None
                )

                if not success:
                    error = ctypes.get_last_error()
                    if error != ERROR_MORE_DATA:
                        break

                if bytes_read.value > 0:
                    try:
                        data = buffer.raw[:bytes_read.value].decode('utf-8', errors='replace')
                    except:
                        data = buffer.raw[:bytes_read.value].decode('gbk', errors='replace')

                    # 处理可能的多行数据
                    data = partial_line + data
                    lines = data.split('\n')

                    # 最后一个可能是不完整的行
                    partial_line = lines[-1]

                    for line in lines[:-1]:
                        self._process_line(line)

        except Exception as e:
            if self._on_error:
                self._on_error(f"命名管道读取错误: {e}")
        finally:
            if self._pipe_handle:
                kernel32.CloseHandle(self._pipe_handle)
                self._pipe_handle = None

    def start(self, wait_for_ready: bool = False, timeout: float = 60) -> bool:
        """
        启动 NapCat-QCE 服务

        Args:
            wait_for_ready: 是否等待服务就绪
            timeout: 等待超时时间（秒）

        Returns:
            是否启动成功
        """
        if self._running:
            return True

        napcat_dir = Path(self.napcat_path)

        # 选择启动脚本
        if self.use_user_mode:
            launcher_bat = napcat_dir / "launcher-user.bat"
            if not launcher_bat.exists():
                launcher_bat = napcat_dir / "launcher-win10-user.bat"
        else:
            launcher_bat = napcat_dir / "launcher.bat"

        if not launcher_bat.exists():
            raise LauncherError(f"启动脚本不存在: {launcher_bat}")

        # 构建命令
        cmd = [str(launcher_bat)]
        if self.auto_login_uin:
            cmd.append(self.auto_login_uin)

        # 设置环境变量
        env = os.environ.copy()
        env["NAPCAT_PATCH_PACKAGE"] = str(napcat_dir / "qqnt.json")
        env["NAPCAT_LOAD_PATH"] = str(napcat_dir / "loadNapCat.js")
        env["NAPCAT_INJECT_PATH"] = str(napcat_dir / "NapCatWinBootHook.dll")
        env["NAPCAT_LAUNCHER_PATH"] = str(napcat_dir / "NapCatWinBootMain.exe")
        env["NAPCAT_MAIN_PATH"] = str(napcat_dir / "napcat.mjs")

        try:
            # 启动进程
            self._process = subprocess.Popen(
                cmd,
                cwd=str(napcat_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )

            self._running = True

            # 启动输出读取线程
            self._output_thread = threading.Thread(target=self._read_output, daemon=True)
            self._output_thread.start()

            print(f"[Launcher] NapCat-QCE 已启动 (PID: {self._process.pid})")

            if wait_for_ready:
                return self.wait_for_ready(timeout)

            return True

        except Exception as e:
            raise LauncherError(f"启动失败: {e}")

    def wait_for_ready(self, timeout: float = 60) -> bool:
        """
        等待服务就绪

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否就绪
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._ready:
                return True
            if not self._running:
                return False
            time.sleep(0.5)
        return False

    def stop(self, force: bool = False):
        """
        停止 NapCat-QCE 服务

        Args:
            force: 是否强制终止
        """
        self._running = False

        if self._process:
            try:
                if force:
                    self._process.kill()
                else:
                    # 尝试优雅终止
                    if sys.platform == "win32":
                        self._process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        self._process.terminate()

                    # 等待进程结束
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self._process.kill()

                print("[Launcher] NapCat-QCE 已停止")
            except Exception as e:
                print(f"[Launcher] 停止时出错: {e}")
            finally:
                self._process = None

        self._ready = False
        self._token = None
        self._pipe_name = None

        # 关闭命名管道句柄
        if sys.platform == "win32" and self._pipe_handle:
            try:
                kernel32.CloseHandle(self._pipe_handle)
            except:
                pass
            self._pipe_handle = None

    def restart(self, wait_for_ready: bool = True, timeout: float = 60) -> bool:
        """
        重启服务

        Args:
            wait_for_ready: 是否等待就绪
            timeout: 超时时间

        Returns:
            是否成功
        """
        self.stop()
        time.sleep(2)
        return self.start(wait_for_ready, timeout)

    @property
    def is_running(self) -> bool:
        """服务是否正在运行"""
        if self._process:
            return self._process.poll() is None
        return False

    @property
    def is_ready(self) -> bool:
        """服务是否就绪"""
        return self._ready and self.is_running

    @property
    def token(self) -> Optional[str]:
        """获取访问令牌"""
        if self._token:
            return self._token
        # 尝试从配置文件读取
        return get_token_from_config()

    @property
    def pid(self) -> Optional[int]:
        """获取进程 ID"""
        if self._process:
            return self._process.pid
        return None

    def get_client(self, host: str = "localhost", port: int = 40653):
        """
        获取已连接的客户端

        Args:
            host: 服务器地址
            port: 服务器端口

        Returns:
            NapCatQCE 客户端实例
        """
        from .client import NapCatQCE

        token = self.token
        if not token:
            raise LauncherError("无法获取访问令牌，服务可能未就绪")

        return NapCatQCE(token=token, host=host, port=port)

    def __enter__(self) -> "NapCatQCELauncher":
        self.start(wait_for_ready=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def start_napcat_qce(
    napcat_path: Optional[str] = None,
    qq_path: Optional[str] = None,
    wait_for_ready: bool = True,
    timeout: float = 60,
    on_output: Optional[Callable[[str], None]] = None,
) -> NapCatQCELauncher:
    """
    快速启动 NapCat-QCE 服务

    Args:
        napcat_path: NapCat-QCE 目录路径
        qq_path: QQ.exe 路径
        wait_for_ready: 是否等待就绪
        timeout: 超时时间
        on_output: 输出回调

    Returns:
        启动器实例

    Example:
        >>> launcher = start_napcat_qce()
        >>> client = launcher.get_client()
        >>> groups = client.groups.get_all()
        >>> launcher.stop()
    """
    launcher = NapCatQCELauncher(napcat_path=napcat_path, qq_path=qq_path)

    if on_output:
        launcher.on_output(on_output)

    launcher.start(wait_for_ready=wait_for_ready, timeout=timeout)
    return launcher


def run_with_napcat(
    func: Callable,
    napcat_path: Optional[str] = None,
    qq_path: Optional[str] = None,
    timeout: float = 60,
):
    """
    在 NapCat-QCE 环境中运行函数

    自动启动服务，执行函数，然后停止服务。

    Args:
        func: 要执行的函数，接收 client 参数
        napcat_path: NapCat-QCE 目录路径
        qq_path: QQ.exe 路径
        timeout: 启动超时时间

    Example:
        >>> def my_task(client):
        ...     groups = client.groups.get_all()
        ...     print(f"共有 {len(groups)} 个群组")
        >>>
        >>> run_with_napcat(my_task)
    """
    with NapCatQCELauncher(napcat_path=napcat_path, qq_path=qq_path) as launcher:
        client = launcher.get_client()
        try:
            func(client)
        finally:
            client.close()
