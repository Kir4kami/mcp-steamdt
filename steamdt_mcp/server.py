import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context


load_dotenv()


@dataclass
class SteamDTConfig:
    api_key: str
    base_url: str = "https://open.steamdt.com"

    @classmethod
    def from_env(cls) -> "SteamDTConfig":
        api_key = os.getenv("STEAMDT_API_KEY")
        if not api_key:
            raise RuntimeError("STEAMDT_API_KEY 环境变量未设置，请在 .env 或环境中配置你的 SteamDT API 密钥。")
        base_url = os.getenv("STEAMDT_BASE_URL", cls.base_url)
        return cls(api_key=api_key, base_url=base_url.rstrip("/"))


def get_client(config: SteamDTConfig) -> httpx.AsyncClient:
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Accept": "application/json",
    }
    return httpx.AsyncClient(base_url=config.base_url, headers=headers, timeout=15)


mcp = FastMCP("steamdt")

# 基础信息缓存文件路径（保存在 MCP 服务器运行目录）
BASE_INFO_CACHE_PATH = Path("steam_items_base.json")


async def _fetch_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """简单封装 HTTP 请求，返回 JSON，出错时抛异常。"""
    resp = await client.request(method, url, params=params)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # 尽量把服务端返回的信息带出去，方便在对话里调试
        detail = getattr(exc.response, "text", "") or ""
        raise RuntimeError(f"SteamDT API 请求失败: {exc} | body={detail[:300]}") from exc
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("SteamDT API 返回了非 JSON 对象，请检查接口路径与参数是否正确。")
    return data


def _load_base_info_cache() -> Optional[Dict[str, Any]]:
    """尝试从本地缓存文件加载基础信息，如果文件不存在或无效则返回 None。"""
    if not BASE_INFO_CACHE_PATH.exists():
        return None
    try:
        content = BASE_INFO_CACHE_PATH.read_text(encoding="utf-8")
        data = json.loads(content)
        # 检查缓存是否有效（有 success=True 且有 data）
        if isinstance(data, dict) and data.get("success") and isinstance(data.get("data"), list) and len(data.get("data", [])) > 0:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _save_base_info_cache(data: Dict[str, Any]) -> None:
    """将基础信息保存到本地缓存文件。"""
    BASE_INFO_CACHE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@mcp.tool()
async def get_item_base_info(
    ctx: Context,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    获取 Steam 饰品基础信息（自动管理本地缓存，用户无需手动处理）。

    文档地址: https://doc.steamdt.com/278832832e0

    说明:
      - 对应接口: GET /open/cs2/v1/base
      - 官方说明: 该接口**每天只能调用一次**，本工具会自动缓存到本地，后续调用优先使用缓存。
      - 接口无请求参数，直接返回一个包含所有基础信息的数组。

    参数:
      - force_refresh: 是否强制刷新（忽略缓存，重新调用 API）。默认 False，优先使用缓存。

    返回:
      - 与官方文档一致的 JSON 对象:
        - success: 是否成功
        - data: BaseInfoVO 数组，每项包含 name、marketHashName、platformList 等
        - errorCode / errorMsg / errorData / errorCodeStr 等错误信息字段
      - 如果使用缓存，会在返回对象中添加 _cached: true 标记

    缓存机制:
      - 首次调用时会调用 API 并自动保存到本地 steam_items_base.json
      - 后续调用优先使用缓存，无需再次请求 API
      - 如果今天已经调用过 API（返回 4005 错误），会自动返回缓存（如果有）
      - 如需更新数据，可设置 force_refresh=True（但需等待第二天才能再次调用 API）
    """
    # 先尝试从缓存加载（除非强制刷新）
    if not force_refresh:
        cached = _load_base_info_cache()
        if cached is not None:
            await ctx.log(f"get_item_base_info 使用了本地缓存（{BASE_INFO_CACHE_PATH.resolve()}）")
            # 添加缓存标记，方便上层应用识别
            result = cached.copy()
            result["_cached"] = True
            return result

    # 缓存不存在或强制刷新，调用 API
    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        try:
            data = await _fetch_json(
                client,
                "GET",
                "/open/cs2/v1/base",
            )
            # API 调用成功，保存缓存
            if data.get("success") and isinstance(data.get("data"), list):
                _save_base_info_cache(data)
                await ctx.log(
                    f"get_item_base_info 调用了 SteamDT API 并已保存缓存到 {BASE_INFO_CACHE_PATH.resolve()}"
                )
            return data
        except RuntimeError as exc:
            # 如果返回 4005（今天已调用），尝试返回缓存
            error_str = str(exc)
            if "4005" in error_str or "已达到上限" in error_str:
                cached = _load_base_info_cache()
                if cached is not None:
                    await ctx.log(
                        f"API 今日调用已达上限，已返回本地缓存（{BASE_INFO_CACHE_PATH.resolve()}）"
                    )
                    result = cached.copy()
                    result["_cached"] = True
                    result["_api_limit_reached"] = True
                    result["_api_error"] = error_str
                    return result
            # 其他错误或没有缓存，直接抛出
            raise


@mcp.tool()
async def get_item_price(
    ctx: Context,
    market_hash_name: str,
) -> Dict[str, Any]:
    """
    通过 marketHashName 查询饰品在各平台的价格信息。

    文档地址: https://doc.steamdt.com/278832830e0

    对应接口:
      - GET /open/cs2/v1/price/single
      - Query 参数:
        - marketHashName (string, required): 饰品名称 / 市场 hash 名

    返回:
      - 与官方文档一致的 JSON 对象:
        - success: 是否成功
        - data: PlatformPriceVO 数组，包含平台、在售价格/数量、求购价格/数量、更新时间等
        - errorCode / errorMsg / errorData / errorCodeStr 等错误信息字段
    """
    if not market_hash_name:
        raise ValueError("market_hash_name 不能为空。")

    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        data = await _fetch_json(
            client,
            "GET",
            "/open/cs2/v1/price/single",
            params={"marketHashName": market_hash_name},
        )
    await ctx.log(
        f"get_item_price 调用了 SteamDT /open/cs2/v1/price/single, marketHashName={market_hash_name}"
    )
    return data


@mcp.tool()
async def get_item_price_history(
    ctx: Context,
    market_hash_name: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    查询指定饰品最近若干天的价格历史。

    参数:
      - market_hash_name: Steam 市场的 market_hash_name
      - days: 回溯的天数，例如 7、30、90 等

    返回:
      - 包含时间序列的历史价格 JSON 数据（具体结构视官方接口而定）
    """
    if days <= 0:
        raise ValueError("days 必须为正整数。")

    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        data = await _fetch_json(
            client,
            "GET",
            "/v1/item/price_history",  # TODO: 按实际文档修改
            params={"marketHashName": market_hash_name, "days": days},
        )
    await ctx.log(
        f"get_item_price_history 调用了 SteamDT，market_hash_name={market_hash_name}, days={days}"
    )
    return data


@mcp.tool()
async def analyze_item_trend(
    ctx: Context,
    market_hash_name: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    基于指定天数的历史价格，对饰品做一个简单趋势分析（仅为客观描述，不构成任何推荐或投资建议）。

    该工具会调用 get_item_price_history，然后在本地做一些轻量级计算，如：
      - 起始价 / 结束价
      - 涨跌幅（百分比）
      - 简单的波动（最大、最小、均值）

    返回:
      - summary: 一段偏中性的中文总结，主要描述价格走势和波动情况
      - stats: 一些基础统计数据，用于需要更细节分析的场景
      - raw: 原始历史数据（可选，视返回体大小与隐私需求决定是否截断）
    """
    if days <= 1:
        raise ValueError("为了有意义的趋势分析，days 建议至少大于 1。")

    # 先拿到历史数据（这里直接复用上面的工具逻辑）
    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        history = await _fetch_json(
            client,
            "GET",
            "/v1/item/price_history",  # TODO: 按实际文档修改
            params={"marketHashName": market_hash_name, "days": days},
        )

    # 下面假设 history 中有一个价格时间序列字段，例如:
    # {"data": [{"time": "...", "price": 123.45}, ...]}
    # 实际字段名请根据文档调整。
    series: List[Dict[str, Any]] = []
    if isinstance(history, dict):
        raw_series = history.get("data") or history.get("prices") or []
        if isinstance(raw_series, list):
            for item in raw_series:
                if not isinstance(item, dict):
                    continue
                price = item.get("price")
                if isinstance(price, (int, float)):
                    series.append(item)

    if len(series) < 2:
        return {
            "summary": f"在最近 {days} 天内可用的价格点太少，无法进行有效趋势分析。",
            "stats": {},
            "raw": history,
        }

    prices = [float(p["price"]) for p in series]
    first = prices[0]
    last = prices[-1]
    minimum = min(prices)
    maximum = max(prices)
    avg = sum(prices) / len(prices)
    change_abs = last - first
    change_pct = (change_abs / first) * 100 if first != 0 else 0.0

    trend: str
    if change_pct > 5:
        trend = "整体呈上升趋势"
    elif change_pct < -5:
        trend = "整体呈下降趋势"
    else:
        trend = "整体相对平稳，涨跌幅不大"

    volatility = maximum - minimum

    summary = (
        f"对饰品 {market_hash_name} 最近 {days} 天的价格走势客观描述如下：\n"
        f"- 起始价格约为 {first:.2f}\n"
        f"- 最新价格约为 {last:.2f}\n"
        f"- 总体涨跌幅约为 {change_pct:.2f}%（{trend}）\n"
        f"- 期间最高价约为 {maximum:.2f}，最低价约为 {minimum:.2f}，"
        f"区间波动约为 {volatility:.2f}\n"
        f"- 平均价格约为 {avg:.2f}\n\n"
        "以上内容仅为基于历史价格的客观统计与描述，不构成任何投资、交易或饰品推荐。"
    )

    await ctx.log(
        f"analyze_item_trend 对 {market_hash_name} 做了简单趋势分析，days={days}, points={len(series)}"
    )

    return {
        "summary": summary,
        "stats": {
            "first": first,
            "last": last,
            "change_abs": change_abs,
            "change_pct": change_pct,
            "min": minimum,
            "max": maximum,
            "avg": avg,
            "volatility_abs": volatility,
            "points": len(series),
        },
        "raw": history,
    }


if __name__ == "__main__":
    # 入口：以 CLI 形式启动 MCP 服务器
    mcp.run()


