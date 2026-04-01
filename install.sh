#!/bin/bash
# Home Device Control Skill 安装脚本

set -e

echo "🚀 安装 Home Device Control Skill..."
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "❌ 需要 Python 3.9+，当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本检查通过: $PYTHON_VERSION"

# 检查并安装 XMIoT
if ! command -v miot &> /dev/null; then
    echo "📦 安装 XMIoT CLI..."
    
    XMIOT_DIR="${HOME}/Documents/openclaw_lab/xiaomi_iot_new"
    if [ ! -d "$XMIOT_DIR" ]; then
        git clone --depth 1 -b master https://github.com/ddandre32/XMIoT.git "$XMIOT_DIR"
    fi
    
    cd "$XMIOT_DIR"
    pip install -e "."
    
    echo "✅ XMIoT 安装完成"
else
    echo "✅ XMIoT 已安装"
fi

# 安装 Skill
echo "📦 安装 Home Device Control Skill..."
SKILL_DIR="${HOME}/Documents/openclaw_lab/skills/HomeDeviceControl"
OPENCLAW_SKILL_DIR="${HOME}/.openclaw/skills/smart-home"

if [ -d "$SKILL_DIR" ]; then
    mkdir -p "$OPENCLAW_SKILL_DIR"
    cp -r "$SKILL_DIR"/* "$OPENCLAW_SKILL_DIR/"
    echo "✅ Skill 已安装到: $OPENCLAW_SKILL_DIR"
else
    echo "⚠️  Skill 目录不存在: $SKILL_DIR"
    exit 1
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "下一步:"
echo "1. 运行 'python3 /Users/Laura/Documents/openclaw_lab/skills/HomeDeviceControl/doctor.py' 检查渠道状态"
echo "2. 运行 'miot system oauth-url' 获取小米授权链接"
echo "3. 获取授权码后运行 'miot system auth <code>'"
echo ""
echo "使用示例:"
echo "  python3 cli.py list-devices"
echo "  python3 cli.py control <device_id> turn_on"
echo "  python3 cli.py execute-scene <scene_id>"
echo ""
