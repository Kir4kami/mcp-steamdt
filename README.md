## SteamDT MCP (Python)

一个基于 Python 的 SteamDT 行情 / 数据分析 MCP 服务端，用于让支持 MCP 的大模型（如 Claude 等）可以直接调用 SteamDT 的开放接口，查询饰品行情并做基础分析。

### 前置要求

- Python 3.10 或更高版本
- 已安装 git（用于方式一安装）
- SteamDT API 密钥（在 [SteamDT 官网](https://steamdt.com) 注册后获取）

### 快速开始

#### 最简单的方式（推荐）✨

1. **直接从 GitHub 安装**
   ```bash
   pip install git+https://github.com/Kir4kami/mcp-steamdt.git
   ```

2. **在 MCP 客户端中配置**
   
   编辑 Claude Desktop 配置文件（或其他 MCP 客户端），添加：
   ```json
   {
     "mcpServers": {
       "steamdt": {
         "command": "python",
         "args": ["-m", "steamdt_mcp.server"],
         "env": {
           "STEAMDT_API_KEY": "你的密钥"
         }
       }
     }
   }
   ```

3. **开始使用**
   
   重启客户端后，就可以在对话中让 AI 查询饰品价格、磨损度等信息了！

> **提示**：`pip install git+...` 会自动下载并安装最新版本，无需手动克隆仓库。

#### 开发模式（需要修改代码）

如果你想修改代码或参与开发，可以克隆仓库后按照 [安装](#安装) 部分的说明进行配置。

> ⚠️ 注意：
> - 本项目未内置你的 API 密钥，也不会帮你绕过任何平台限制。请在遵守 SteamDT 官方服务条款的前提下使用。
> - 本项目**只提供数据获取与基础统计功能，不做任何主观推荐或投资建议**；如何解读和使用这些数据，应由上层应用或用户自行决定。

### 功能概览

#### 基础信息与价格查询
- `get_item_base_info`：获取所有饰品的基础信息（名称、marketHashName 等）。**自动管理本地缓存**，首次调用会请求 API 并保存，后续优先使用缓存，无需担心每天限 1 次的限制。
- `search_item_by_name`：根据中文名或英文名搜索饰品，返回匹配的 `market_hash_name`。特别适合只知道中文名的情况。
- `get_item_price`：根据 `market_hash_name` 查询单个饰品的当前价格信息（每分钟60次）。
- `get_item_prices_batch`：批量查询多个饰品的价格信息（每分钟1次）。
- `get_item_price_history`：查询指定饰品最近若干天的价格历史（30天均价数据）。

#### 磨损度查询
- `get_item_wear_by_inspect_url`：通过检视链接查询饰品的磨损度相关数据（每小时36000次）。
- `get_item_wear_by_asmd`：通过 ASMD 参数查询饰品的磨损度相关数据（每小时36000次）。

#### 价格历史查询
- `get_item_price_history`：查询最近若干天的价格历史数据（30天均价）。根据 `market_hash_name` 和 `days` 参数查询各平台的30天平均价格。

> 所有接口均基于 SteamDT 官方文档实现：`https://doc.steamdt.com/`。权限限制请参考官方文档。

### 安装

#### 方式一：直接从 GitHub 安装（推荐，最简单）✨

无需克隆仓库，直接用 pip 从 GitHub 安装：

```bash
pip install git+https://github.com/Kir4kami/mcp-steamdt.git
```

然后在 MCP 客户端配置中使用：

```json
{
  "mcpServers": {
    "steamdt": {
      "command": "python",
      "args": ["-m", "steamdt_mcp.server"],
      "env": {
        "STEAMDT_API_KEY": "你的密钥"
      }
    }
  }
}
```

#### 方式二：使用 Git Clone（开发模式）

如果你想修改代码或参与开发：

```bash
# 克隆仓库
git clone https://github.com/Kir4kami/mcp-steamdt.git
cd mcp-steamdt

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 方式三：使用 uv（开发模式，更快）

```bash
# 克隆仓库
git clone https://github.com/Kir4kami/mcp-steamdt.git
cd mcp-steamdt

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt
```

### 配置

#### 方式一（直接安装）的配置

对于方式一（`pip install git+...`），**只需要在 MCP 客户端配置中设置环境变量**（如上方的快速开始示例），无需创建 `.env` 文件。

#### 方式二/三（开发模式）的配置

对于开发模式，你可以选择以下两种方式之一：

**方式 A：使用环境变量（推荐）**
- 在 MCP 客户端配置中设置环境变量（与方式一相同）

**方式 B：使用 .env 文件（可选）**
- 在项目根目录新建一个 `.env` 文件：

```bash
STEAMDT_API_KEY=你的密钥
STEAMDT_BASE_URL=https://open.steamdt.com  # 可选，默认值已配置
```

> **注意**：如果同时在 MCP 客户端配置和 `.env` 文件中设置了环境变量，MCP 客户端配置中的值会优先使用。

### 自动缓存机制

`get_item_base_info` 工具**已内置自动缓存功能**，用户无需手动处理：

- **首次调用**：会自动请求 SteamDT API，并将结果保存到本地 `steam_items_base.json`
- **后续调用**：优先使用本地缓存，无需再次请求 API
- **智能降级**：如果今天已调用过 API（返回 4005 错误），会自动返回缓存（如果有）

这意味着：
- ✅ 用户无需手动运行脚本或管理缓存文件
- ✅ 不用担心每天限 1 次的限制
- ✅ 首次调用后，后续查询都是秒级响应

> **可选**：如果你需要手动刷新缓存，可以运行 `python scripts/cache_base_info.py`，或调用 `get_item_base_info` 时设置 `force_refresh=True`（但需等待第二天才能再次调用 API）。 


> `STEAMDT_BASE_URL` 可选，如果不设置将使用代码里的默认值。

### 运行 MCP 服务器

```bash
python -m steamdt_mcp.server
```

这会以标准 MCP 协议的方式启动一个命令行服务器，支持被 MCP 客户端（例如支持 MCP 的 IDE、聊天工具或代理）调用。

### 在 MCP 客户端中配置

#### Claude Desktop (推荐)

1. 找到 Claude Desktop 的配置文件位置：
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. 编辑配置文件，添加以下内容：

```json
{
  "mcpServers": {
    "steamdt": {
      "command": "python",
      "args": ["-m", "steamdt_mcp.server"],
      "env": {
        "STEAMDT_API_KEY": "你的实际密钥",
        "STEAMDT_BASE_URL": "https://open.steamdt.com"
      }
    }
  }
}
```

> **注意**：如果使用虚拟环境，需要将 `command` 改为虚拟环境中 Python 的完整路径，例如：
> - Windows: `"command": "F:\\mymcp\\mcp-steamdt\\.venv\\Scripts\\python.exe"`
> - macOS/Linux: `"command": "/path/to/mcp-steamdt/.venv/bin/python"`

3. 重启 Claude Desktop，MCP 服务器会自动启动。

#### Cursor IDE

在 Cursor 的设置中，找到 MCP 配置，添加：

```json
{
  "mcpServers": {
    "steamdt": {
      "command": "python",
      "args": ["-m", "steamdt_mcp.server"],
      "env": {
        "STEAMDT_API_KEY": "你的实际密钥",
        "STEAMDT_BASE_URL": "https://open.steamdt.com"
      }
    }
  }
}
```

#### 其他 MCP 客户端

对于其他支持 MCP 的客户端，配置格式类似：

```json
{
  "name": "steamdt",
  "command": "python",
  "args": ["-m", "steamdt_mcp.server"],
  "env": {
    "STEAMDT_API_KEY": "你的实际密钥",
    "STEAMDT_BASE_URL": "https://open.steamdt.com"
  }
}
```

### 使用示例

配置完成后，你就可以在聊天中让模型执行类似指令：

#### 基础查询

- "查询 `AWP | Pit Viper (Minimal Wear)` 的当前价格"
- "批量查询这几个饰品的价格：`AK-47 | Redline (Field-Tested)`, `M4A4 | Howl (Factory New)`"
- "获取所有饰品的基础信息，帮我找一个叫 'Dragon Lore' 的饰品"

#### 磨损度查询

- "通过这个检视链接查询磨损度：`steam://rungame/730/...`"
- "使用 ASMD 参数查询磨损度：`{...}`"

#### 价格历史查询

- "查询 `AK-47 | The Empress (Factory New)` 最近 30 天的价格历史"
- "对比这几个饰品的价格，看看哪个性价比更高"

模型会自动调用 MCP 中的工具，与 SteamDT 通信获取数据。