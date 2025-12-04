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
    json_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """简单封装 HTTP 请求，返回 JSON，出错时抛异常。"""
    resp = await client.request(method, url, params=params, json=json_data)
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


def _normalize_text(text: str) -> str:
    """标准化文本：转小写、移除标点符号和空格。"""
    import re
    # 移除标点符号和空格，只保留字母、数字和中文字符
    normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', text.lower())
    return normalized


def _extract_keywords(query: str) -> List[str]:
    """从查询字符串中提取关键词（支持中英文混合）。"""
    import re
    # 移除标点符号和多余空格
    cleaned = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', query)
    # 按空格分割，过滤空字符串
    keywords = [kw.strip().lower() for kw in cleaned.split() if kw.strip()]
    # 如果没有空格分割的关键词，尝试按字符类型分割（中英文混合）
    if not keywords or (len(keywords) == 1 and not ' ' in query):
        # 使用更智能的分割：按字符类型边界分割（中文字符和英文字符/数字的边界）
        # 这个正则会匹配：连续的中文字符 或 连续的英文字母/数字
        parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', query.lower())
        if parts:
            keywords = [p for p in parts if p]
    return keywords if keywords else [query.lower()]


def _weapon_alias_match(query: str, item_name: str) -> bool:
    """检查武器别名是否匹配（如 'usp' 匹配 'USP消音版' 或 'USP-S'）。"""
    query_lower = query.lower()
    item_lower = item_name.lower()
    
    # 武器别名映射表
    aliases = {
        'usp': ['usp', 'usp-s', 'usp消音版', 'usps', 'usp消音'],
        'ak': ['ak', 'ak47', 'ak-47'],
        'm4': ['m4', 'm4a4', 'm4a1', 'm4a1-s', 'm4a1s'],
        'awp': ['awp'],
        'glock': ['glock', 'glock-18'],
        'p250': ['p250'],
        'tec9': ['tec-9', 'tec9'],
        'mp7': ['mp7', 'mp-7'],
    }
    
    # 检查查询词是否是某个武器的别名
    for weapon, alias_list in aliases.items():
        if query_lower in alias_list:
            # 检查物品名是否包含该武器的任何别名
            for alias in alias_list:
                if alias in item_lower:
                    return True
    
    return False


def _smart_match(query: str, item_name: str, market_hash_name: str) -> bool:
    """
    智能匹配：支持分词匹配、忽略标点符号、武器别名。
    
    匹配策略（按优先级）：
    1. 完全包含匹配（原有逻辑）
    2. 分词匹配：查询的所有关键词都在物品名中出现
    3. 武器别名匹配
    4. 标准化后的包含匹配（忽略标点符号）
    """
    query_lower = query.lower()
    name_lower = item_name.lower()
    market_lower = market_hash_name.lower()
    
    # 策略1: 完全包含匹配（原有逻辑，优先级最高）
    if query_lower in name_lower or query_lower in market_lower:
        return True
    
    # 策略2: 分词匹配
    keywords = _extract_keywords(query)
    if len(keywords) > 1:  # 只有多个关键词时才使用分词匹配
        # 标准化文本以便匹配
        normalized_name = _normalize_text(item_name)
        normalized_market = _normalize_text(market_hash_name)
        
        # 检查所有关键词是否都在物品名中出现
        all_keywords_match = True
        for keyword in keywords:
            normalized_keyword = _normalize_text(keyword)
            if (normalized_keyword not in normalized_name and 
                normalized_keyword not in normalized_market):
                all_keywords_match = False
                break
        
        if all_keywords_match:
            return True
    
    # 策略3: 武器别名匹配 + 其他关键词匹配
    keywords = _extract_keywords(query)
    if len(keywords) > 1:
        # 检查是否有武器别名匹配，同时其他关键词也在物品名中
        weapon_matched = False
        other_keywords_matched = True
        
        for kw in keywords:
            # 检查是否是武器别名
            if _weapon_alias_match(kw, item_name) or _weapon_alias_match(kw, market_hash_name):
                weapon_matched = True
            else:
                # 检查其他关键词是否在物品名中
                normalized_kw = _normalize_text(kw)
                normalized_name = _normalize_text(item_name)
                normalized_market = _normalize_text(market_hash_name)
                if normalized_kw not in normalized_name and normalized_kw not in normalized_market:
                    other_keywords_matched = False
                    break
        
        if weapon_matched and other_keywords_matched:
            return True
    
    # 策略4: 标准化后的包含匹配（忽略标点符号）
    normalized_query = _normalize_text(query)
    normalized_name = _normalize_text(item_name)
    normalized_market = _normalize_text(market_hash_name)
    
    if normalized_query in normalized_name or normalized_query in normalized_market:
        return True
    
    return False


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
            await ctx.log("info", f"get_item_base_info 使用了本地缓存（{BASE_INFO_CACHE_PATH.resolve()}）")
            # 添加缓存标记，方便上层应用识别
            result = cached.copy()
            result["_cached"] = True
            return result

    # 缓存不存在或强制刷新，调用 API
    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        try:
            resp = await client.request("GET", "/open/cs2/v1/base")
            # 先尝试解析 JSON，即使状态码不是 2xx
            try:
                data = resp.json()
            except Exception:
                data = {}
            
            # 检查是否是 4005 错误（API 限制）
            if resp.status_code != 200 or data.get("errorCode") == 4005:
                cached = _load_base_info_cache()
                if cached is not None:
                    await ctx.log("info", f"API 今日调用已达上限，已返回本地缓存（{BASE_INFO_CACHE_PATH.resolve()}）")
                    result = cached.copy()
                    result["_cached"] = True
                    result["_api_limit_reached"] = True
                    if resp.status_code != 200:
                        result["_api_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    else:
                        result["_api_error"] = data.get("errorMsg", "API limit reached")
                    return result
                # 没有缓存，返回 API 错误
                resp.raise_for_status()
            
            # API 调用成功，保存缓存
            if data.get("success") and isinstance(data.get("data"), list):
                _save_base_info_cache(data)
                await ctx.log("info", f"get_item_base_info 调用了 SteamDT API 并已保存缓存到 {BASE_INFO_CACHE_PATH.resolve()}")
            return data
        except httpx.HTTPStatusError as exc:
            # HTTP 错误，尝试返回缓存
            cached = _load_base_info_cache()
            if cached is not None:
                await ctx.log("info", f"API 请求失败，已返回本地缓存（{BASE_INFO_CACHE_PATH.resolve()}）")
                result = cached.copy()
                result["_cached"] = True
                result["_api_error"] = str(exc)
                return result
            raise RuntimeError(f"SteamDT API 请求失败: {exc}") from exc


@mcp.tool()
async def search_item_by_name(
    ctx: Context,
    query: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    根据中文名或英文名搜索饰品，返回匹配的 market_hash_name。
    
    这个工具可以帮助用户找到正确的 market_hash_name，特别是当用户只知道中文名时。
    
    参数:
      - query: 搜索关键词（可以是中文名、英文名或部分名称）
      - limit: 返回结果的最大数量，默认 10
    
    返回:
      - success: 是否成功
      - data: 匹配的饰品列表，每项包含 name 和 marketHashName
      - count: 匹配数量
    """
    if not query:
        raise ValueError("query 不能为空。")
    
    # 从缓存加载基础信息
    cached = _load_base_info_cache()
    if cached is None:
        return {
            "success": False,
            "errorCode": "NO_CACHE",
            "errorMsg": "本地缓存不存在，请先调用 get_item_base_info 获取基础信息。",
            "data": [],
            "count": 0,
        }
    
    items = cached.get("data") or []
    if not isinstance(items, list):
        return {
            "success": False,
            "errorCode": "INVALID_CACHE",
            "errorMsg": "缓存数据格式无效。",
            "data": [],
            "count": 0,
        }
    
    # 搜索匹配的饰品（使用智能匹配）
    matches = []
    
    for item in items:
        if not isinstance(item, dict):
            continue
        
        name = item.get("name", "")
        market_hash_name = item.get("marketHashName", "")
        
        # 使用智能匹配算法
        if _smart_match(query, name, market_hash_name):
            matches.append({
                "name": name,
                "marketHashName": market_hash_name,
            })
            
            if len(matches) >= limit:
                break
    
    await ctx.log("info", f"search_item_by_name 搜索了 '{query}'，找到 {len(matches)} 个匹配项")
    
    return {
        "success": True,
        "data": matches,
        "count": len(matches),
        "query": query,
    }


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
    await ctx.log("info", f"get_item_price 调用了 SteamDT /open/cs2/v1/price/single, marketHashName={market_hash_name}")
    return data


@mcp.tool()
async def get_item_price_history(
    ctx: Context,
    market_hash_name: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    查询指定饰品最近若干天的价格历史（均价数据）。

    文档地址: https://doc.steamdt.com/319748133e0

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
        # 根据官方文档 https://doc.steamdt.com/319748133e0，接口路径是 /open/cs2/v1/price/avg
        data = await _fetch_json(
            client,
            "GET",
            "/open/cs2/v1/price/avg",
            params={"marketHashName": market_hash_name, "days": days},
        )
    await ctx.log("info", f"get_item_price_history 调用了 SteamDT /open/cs2/v1/price/avg, market_hash_name={market_hash_name}, days={days}")
    return data


@mcp.tool()
async def get_item_prices_batch(
    ctx: Context,
    market_hash_names: List[str],
) -> Dict[str, Any]:
    """
    批量查询多个饰品的价格信息。

    文档地址: https://doc.steamdt.com/278832831e0

    对应接口:
      - POST /open/cs2/v1/price/batch
      - Body 参数:
        - marketHashNames (array of string, required): 饰品名称数组

    权限限制: 每分钟1次

    返回:
      - 与官方文档一致的 JSON 对象:
        - success: 是否成功
        - data: 数组，每项包含 marketHashName 和 dataList（平台价格列表）
        - errorCode / errorMsg / errorData / errorCodeStr 等错误信息字段
    """
    if not market_hash_names:
        raise ValueError("market_hash_names 不能为空，至少需要一个饰品名称。")
    if not isinstance(market_hash_names, list):
        raise ValueError("market_hash_names 必须是一个字符串数组。")

    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        data = await _fetch_json(
            client,
            "POST",
            "/open/cs2/v1/price/batch",
            json_data={"marketHashNames": market_hash_names},
        )
    await ctx.log("info", f"get_item_prices_batch 调用了 SteamDT /open/cs2/v1/price/batch, count={len(market_hash_names)}")
    return data


@mcp.tool()
async def get_item_wear_by_inspect_url(
    ctx: Context,
    inspect_url: str,
) -> Dict[str, Any]:
    """
    通过检视链接查询饰品的磨损度相关数据。

    文档地址: https://doc.steamdt.com/273806087e0

    对应接口:
      - POST /open/cs2/v1/wear
      - Body 参数:
        - inspectUrl (string, required): Steam 检视链接

    权限限制: 每小时36000次

    返回:
      - 与官方文档一致的 JSON 对象:
        - success: 是否成功
        - data: 包含 needWaiting、taskId、blockDTO（磨损度数据）等
        - errorCode / errorMsg / errorData / errorCodeStr 等错误信息字段
    """
    if not inspect_url:
        raise ValueError("inspect_url 不能为空。")

    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        data = await _fetch_json(
            client,
            "POST",
            "/open/cs2/v1/wear",
            json_data={"inspectUrl": inspect_url},
        )
    await ctx.log("info", f"get_item_wear_by_inspect_url 调用了 SteamDT /open/cs2/v1/wear, inspectUrl={inspect_url[:50]}...")
    return data


@mcp.tool()
async def get_item_wear_by_asmd(
    ctx: Context,
    asmd_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    通过 ASMD 参数查询饰品的磨损度相关数据。

    文档地址: https://doc.steamdt.com/273806088e0

    对应接口:
      - POST /open/cs2/v2/wear
      - Body 参数: ASMD 相关参数字典（具体字段请参考官方文档）

    权限限制: 每小时36000次

    返回:
      - 与官方文档一致的 JSON 对象:
        - success: 是否成功
        - data: 包含 needWaiting、taskId、blockDTO（磨损度数据）等
        - errorCode / errorMsg / errorData / errorCodeStr 等错误信息字段
    """
    if not asmd_params or not isinstance(asmd_params, dict):
        raise ValueError("asmd_params 必须是一个非空字典。")

    config = SteamDTConfig.from_env()
    async with get_client(config) as client:
        data = await _fetch_json(
            client,
            "POST",
            "/open/cs2/v2/wear",
            json_data=asmd_params,
        )
    await ctx.log("info", f"get_item_wear_by_asmd 调用了 SteamDT /open/cs2/v2/wear")
    return data


def main():
    """MCP 服务器入口函数，用于命令行和 PyPI 安装后的直接调用。"""
    import asyncio
    import sys
    
    # 确保环境变量已设置（用于调试）
    if not os.getenv("STEAMDT_API_KEY"):
        print("警告: STEAMDT_API_KEY 环境变量未设置", file=sys.stderr)
        sys.stderr.flush()
    
    # 启动 stdio 模式的 MCP 服务器
    # FastMCP 会自动处理工具注册和 MCP 协议通信
    try:
        asyncio.run(mcp.run_stdio_async())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


if __name__ == "__main__":
    # 入口：以 CLI 形式启动 MCP 服务器
    main()


