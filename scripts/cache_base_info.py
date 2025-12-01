import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.getenv("STEAMDT_BASE_URL", "https://open.steamdt.com").rstrip("/")
API_KEY = os.getenv("STEAMDT_API_KEY")
OUT_PATH = Path("steam_items_base.json")


def main() -> None:
    if not API_KEY:
        raise RuntimeError("STEAMDT_API_KEY 未设置，请在环境变量或 .env 中配置后再运行本脚本。")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }

    url = f"{BASE_URL}/open/cs2/v1/base"
    print(f"请求 {url} 获取基础信息...")

    with httpx.Client(headers=headers, timeout=30.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()

    success = data.get("success")
    items = data.get("data") or []

    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"已写入 {OUT_PATH.resolve()}，success={success}，条数={len(items)}\n"
        "注意：根据官方文档，该接口每天只能调用一次，请优先复用本地缓存文件。"
    )


if __name__ == "__main__":
    main()


