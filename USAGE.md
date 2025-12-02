# SteamDT MCP 使用指南

## 📋 目录

- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/Kir4kami/mcp-steamdt.git
cd mcp-steamdt

# 安装依赖（推荐使用虚拟环境）
python -m venv .venv
.venv\Scripts\activate  # Windows
# 或 source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. 获取 API 密钥

1. 访问 [SteamDT 官网](https://steamdt.com)
2. 注册账号并登录
3. 进入「个人中心 - API 管理」
4. 申请并复制你的 `API_KEY`

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
STEAMDT_API_KEY=你的密钥
STEAMDT_BASE_URL=https://open.steamdt.com
```

### 4. 配置 MCP 客户端

#### Claude Desktop

1. 找到配置文件：
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. 编辑配置文件，添加：

```json
{
  "mcpServers": {
    "steamdt": {
      "command": "python",
      "args": ["-m", "steamdt_mcp.server"],
      "env": {
        "STEAMDT_API_KEY": "你的密钥",
        "STEAMDT_BASE_URL": "https://open.steamdt.com"
      }
    }
  }
}
```

> **提示**：如果使用虚拟环境，将 `command` 改为虚拟环境中 Python 的完整路径

3. 重启 Claude Desktop

## 📖 使用示例

### 查询单个饰品价格

```
用户: 查询 AWP | Pit Viper (Minimal Wear) 的价格

AI: [自动调用 get_item_price]
    查询结果显示：
    - C5 平台：在售价格 8.98，在售数量 723
    - BUFF 平台：在售价格 9.20，在售数量 156
    ...
```

### 批量查询价格

```
用户: 批量查询这几个饰品的价格：
     1. AK-47 | Redline (Field-Tested)
     2. M4A4 | Howl (Factory New)
     3. AWP | Dragon Lore (Factory New)

AI: [自动调用 get_item_prices_batch]
    批量查询结果：
    1. AK-47 | Redline (Field-Tested) - 最低价 45.6 (C5)
    2. M4A4 | Howl (Factory New) - 最低价 1234.5 (BUFF)
    3. AWP | Dragon Lore (Factory New) - 最低价 5678.9 (C5)
```

### 查询磨损度

```
用户: 通过这个检视链接查询磨损度：
     steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S...

AI: [自动调用 get_item_wear_by_inspect_url]
    查询已提交，taskId: xxxxx
    请稍后查询结果...
```

### 查找饰品基础信息

```
用户: 帮我找一个叫 "Dragon Lore" 的 AWP 皮肤

AI: [自动调用 get_item_base_info]
    找到了以下匹配的饰品：
    - AWP | Dragon Lore (Factory New)
    - AWP | Dragon Lore (Minimal Wear)
    ...
```

## 🔧 详细配置

### 使用虚拟环境（推荐）

如果使用虚拟环境，需要修改配置中的 `command` 路径：

**Windows:**
```json
{
  "command": "F:\\mymcp\\mcp-steamdt\\.venv\\Scripts\\python.exe"
}
```

**macOS/Linux:**
```json
{
  "command": "/path/to/mcp-steamdt/.venv/bin/python"
}
```

### 环境变量说明

- `STEAMDT_API_KEY`（必需）：你的 SteamDT API 密钥
- `STEAMDT_BASE_URL`（可选）：API 基础 URL，默认 `https://open.steamdt.com`

## ❓ 常见问题

### Q1: 如何确认 MCP 是否正常工作？

**A:** 在项目目录运行：
```bash
python -m steamdt_mcp.server
```

如果看到服务器启动且没有报错，说明配置正确。然后重启你的 MCP 客户端。

### Q2: Claude Desktop 找不到配置文件？

**A:** 
- Windows: 按 `Win+R`，输入 `%APPDATA%\Claude`，回车
- macOS: 打开 Finder，按 `Cmd+Shift+G`，输入 `~/Library/Application Support/Claude`
- Linux: `~/.config/Claude/`

如果目录不存在，先启动一次 Claude Desktop，它会自动创建。

### Q3: 如何更新基础信息缓存？

**A:** 基础信息接口每天只能调用一次，会自动缓存。如果需要强制刷新：

1. 等待第二天再调用
2. 或调用时设置 `force_refresh=True`（但需等待第二天才能再次调用 API）

### Q4: 批量查询有限制吗？

**A:** 批量查询接口每分钟只能调用 1 次。建议每次查询不超过 10-20 个饰品。

### Q5: 磨损度查询返回 taskId 是什么意思？

**A:** 某些查询是异步的，返回 `taskId` 表示任务已提交。你可以：
- 通过 `taskId` 查询结果（如果 SteamDT 提供查询接口）
- 等待回调通知（如果配置了 `notifyUrl`）

### Q6: 支持哪些 MCP 客户端？

**A:** 理论上支持所有符合 MCP 协议的客户端，包括：
- Claude Desktop
- Cursor IDE
- 其他支持 MCP 的 IDE 和工具

### Q7: 如何测试工具是否正常工作？

**A:** 运行项目自带的测试脚本：
```bash
python test_all_tools.py
```

## 📚 更多资源

- [SteamDT 官方文档](https://doc.steamdt.com/)
- [MCP 协议文档](https://modelcontextprotocol.io/)
- [项目 Issues](https://github.com/Kir4kami/mcp-steamdt/issues)

## 🤝 贡献

欢迎提交 Issue 和 PR！

