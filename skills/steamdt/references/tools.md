# 官方 MCP 工具参考

核对日期：2026-10-20。以下参数来自该日服务实际返回的 `tools/list`；服务升级后，以当前 schema 为准。

- [官方 MCP 接入](https://doc.steamdt.com/9475656m0)
- [七日均价 API 说明](https://doc.steamdt.com/319748133e0)
- [饰品 K 线 API 说明](https://doc.steamdt.com/428124801e0)
- [开放平台文档](https://doc.steamdt.com/)

## 参数

| 工具 | 必填 | 可选 |
| --- | --- | --- |
| `search_items` | `content`：非空搜索文本 | 无 |
| `get_item_prices` | `marketHashName`：完整英文市场名称 | 无 |
| `get_item_average_price_7d` | `marketHashName` | 无，不支持 `days` |
| `get_item_kline` | `marketHashName`、`granularity` | `platform`、`specialStyle`、`recentPoints` |
| `get_broad_index` | 无，传 `{}` | 无 |
| `get_broad_kline` | `granularity` | 无 |

`granularity` 为 `hour`、`day` 或 `week`。饰品 K 线的 `platform` 为 `ALL`（默认）、`BUFF`、`YOUPIN`、`C5`、`STEAM` 或 `HALOSKINS`。

`recentPoints` 取值 1–100，默认 20，仅用于饰品 K 线；不能传给大盘 K 线。它控制返回点数，不能假定某个点数一定等于同样多的自然日。

`specialStyle` 仅在用户指定且当前 schema 支持时传入。含义需要在[官方文档](https://doc.steamdt.com/)的特殊款式对照表核对，不通过缩写猜测等级或款式。

## 名称搜索

`search_items` 最多返回 20 个候选，不代表返回了全部匹配项。候选过多时根据用户的皮肤、磨损等条件缩小查询，不把未出现在前 20 条里的饰品认定为不存在。

## 价格单位与报价条件

本项目用户已确认 SteamDT 饰品价格口径为人民币元（CNY），适用于实时价格、七日均价及 K 线价格；不因响应缺少币种字段而省略单位。若响应明确给出其他币种，按实际标注；大盘指数不属于货币价格。

实时价格实测返回 `platforms`，每项包括 `platform`、`sellPrice`、`sellCount`、`biddingPrice`、`biddingCount`、`updateTime` 等字段。

- `sellPrice` 展示为在售底价，`biddingPrice` 展示为最高求购价（可能附条件）。
- 最高求购可能限制 float 等具体单件属性；即使同属一个磨损档位，也不代表底价货品满足最高求购条件。
- 实测响应未包含具体求购条件，不能只比较这两个数值就判异常、算套利收益或推断可立即成交。需要核对条件时到平台查看。
- 缺失、零值及无报价按主 Skill 的缺失数据规则处理，不把它们当作有效免费报价。

## 七日均价

请求示例：

```json
{"marketHashName": "AK-47 | Case Hardened (Field-Tested)"}
```

返回业务对象包含：

- `marketHashName`：实际标的。
- `avgPrice`：服务提供的总体近七日均价；文档未在该页面解释加权算法，不声称它是平台均价的简单算术平均。
- `dataList`：每项含 `platform` 和 `avgPrice`。

2026-10-20 实测响应未包含币种和数据更新时间；币种按上述用户确认口径使用人民币元，更新时间不能自行补造。不要将这次响应里的价格保存为未来查询的默认结果。

## K 线与大盘

饰品 K 线的 API 页面说明不包含成交数据。不要由其推导真实成交笔数或成交量。

官方 MCP 文档说明大盘 K 线摘要覆盖全部数据，而点位只返回最近 20 个。解读摘要时保留其覆盖口径，不能将全部历史的摘要涨跌解释为最近 20 点的涨跌。

本参考未固定未经实测核对的 K 线、大盘和实时价格响应字段。调用后读取实际响应及工具说明；对含义不明确的字段再查官方文档，不从旧本地 MCP 的返回结构推断。

## 能力边界

这六个工具不提供单件磨损、检视图或下单能力，也没有批量价格工具。多标的查询需要逐个调用时控制数量并复用结果；不自动切换到旧服务或直接 API。

仓库保留的旧服务含磨损及批量价格封装，但需要单独配置和验证。仅在用户明确需要该能力且已可用时考虑它，不把旧服务当作默认依赖。
