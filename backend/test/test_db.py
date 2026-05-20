"""数据库连接测试脚本"""
import asyncio
from sqlmodel import text
from app.database.engine import async_engine


async def test_connection():
    """测试数据库连接"""
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功:", result.scalar())
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")


async def cleanup():
    """清理资源"""
    await async_engine.dispose()


if __name__ == "__main__":
    print("开始测试数据库连接...")
    asyncio.run(test_connection())
    asyncio.run(cleanup())
    print("测试完成")
