"""测试所有 SteamDT MCP 工具"""
import asyncio
import json
from steamdt_mcp.server import (
    get_item_base_info,
    get_item_price,
    get_item_prices_batch,
    get_item_wear_by_inspect_url,
    get_item_wear_by_asmd,
)
from mcp.server.fastmcp import Context


class MockContext:
    """模拟 MCP Context，用于测试"""
    async def log(self, message: str):
        print(f"[LOG] {message}")


async def test_get_item_base_info():
    """测试基础信息获取（应该使用缓存）"""
    print("=" * 60)
    print("测试 1: get_item_base_info（应该使用缓存）")
    print("=" * 60)
    
    ctx = MockContext()
    try:
        result = await get_item_base_info(ctx)
        print(f"[OK] 调用成功")
        print(f"   success: {result.get('success')}")
        print(f"   数据条数: {len(result.get('data', []))}")
        print(f"   是否使用缓存: {result.get('_cached', False)}")
        if result.get('data'):
            first_item = result['data'][0]
            print(f"   第一条饰品: {first_item.get('name')}")
            print(f"   marketHashName: {first_item.get('marketHashName')}")
        return True, result
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_get_item_price():
    """测试单个价格查询"""
    print("\n" + "=" * 60)
    print("测试 2: get_item_price（查询单个价格）")
    print("=" * 60)
    
    # 从缓存里找一个 marketHashName
    try:
        with open("steam_items_base.json", encoding="utf-8") as f:
            base_data = json.load(f)
        items = base_data.get("data", [])
        if items:
            test_hash_name = items[0].get("marketHashName")
            print(f"使用测试 marketHashName: {test_hash_name}")
        else:
            test_hash_name = "AWP | Pit Viper (Minimal Wear)"
            print(f"缓存为空，使用默认: {test_hash_name}")
    except Exception as e:
        test_hash_name = "AWP | Pit Viper (Minimal Wear)"
        print(f"读取缓存失败，使用默认: {test_hash_name}")
    
    ctx = MockContext()
    try:
        result = await get_item_price(ctx, test_hash_name)
        print(f"[OK] 调用成功")
        print(f"   success: {result.get('success')}")
        print(f"   平台数量: {len(result.get('data', []))}")
        if result.get('data'):
            first_platform = result['data'][0]
            print(f"   第一个平台: {first_platform.get('platform')}")
            print(f"   在售价格: {first_platform.get('sellPrice')}")
            print(f"   在售数量: {first_platform.get('sellCount')}")
        return True, result, test_hash_name
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


async def test_get_item_prices_batch():
    """测试批量价格查询"""
    print("\n" + "=" * 60)
    print("测试 3: get_item_prices_batch（批量查询价格）")
    print("=" * 60)
    
    # 从缓存里找几个 marketHashName
    try:
        with open("steam_items_base.json", encoding="utf-8") as f:
            base_data = json.load(f)
        items = base_data.get("data", [])
        if items and len(items) >= 3:
            test_hash_names = [items[i].get("marketHashName") for i in range(3)]
            print(f"使用测试 marketHashNames: {test_hash_names}")
        else:
            test_hash_names = [
                "AWP | Pit Viper (Minimal Wear)",
                "AK-47 | Redline (Field-Tested)",
                "M4A4 | Howl (Factory New)"
            ]
            print(f"缓存不足，使用默认: {test_hash_names}")
    except Exception as e:
        test_hash_names = [
            "AWP | Pit Viper (Minimal Wear)",
            "AK-47 | Redline (Field-Tested)"
        ]
        print(f"读取缓存失败，使用默认: {test_hash_names}")
    
    ctx = MockContext()
    try:
        result = await get_item_prices_batch(ctx, test_hash_names)
        print(f"[OK] 调用成功")
        print(f"   success: {result.get('success')}")
        print(f"   返回饰品数量: {len(result.get('data', []))}")
        if result.get('data'):
            for item in result['data'][:2]:  # 只显示前2个
                print(f"   - {item.get('marketHashName')}: {len(item.get('dataList', []))} 个平台")
        return True, result
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_get_item_wear_by_inspect_url():
    """测试通过检视链接查询磨损度"""
    print("\n" + "=" * 60)
    print("测试 4: get_item_wear_by_inspect_url（通过检视链接查询磨损度）")
    print("=" * 60)
    
    # 使用一个示例检视链接（需要替换为真实的）
    test_inspect_url = "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198000000000A1234567890D1234567890123456789"
    print(f"使用测试 inspectUrl: {test_inspect_url[:50]}...")
    print("注意: 这是一个示例 URL，实际测试需要真实的检视链接")
    
    ctx = MockContext()
    try:
        result = await get_item_wear_by_inspect_url(ctx, test_inspect_url)
        print(f"[OK] 调用成功")
        print(f"   success: {result.get('success')}")
        if result.get('data'):
            data = result['data']
            print(f"   needWaiting: {data.get('needWaiting')}")
            print(f"   taskId: {data.get('taskId')}")
            if data.get('blockDTO'):
                print(f"   已获取 blockDTO 数据")
        return True, result
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        print("   这可能是正常的，因为示例 URL 可能无效")
        import traceback
        traceback.print_exc()
        return False, None


async def test_get_item_wear_by_asmd():
    """测试通过 ASMD 参数查询磨损度"""
    print("\n" + "=" * 60)
    print("测试 5: get_item_wear_by_asmd（通过 ASMD 参数查询磨损度）")
    print("=" * 60)
    
    # ASMD 参数示例（需要根据实际文档调整）
    test_asmd = {
        "a": "76561198000000000",  # accountId
        "s": "1234567890",  # itemId
        "m": "1234567890123456789",  # 其他参数
        "d": "1234567890123456789"  # 其他参数
    }
    print(f"使用测试 ASMD 参数: {test_asmd}")
    print("注意: 这是示例参数，实际测试需要真实的 ASMD 参数")
    
    ctx = MockContext()
    try:
        result = await get_item_wear_by_asmd(ctx, test_asmd)
        print(f"[OK] 调用成功")
        print(f"   success: {result.get('success')}")
        if result.get('data'):
            data = result['data']
            print(f"   needWaiting: {data.get('needWaiting')}")
            print(f"   taskId: {data.get('taskId')}")
        return True, result
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        print("   这可能是正常的，因为示例参数可能无效")
        import traceback
        traceback.print_exc()
        return False, None




async def main():
    """运行所有测试"""
    print("开始测试所有 SteamDT MCP 工具...\n")
    
    results = {}
    
    # 测试基础信息
    success, result = await test_get_item_base_info()
    results["get_item_base_info"] = success
    
    # 测试单个价格查询
    success, result, hash_name = await test_get_item_price()
    results["get_item_price"] = success
    
    # 测试批量价格查询
    success, result = await test_get_item_prices_batch()
    results["get_item_prices_batch"] = success
    
    # 测试磨损度查询（检视链接）
    success, result = await test_get_item_wear_by_inspect_url()
    results["get_item_wear_by_inspect_url"] = success
    
    # 测试磨损度查询（ASMD）
    success, result = await test_get_item_wear_by_asmd()
    results["get_item_wear_by_asmd"] = success
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试完成！汇总结果：")
    print("=" * 60)
    
    for tool_name, success in results.items():
        status = "[OK]" if success else "[ERROR]"
        print(f"{status} {tool_name}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\n总计: {passed}/{total} 个工具测试通过")
    
    print("\n注意:")
    print("- 磨损度相关的接口可能需要真实的参数才能成功")
    print("- 如果某些接口返回错误，可能是因为示例参数无效，这是正常的")
    print("- 价格查询相关的接口应该都能正常工作")


if __name__ == "__main__":
    asyncio.run(main())

