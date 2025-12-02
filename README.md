## SteamDT MCP (Python)

一个基于 Python 的 SteamDT 行情 / 数据分析 MCP 服务端，用于让支持 MCP 的大模型（如 Claude 等）可以直接调用 SteamDT 的开放接口，查询饰品行情并做基础分析。

> ⚠️ 注意：
> - 本项目未内置你的 API 密钥，也不会帮你绕过任何平台限制。请在遵守 SteamDT 官方服务条款的前提下使用。
> - 本项目**只提供数据获取与基础统计功能，不做任何主观推荐或投资建议**；如何解读和使用这些数据，应由上层应用或用户自行决定。

### 功能概览

#### 基础信息与价格查询
- `get_item_base_info`：获取所有饰品的基础信息（名称、marketHashName 等）。**自动管理本地缓存**，首次调用会请求 API 并保存，后续优先使用缓存，无需担心每天限 1 次的限制。
- `get_item_price`：根据 `market_hash_name` 查询单个饰品的当前价格信息（每分钟60次）。
- `get_item_prices_batch`：批量查询多个饰品的价格信息（每分钟1次）。

#### 磨损度查询
- `get_item_wear_by_inspect_url`：通过检视链接查询饰品的磨损度相关数据（每小时36000次）。
- `get_item_wear_by_asmd`：通过 ASMD 参数查询饰品的磨损度相关数据（每小时36000次）。

#### 数据分析（实验性）
- `get_item_price_history`：查询最近若干天的价格历史数据（接口待完善）。
- `analyze_item_trend`：基于历史价格做一个简单的趋势分析（涨跌、波动等），返回总结文本，方便 AI 继续加工。

> 所有接口均基于 SteamDT 官方文档实现：`https://doc.steamdt.com/`。权限限制请参考官方文档。

### 安装

```bash
git clone <your-repo-url>
cd mcp-steamDT

pip install -r requirements.txt
```

建议使用虚拟环境（如 `venv` 或 `conda`）。

### 配置

1. 在 SteamDT 官网注册并在「个人中心 - API 管理」获取你的 `API_KEY`。
2. 在项目根目录新建一个 `.env` 文件：

```bash
STEAMDT_API_KEY=你的密钥
STEAMDT_BASE_URL=https://open.steamdt.com  # 按官方文档调整（当前示例接口使用 open.steamdt.com）
```

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

以下是一个**示例**配置（具体格式视你的 MCP 客户端而定，下面是偏向 JSON 风格的示例）：

```json
{
  "name": "steamdt",
  "command": "python",
  "args": ["-m", "steamdt_mcp.server"],
  "env": {
    "STEAMDT_API_KEY": "你的实际密钥",
    "STEAMDT_BASE_URL": "https://api.steamdt.com"
  }
}
```

配置完成后，你就可以在聊天中让模型执行类似指令：

- “查询 AWP | Dragon Lore（略）最近 30 天的价格走势并给出一个趋势分析。”
- “看看这几个饰品最近哪一个性价比更高，按你自己的标准给个排序。”

模型会自动调用 MCP 中的工具，与 SteamDT 通信获取数据。

### 开发计划

- [x] Python 版 MCP 基础骨架
- [x] 基础信息与价格查询工具
- [x] 批量价格查询
- [x] 磨损度查询（检视链接 + ASMD 参数）
- [x] 检视图生成（检视链接 + ASMD 参数）
- [ ] 价格历史查询接口完善（等待官方文档）
- [ ] 增加更丰富的分析维度（波动率、极值、回撤等）

欢迎 issue / PR 一起完善～ 


