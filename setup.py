#!/usr/bin/env python3
"""
HomeDeviceControl Skill Setup
整合 XMIoT SDK，提供完整的智能家居控制功能
"""

from setuptools import setup, find_packages

setup(
    name="home-device-control",
    version="2.0.0",
    description="控制智能家居设备的原子工具，支持小米、海尔等多品牌",
    author="OpenClaw",
    author_email="",
    url="https://github.com/ddandre32/HomeDeviceControl",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "aiohttp>=3.8.0",
        "cryptography>=3.0",
        "pycryptodome>=3.15.0",
        "click>=8.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "home-device=cli:main",
            "miot=cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
