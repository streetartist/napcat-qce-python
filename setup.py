"""
NapCat-QCE Python SDK 安装脚本
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="napcat-qce",
    version="1.0.0",
    author="NapCat-QCE Contributors",
    author_email="",
    description="NapCat-QCE (QQ聊天记录导出工具) Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shuakami/qq-chat-exporter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "websocket": ["websocket-client>=1.0.0"],
        "async": ["aiohttp>=3.8.0", "websockets>=10.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.990",
        ],
    },
    keywords=[
        "qq",
        "chat",
        "export",
        "napcat",
        "qce",
        "message",
        "backup",
    ],
    project_urls={
        "Bug Reports": "https://github.com/shuakami/qq-chat-exporter/issues",
        "Source": "https://github.com/shuakami/qq-chat-exporter",
    },
)
