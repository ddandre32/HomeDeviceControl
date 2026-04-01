#!/bin/bash
# Home Device Control Skill 安装脚本
# 整合 miot SDK，提供完整的智能家居控制

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

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 安装依赖
echo "📦 安装依赖..."
pip install -q aiohttp cryptography pycryptodome click pyyaml

# 安装 Skill
echo "📦 安装 Home Device Control Skill..."
cd "$SCRIPT_DIR"
pip install -e "."

# 创建配置目录
mkdir -p ~/.home-device-control
mkdir -p ~/.miot/cache

# 复制默认配置
if [ ! -f ~/.miot/config.json ]; then
    echo "📝 创建默认配置..."
    cat > ~/.miot/config.json << 'EOF'
{
  "uuid": null,
  "redirect_uri": "https://mico.api.mijia.tech/login_redirect",
  "cache_path": "~/.miot/cache",
  "cloud_server": "cn",
  "oauth_info": null,
  "format": null
}
EOF
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "使用说明:"
echo "  1. 运行 'home-device doctor' 检查状态"
echo "  2. 运行 'home-device auth' 完成小米认证"
echo "  3. 运行 'home-device list' 列出设备"
echo "  4. 运行 'home-device control <device_id> turn_on' 控制设备"
echo ""
echo "或使用 Python API:"
echo "  from channels import get_channel"
echo "  xiaomi = get_channel('xiaomi')"
echo "  devices = xiaomi.list_devices()"
echo ""
