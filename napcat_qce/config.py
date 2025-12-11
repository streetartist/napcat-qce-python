"""
NapCat-QCE 配置管理
==================

管理导出配置，包括文件格式、保存位置等。
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field, asdict

from .types import ExportFormat
from .auto_token import get_config_dir


@dataclass
class ExportConfig:
    """
    导出配置

    控制聊天记录导出的各种设置。
    """

    # 导出格式
    format: str = "HTML"

    # 保存位置
    output_dir: Optional[str] = None  # None 时使用默认位置

    # 文件命名
    file_name_template: str = "{name}_{date}"  # 支持变量: {name}, {date}, {time}, {type}

    # 资源处理
    include_resources: bool = True  # 是否下载图片/视频等资源
    resource_folder: str = "resources"  # 资源文件夹名称

    # 消息处理
    batch_size: int = 5000  # 每批处理消息数
    include_system_messages: bool = True  # 包含系统消息
    include_recalled_messages: bool = False  # 包含撤回消息

    # 格式化选项
    pretty_format: bool = True  # JSON 美化输出
    encoding: str = "utf-8"  # 文件编码

    # ZIP 打包
    export_as_zip: bool = False  # 是否打包为 ZIP
    delete_original_after_zip: bool = False  # ZIP 后删除原文件

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_export_options(self):
        """转换为 ExportOptions"""
        from .types import ExportOptions
        return ExportOptions(
            batch_size=self.batch_size,
            include_resource_links=self.include_resources,
            include_system_messages=self.include_system_messages,
            pretty_format=self.pretty_format,
            export_as_zip=self.export_as_zip,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportConfig":
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def get_output_path(self, name: str, chat_type: str = "group") -> str:
        """
        获取输出文件路径

        Args:
            name: 会话名称
            chat_type: 聊天类型 (group/private)

        Returns:
            完整文件路径
        """
        from datetime import datetime

        # 确定输出目录
        if self.output_dir:
            output_dir = Path(self.output_dir)
        else:
            output_dir = get_config_dir() / "exports"

        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        now = datetime.now()
        file_name = self.file_name_template.format(
            name=self._sanitize_filename(name),
            date=now.strftime("%Y%m%d"),
            time=now.strftime("%H%M%S"),
            type=chat_type,
        )

        # 添加扩展名
        ext = self._get_extension()
        if self.export_as_zip:
            ext = "zip"

        return str(output_dir / f"{file_name}.{ext}")

    def _get_extension(self) -> str:
        """获取文件扩展名"""
        format_lower = self.format.lower()
        if format_lower == "excel":
            return "xlsx"
        return format_lower

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        return name.strip()


class ConfigManager:
    """
    配置管理器

    管理全局和项目级别的配置。

    Example:
        >>> config_manager = ConfigManager()
        >>> config = config_manager.get_export_config()
        >>> config.format = "JSON"
        >>> config.output_dir = "D:/exports"
        >>> config_manager.save_export_config(config)
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置目录（None 时使用默认目录）
        """
        self.config_dir = Path(config_dir) if config_dir else get_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._export_config_path = self.config_dir / "export_config.json"
        self._export_config: Optional[ExportConfig] = None

    def get_export_config(self) -> ExportConfig:
        """
        获取导出配置

        Returns:
            导出配置对象
        """
        if self._export_config:
            return self._export_config

        if self._export_config_path.exists():
            try:
                with open(self._export_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._export_config = ExportConfig.from_dict(data)
            except Exception as e:
                print(f"[ConfigManager] 加载配置失败: {e}")
                self._export_config = ExportConfig()
        else:
            self._export_config = ExportConfig()

        return self._export_config

    def save_export_config(self, config: Optional[ExportConfig] = None):
        """
        保存导出配置

        Args:
            config: 配置对象（None 时保存当前配置）
        """
        if config:
            self._export_config = config

        if self._export_config:
            with open(self._export_config_path, "w", encoding="utf-8") as f:
                json.dump(self._export_config.to_dict(), f, ensure_ascii=False, indent=2)

    def reset_export_config(self):
        """重置导出配置为默认值"""
        self._export_config = ExportConfig()
        self.save_export_config()

    def set_output_dir(self, path: str):
        """
        设置导出目录

        Args:
            path: 目录路径
        """
        config = self.get_export_config()
        config.output_dir = path
        self.save_export_config()

    def set_format(self, format: Union[str, ExportFormat]):
        """
        设置导出格式

        Args:
            format: 格式 (HTML, JSON, TXT, EXCEL)
        """
        config = self.get_export_config()
        if isinstance(format, ExportFormat):
            config.format = format.value.upper()
        else:
            config.format = format.upper()
        self.save_export_config()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_export_config() -> ExportConfig:
    """获取导出配置"""
    return get_config_manager().get_export_config()


def set_export_dir(path: str):
    """
    设置导出目录

    Args:
        path: 目录路径

    Example:
        >>> from napcat_qce import set_export_dir
        >>> set_export_dir("D:/我的QQ聊天记录")
    """
    get_config_manager().set_output_dir(path)


def set_export_format(format: Union[str, ExportFormat]):
    """
    设置导出格式

    Args:
        format: 格式 (HTML, JSON, TXT, EXCEL)

    Example:
        >>> from napcat_qce import set_export_format
        >>> set_export_format("JSON")
    """
    get_config_manager().set_format(format)
