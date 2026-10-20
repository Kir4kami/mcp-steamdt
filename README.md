# SteamDT：CS2 饰品行情 Skill

通过 **SteamDT 官方 MCP + SteamDT Skill**，用中文查询饰品价格、比较平台行情、查看七日均价和 K 线，以及了解 CS2 大盘。

本仓库保留原有 Python MCP 实现；新版主要入口为 [`skills/steamdt/SKILL.md`](skills/steamdt/SKILL.md)。使用新版不需要安装 Python 依赖或维护饰品基础信息缓存。

## 快速开始

### 1. 接入官方 MCP

按[官方接入文档](https://doc.steamdt.com/9475656m0)申请 API Key，在客户端添加远程 MCP：

- 服务名称：`steamdt`
- 地址：`https://mcp.steamdt.com/mcp`
- 传输方式：Streamable HTTP
- 鉴权：`Authorization: Bearer <APIKEY>`

API Key 只保存在本机用户级客户端配置或凭证存储中，不要放进本仓库、Skill 或聊天内容。

Codex 支持在用户级 `~/.codex/config.toml` 配置；以下示例从客户端进程环境读取密钥：

```toml
[mcp_servers.steamdt]
url = "https://mcp.steamdt.com/mcp"
bearer_token_env_var = "STEAMDT_API_KEY"
```

在本机设置 `STEAMDT_API_KEY`，确保启动客户端的进程能够读取它，再重启或重载客户端。项目根目录的 `.env` 不会自动为远程 MCP 配置提供环境变量。也可使用客户端支持的鉴权请求头设置。详见 [Codex MCP 文档](https://developers.openai.com/codex/mcp)。

连接后检查工具。2026-10-20 实测官方提供 **6 个**：

`search_items`、`get_item_prices`、`get_item_average_price_7d`、`get_item_kline`、`get_broad_index`、`get_broad_kline`。

清单可能随服务升级变化；确认所需工具可用即可，不要求数量固定。

### 2. 安装 Skill

将仓库中的整个 `skills/steamdt` 文件夹复制到 Codex 的用户 Skill 目录：

- Windows：`%USERPROFILE%\.codex\skills\steamdt`
- macOS / Linux：`~/.codex/skills/steamdt`
- 若自定义了 `CODEX_HOME`：使用其下的 `skills/steamdt`

如果目标目录已经存在，先比较内容再更新。重启或重载客户端后，在新对话中用 `$steamdt` 调用，也可让客户端自动匹配相关请求。Skill 文件中的依赖声明用于说明所需服务，不会替你填写凭证或保证自动完成 MCP 配置。

### 3. 开始查询

```text
使用 $steamdt，查一下 USP 印花集现在多少钱。
```

名称存在多个磨损、暗金或纪念品版本时，Skill 会根据上下文筛选，仍有歧义再请你选择。

```text
使用 $steamdt，查询 AK-47 | Case Hardened (Field-Tested) 的近七日均价。
使用 $steamdt，对比同一饰品在 BUFF 和悠悠有品的当前在售与求购报价。
使用 $steamdt，看看这件饰品最近三十天的日 K 走势，以及今天大盘的变化。
```

## 数据口径

- 在售底价、最高求购价（可能附条件）与七日均价分别展示；报价不等于成交价。
- 最高求购可能限制具体磨损值（float）等条件，与在售底价不一定对应同规格货品；求购价高于在售价不直接判为异常或套利机会，具体条件需到平台核对。
- 七日均价工具不支持任意天数历史序列。走势使用 K 线，并核对实际时间覆盖。
- 本项目由用户确认饰品价格统一使用人民币元（CNY），即使响应未标币种也按此展示；若响应明确指定其他币种则以实际为准。大盘指数不标货币单位，缺少数据更新时间时明确说明。
- 不把平台价差直接解释为可获得的套利利润，也不把总体均价擅自重算成平台均价的平均数。
- 凭证错误或达到配额时停止相关请求；官方 MCP 与直接 API 共用 API Key 配额。

## 验证与维护

更新 Skill 后可使用 Codex 自带 skill-creator 的 `scripts/quick_validate.py` 检查其结构。行为验收覆盖：

| 场景 | 预期行为 |
| --- | --- |
| 中文名匹配多个版本 | 搜索并筛选；无法唯一确认时询问，不自动选第一项 |
| 完整英文名查七日均价 | 直接调用均价工具，不额外搜索或获取 K 线 |
| 返回价格未标明币种 | 按本项目确认口径展示人民币元；不将大盘指数标成元 |
| 在售 594 元、最高求购 716 元 | 说明可能有磨损等订单条件差异，需到平台核对；不标异常、不推断套利或保证可卖出 |
| 请求三十天涨跌，但 K 线覆盖不足 | 说明实际覆盖，不将七日均价当作三十天序列 |
| 凭证拒绝或配额耗尽 | 停止请求，不切换接口继续尝试 |
| 工具未加载 | 说明连接或重载步骤，不声称已查询 |

官方接入和均价查询已于 2026-10-20 在本机独立 MCP 连接中验证；这不代表 Skill 已安装，或实时价格、K 线和大盘工具已全部完成实测。参数与来源见 [工具参考](skills/steamdt/references/tools.md)。

## 原有 Python MCP

`steamdt_mcp/`、`scripts/cache_base_info.py`、依赖文件和 Python 安装入口均保留。本轮未修改旧服务行为；它可以作为后续磨损查询、批量处理等能力的代码基础。

旧服务的安装与使用方式见 [旧版 MCP 文档](docs/legacy-mcp.md)。其中 `get_item_price_history` 对均价接口的历史描述与当前官方文档不一致，不应作为任意天数历史数据来源；使用前需单独适配与验证。

## 官方资料

- [开放平台文档](https://doc.steamdt.com/)
- [官方 MCP 接入与工具说明](https://doc.steamdt.com/9475656m0)
- [接口权限列表](https://doc.steamdt.com/6369437m0)
