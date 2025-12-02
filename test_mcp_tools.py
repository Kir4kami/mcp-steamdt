"""直接测试 MCP 工具函数"""
import asyncio
import json
from steamdt_mcp.server import get_item_base_info, get_item_price
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
        return result
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_item_price():
    """测试价格查询"""
    print("\n" + "=" * 60)
    print("测试 2: get_item_price（查询价格）")
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
        return result
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """运行所有测试"""
    print("开始测试 SteamDT MCP 工具...\n")
    
    # 测试基础信息（应该用缓存）
    base_result = await test_get_item_base_info()
    
    # 测试价格查询
    price_result = await test_get_item_price()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    if base_result and base_result.get('success'):
        print("[OK] get_item_base_info 工作正常")
    else:
        print("[ERROR] get_item_base_info 有问题")
    
    if price_result and price_result.get('success'):
        print("[OK] get_item_price 工作正常")
    else:
        print("[ERROR] get_item_price 有问题")


if __name__ == "__main__":
    asyncio.run(main())

