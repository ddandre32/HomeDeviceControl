# OpenClaw Skill 技术架构设计规范

> 基于 Agent Reach 等优秀开源 Skill 项目的架构分析总结

---

## 📐 核心设计原则

### 1. 脚手架而非框架 (Scaffolding, not Framework)

**❌ 反模式**: Skill 包装所有功能，Agent 通过 Skill 的 API 间接调用底层工具

**✅ 最佳实践**: Skill 只做安装、配置、路由，Agent 直接调用上游工具

```
❌ 框架模式 (不推荐)
Agent → Skill API → 内部封装 → 底层工具

✅ 脚手架模式 (推荐)
Agent → 直接调用上游工具 (yt-dlp, gh, bird 等)
      ↳ Skill 只负责: 安装引导 + 配置管理 + 使用文档
```

**为什么**:
- 减少中间层，降低复杂度和出错概率
- Agent 直接掌握完整工具能力，不受 Skill 封装限制
- 用户可以随时替换底层工具，不受 Skill 绑定

---

## 🏗️ 目录结构规范

```
skill-name/
├── SKILL.md                 # 主入口文档 (必须)
├── README.md               # 项目说明 (可选)
├── install.sh              # 安装脚本 (推荐)
├── config.yaml / config.json   # 配置文件 (可选)
│
├── skill.json              # OpenClaw 工具定义 (如需要)
├── skill.py                # 主程序 (如需要)
│
├── channels/               # 渠道/平台适配器 (推荐)
│   ├── __init__.py        # 渠道注册
│   ├── web.py             # 网页渠道
│   ├── twitter.py         # 推特渠道
│   └── ...
│
├── guides/                 # 安装指南 (推荐)
│   ├── install.md
│   ├── configure.md
│   └── troubleshoot.md
│
├── integrations/           # 第三方集成 (可选)
│   ├── mcp/               # MCP 服务配置
│   └── cli/               # CLI 工具封装
│
├── references/             # 详细参考文档 (推荐)
│   ├── search.md
│   ├── social.md
│   └── ...
│
├── scripts/                # 辅助脚本 (可选)
│   └── setup.sh
│
└── utils/                  # 工具函数 (可选)
    └── helpers.py
```

---

## 📄 SKILL.md 设计规范

### 结构模板

```markdown
# Skill 名称

## Metadata

| 字段 | 值 |
|------|-----|
| name | skill-name |
| description | 一句话描述 Skill 功能 |
| version | 1.0.0 |

## Triggers (触发词)

定义 Agent 何时应该使用这个 Skill：

| 意图 | 关键词 | 路由 |
|------|--------|------|
| 搜索 | 搜/查/找/search | references/search.md |
| 社交 | 小红书/抖音/推特 | references/social.md |
| 开发 | github/代码/仓库 | references/dev.md |

## Quick Start

### 安装
```bash
./install.sh
```

### 常用命令
```bash
# 命令1
command1

# 命令2
command2
```

## 路由表

| 用户意图 | 详细文档 |
|---------|---------|
| 意图A | references/a.md |
| 意图B | references/b.md |

## 注意事项
- 不要在 agent workspace 创建文件
- 使用 /tmp/ 存放临时输出
- 使用 ~/.skill-name/ 存放持久数据
```

### 关键要素

1. **Triggers**: 明确的关键词触发器，帮助 Agent 识别何时使用该 Skill
2. **路由表**: 复杂 Skill 应该分模块文档，通过路由表引导 Agent 阅读
3. **Quick Commands**: 最常用的 3-5 个命令，Agent 可以直接使用
4. **Constraints**: 明确告诉 Agent 什么不该做

---

## 🔧 安装脚本设计规范

### 职责分离

```bash
#!/bin/bash
# install.sh

set -e

echo "🔧 安装 Skill: xxx"

# 1. 检测环境
detect_environment() {
    # 检测操作系统
    # 检测是否已安装依赖
    # 检测是本地还是服务器环境
}

# 2. 安装系统依赖
install_system_deps() {
    # Node.js, Python 包等
    # 使用包管理器或提供手动安装指引
}

# 3. 安装 CLI 工具
install_cli_tools() {
    # pip install xxx
    # npm install -g xxx
}

# 4. 配置 MCP 服务 (如需要)
setup_mcp() {
    # mcporter config add ...
}

# 5. 注册 Skill 文档
register_skill() {
    # 复制 SKILL.md 到 ~/.openclaw/skills/
}

# 6. 诊断检查
run_doctor() {
    # 检查每个渠道是否可用
    # 输出状态报告
}

main() {
    detect_environment
    install_system_deps
    install_cli_tools
    setup_mcp
    register_skill
    run_doctor
}

main "$@"
```

### 设计要点

1. **幂等性**: 多次运行不会出错或重复安装
2. **环境检测**: 自动识别本地/服务器、已安装/未安装
3. **渐进式**: 核心功能无需配置即可用，高级功能逐步引导配置
4. **诊断报告**: 安装完成后输出每个组件的状态

---

## 🔌 渠道 (Channel) 设计规范

### 渠道抽象

每个渠道是一个独立的适配器，负责：
1. **检测**: 检查上游工具是否可用
2. **配置**: 引导用户完成配置（如需要）
3. **路由**: 提供使用该渠道的最佳实践

```python
# channels/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class Channel(ABC):
    """渠道基类"""
    
    name: str = ""
    description: str = ""
    
    @abstractmethod
    def check(self) -> Dict[str, Any]:
        """检查渠道是否可用"""
        pass
    
    @abstractmethod
    def configure(self) -> bool:
        """引导配置"""
        pass
    
    def get_usage(self) -> str:
        """获取使用指南"""
        return f"使用 {self.name}: ..."

# channels/twitter.py
class TwitterChannel(Channel):
    name = "twitter"
    description = "Twitter/X 平台"
    
    def check(self):
        # 检查 bird CLI 是否安装
        # 检查 cookie 是否配置
        return {
            "available": True/False,
            "configured": True/False,
            "message": "状态说明"
        }
    
    def configure(self):
        # 引导用户获取 cookie
        # 保存配置
        pass
```

### 渠道注册

```python
# channels/__init__.py
from .twitter import TwitterChannel
from .youtube import YouTubeChannel
# ...

CHANNELS = {
    "twitter": TwitterChannel,
    "youtube": YouTubeChannel,
    # ...
}

def get_channel(name: str) -> Channel:
    return CHANNELS.get(name)()

def check_all() -> Dict[str, Any]:
    """检查所有渠道状态"""
    results = {}
    for name, channel_class in CHANNELS.items():
        channel = channel_class()
        results[name] = channel.check()
    return results
```

---

## 🩺 诊断工具设计规范

### doctor 命令

每个 Skill 应该提供诊断命令，输出所有组件的状态：

```bash
$ skill-name doctor

🩺 Skill 健康检查
==================

渠道状态:
  ✅ web        - Jina Reader 可用
  ✅ youtube    - yt-dlp 已安装
  ⚠️  twitter    - bird 已安装但未配置 cookie
  ❌ xiaohongshu - Docker 未安装

配置状态:
  ✅ ~/.skill-name/config.yaml 存在
  ✅ Cookie 文件权限正确 (600)

建议:
  1. 运行 `skill-name configure twitter` 配置推特
  2. 安装 Docker 以使用小红书功能
```

### 实现要点

1. **分级状态**: ✅ 可用 / ⚠️ 需配置 / ❌ 未安装
2. **具体建议**: 不只是报问题，还要给解决方案
3. **自动化检查**: 尽量自动检测，减少用户手动操作

---

## 🔐 安全设计规范

### 凭据管理

```
❌ 错误做法
- 凭据硬编码在代码中
- 凭据上传到 Git
- 凭据通过日志输出

✅ 正确做法
- 凭据存储在 ~/.skill-name/config.yaml
- 文件权限设置为 600 (仅所有者可读写)
- 敏感信息打码输出
```

### 配置示例

```yaml
# ~/.skill-name/config.yaml
version: "1.0"

credentials:
  twitter:
    cookies: "xxx"  # 加密存储或明文但权限控制
    
settings:
  default_timeout: 30
  cache_enabled: true
```

### 安全模式

```bash
# 安全模式：只检测，不自动修改系统
skill-name install --safe

# 预览模式：显示将要做什么，但不执行
skill-name install --dry-run
```

---

## 📚 文档设计规范

### 分层文档结构

```
skill-name/
├── SKILL.md              # 入口文档 (1页，快速上手)
├── references/
│   ├── search.md         # 搜索功能详细说明
│   ├── social.md         # 社交媒体功能
│   └── dev.md            # 开发工具功能
└── guides/
    ├── install.md        # 安装指南
    ├── configure.md      # 配置指南
    └── troubleshoot.md   # 故障排除
```

### 文档原则

1. **SKILL.md 要薄**: 只包含最常用的信息，详细内容分到 references/
2. **路由清晰**: 告诉 Agent 什么情况下读哪个文档
3. **示例丰富**: 每个功能都要有具体命令示例
4. **约束明确**: 告诉 Agent 什么不该做

---

## 🔄 更新机制设计规范

### 版本检查

```bash
# 检查更新
skill-name update check

# 执行更新
skill-name update
```

### 更新脚本

```bash
#!/bin/bash
# update.sh

echo "🔄 检查更新..."

# 1. 获取远程版本
REMOTE_VERSION=$(curl -s https://raw.githubusercontent.com/xxx/main/version.txt)
LOCAL_VERSION=$(cat ~/.skill-name/version)

# 2. 比较版本
if [ "$REMOTE_VERSION" != "$LOCAL_VERSION" ]; then
    echo "发现新版本: $REMOTE_VERSION"
    
    # 3. 下载更新
    curl -sL https://raw.githubusercontent.com/xxx/main/install.sh | bash
    
    echo "✅ 更新完成"
else
    echo "✅ 已是最新版本"
fi
```

---

## 🎯 总结：优秀 Skill 的特征

| 特征 | 说明 |
|------|------|
| **薄封装** | Skill 只做安装和路由，不包装底层工具 |
| **自诊断** | 提供 doctor 命令，自动检测所有组件状态 |
| **渐进式** | 核心功能开箱即用，高级功能逐步引导配置 |
| **分层文档** | SKILL.md 薄而精，详细文档分模块存放 |
| **安全第一** | 凭据本地存储，权限严格控制 |
| **幂等安装** | 多次安装不会出错，更新平滑 |

---

## ❌ 常见反模式

### 1. 过度封装
```python
# ❌ 不好：Skill 包装所有 API
class MySkill:
    def search(self, query):
        return api.search(query)

# ✅ 好：Agent 直接调用上游工具
# Agent 读取 SKILL.md 后，直接运行: gh search repos "query"
```

### 2. 单一大文件
```
# ❌ 不好
skill/
└── skill.py (3000行，包含所有功能)

# ✅ 好
skill/
├── channels/          # 按渠道拆分
├── guides/           # 按主题拆分
└── references/       # 按功能拆分
```

### 3. 缺少诊断
```bash
# ❌ 不好
$ skill-name
Error: something went wrong

# ✅ 好
$ skill-name doctor
✅ Component A: OK
⚠️  Component B: Needs configuration
   Run: skill-name configure b
```

---

*本规范基于 Agent Reach 等优秀开源 Skill 项目分析总结*
