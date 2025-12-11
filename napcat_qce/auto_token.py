"""
NapCat-QCE 自动令牌获取
=====================

自动从本地配置文件或服务器获取访问令牌。
"""

import json
import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any

from .exceptions import AuthenticationError


def get_config_dir() -> Path:
    """
    获取 NapCat-QCE 配置目录

    Returns:
        配置目录路径
    """
    if platform.system() == "Windows":
        # Windows: %USERPROFILE%\.qq-chat-exporter
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            return Path(user_profile) / ".qq-chat-exporter"
    else:
        # Linux/macOS: ~/.qq-chat-exporter
        home = os.environ.get("HOME", "")
        if home:
            return Path(home) / ".qq-chat-exporter"

    # 回退到当前目录
    return Path(".qq-chat-exporter")


def get_security_config_path() -> Path:
    """
    获取安全配置文件路径

    Returns:
        security.json 文件路径
    """
    return get_config_dir() / "security.json"


def load_security_config() -> Optional[Dict[str, Any]]:
    """
    加载安全配置文件

    Returns:
        配置字典，如果文件不存在则返回 None
    """
    config_path = get_security_config_path()

    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[AutoToken] 读取配置文件失败: {e}")
        return None


def get_token_from_config() -> Optional[str]:
    """
    从本地配置文件获取访问令牌

    Returns:
        访问令牌，如果不存在则返回 None
    """
    config = load_security_config()
    if config:
        return config.get("accessToken")
    return None


def get_server_host_from_config() -> Optional[str]:
    """
    从本地配置文件获取服务器地址

    Returns:
        服务器地址，如果不存在则返回 None
    """
    config = load_security_config()
    if config:
        return config.get("serverHost")
    return None


def auto_discover_token(
    host: str = "localhost",
    port: int = 40653,
    try_local_config: bool = True,
) -> Optional[str]:
    """
    自动发现访问令牌

    尝试顺序:
    1. 从本地配置文件读取（如果 try_local_config=True）
    2. 从环境变量 NAPCAT_QCE_TOKEN 读取

    Args:
        host: 服务器地址（用于验证）
        port: 服务器端口
        try_local_config: 是否尝试从本地配置文件读取

    Returns:
        访问令牌，如果无法获取则返回 None
    """
    # 1. 尝试从环境变量获取
    env_token = os.environ.get("NAPCAT_QCE_TOKEN")
    if env_token:
        print("[AutoToken] 从环境变量获取令牌")
        return env_token

    # 2. 尝试从本地配置文件获取
    if try_local_config:
        local_token = get_token_from_config()
        if local_token:
            print(f"[AutoToken] 从本地配置文件获取令牌: {get_security_config_path()}")
            return local_token

    return None


def create_client_with_auto_token(
    host: str = "localhost",
    port: int = 40653,
    token: Optional[str] = None,
    auto_discover: bool = True,
    **kwargs,
):
    """
    创建带有自动令牌发现的客户端

    Args:
        host: 服务器地址
        port: 服务器端口
        token: 手动指定的令牌（优先级最高）
        auto_discover: 是否自动发现令牌
        **kwargs: 传递给 NapCatQCE 的其他参数

    Returns:
        NapCatQCE 客户端实例

    Raises:
        AuthenticationError: 无法获取令牌
    """
    # 延迟导入避免循环依赖
    from .client import NapCatQCE

    # 确定令牌
    final_token = token
    if not final_token and auto_discover:
        final_token = auto_discover_token(host, port)

    if not final_token:
        raise AuthenticationError(
            "无法获取访问令牌。请通过以下方式之一提供令牌:\n"
            "1. 直接传入 token 参数\n"
            "2. 设置环境变量 NAPCAT_QCE_TOKEN\n"
            "3. 确保 NapCat-QCE 服务在本机运行（将自动读取配置文件）"
        )

    return NapCatQCE(token=final_token, host=host, port=port, **kwargs)


class AutoTokenClient:
    """
    自动令牌客户端包装器

    自动从本地配置或环境变量获取令牌，简化客户端创建。

    Example:
        >>> # 最简单的用法 - 自动获取令牌
        >>> client = AutoTokenClient()
        >>>
        >>> # 指定服务器地址
        >>> client = AutoTokenClient(host="192.168.1.100")
        >>>
        >>> # 使用
        >>> groups = client.groups.get_all()
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 40653,
        token: Optional[str] = None,
        auto_discover: bool = True,
        **kwargs,
    ):
        """
        初始化自动令牌客户端

        Args:
            host: 服务器地址（None 时尝试从配置读取）
            port: 服务器端口
            token: 手动指定的令牌
            auto_discover: 是否自动发现令牌
            **kwargs: 传递给 NapCatQCE 的其他参数
        """
        # 尝试从配置获取服务器地址
        if host is None:
            config_host = get_server_host_from_config()
            host = config_host if config_host else "localhost"

        self._client = create_client_with_auto_token(
            host=host,
            port=port,
            token=token,
            auto_discover=auto_discover,
            **kwargs,
        )

    def __getattr__(self, name):
        """代理所有属性访问到内部客户端"""
        return getattr(self._client, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()

    @property
    def client(self):
        """获取内部客户端实例"""
        return self._client


# 便捷函数
def connect(
    host: Optional[str] = None,
    port: int = 40653,
    token: Optional[str] = None,
) -> "AutoTokenClient":
    """
    快速连接到 NapCat-QCE 服务器

    自动从本地配置文件或环境变量获取令牌。

    Args:
        host: 服务器地址（None 时自动检测）
        port: 服务器端口
        token: 手动指定的令牌（可选）

    Returns:
        客户端实例

    Example:
        >>> from napcat_qce import connect
        >>> client = connect()
        >>> groups = client.groups.get_all()
    """
    return AutoTokenClient(host=host, port=port, token=token)
