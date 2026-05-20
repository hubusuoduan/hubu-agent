# test_redis.py
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.redis_client import RedisClient
import asyncio


async def test_redis():
    """测试Redis功能"""
    print("=" * 50)
    print("开始测试 Redis 功能")
    print("=" * 50)
    
    try:
        # 设置值
        print("\n1. 测试 set() 方法...")
        result = RedisClient.set("test_key", "test_value", expiration=60)
        print(f"   设置结果: {result}")
        
        # 获取值
        print("\n2. 测试 get() 方法...")
        value = RedisClient.get("test_key")
        print(f"   获取的值: {value}")
        assert value == "test_value", f"值不匹配: 期望 'test_value', 实际 '{value}'"
        
        # 检查存在
        print("\n3. 测试 exists() 方法...")
        exists = RedisClient.exists("test_key")
        print(f"   键是否存在: {exists}")
        assert exists == True, "键应该存在"
        
        # 测试不存在的键
        print("\n4. 测试不存在的键...")
        not_exists = RedisClient.exists("nonexistent_key")
        print(f"   不存在的键: {not_exists}")
        assert not_exists == False, "键应该不存在"
        
        # 删除
        print("\n5. 测试 delete() 方法...")
        delete_result = RedisClient.delete("test_key")
        print(f"   删除结果: {delete_result}")
        assert delete_result == True, "应该删除成功"
        
        # 验证删除
        print("\n6. 验证删除后的键...")
        after_delete = RedisClient.exists("test_key")
        print(f"   删除后是否存在: {after_delete}")
        assert after_delete == False, "键应该已被删除"
        
        print("\n" + "=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_redis())
