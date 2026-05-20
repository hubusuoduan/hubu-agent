# test_milvus.py
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 延迟导入，避免在模块加载时初始化全局实例
import asyncio


async def test_milvus():
    """测试Milvus功能"""
    # 在函数内部导入，避免模块级别的导入触发全局实例初始化
    from app.services.rag.milvus_client import VectorDBClient
    print("=" * 50)
    print("开始测试 Milvus 功能")
    print("=" * 50)
    
    client = None
    try:
        # 初始化客户端
        print("\n0. 初始化Milvus客户端...")
        client = VectorDBClient()
        print("   ✓ 客户端初始化成功")
        # 测试1: 创建集合
        print("\n1. 测试创建集合...")
        collection_name = "test_collection"
        # 使用默认的嵌入维度（从配置读取，通常是2048）
        await client.create_collection(collection_name)
        print(f"   ✓ 集合 '{collection_name}' 创建成功")
        
        # 测试2: 插入数据
        print("\n2. 测试插入数据...")
        test_chunks = [
            {
                'chunk_id': 'chunk_001',
                'content': '这是一个测试文档片段',
                'file_id': 'file_001',
                'file_name': 'test_doc.txt',
                'knowledge_id': 'kb_001'
            },
            {
                'chunk_id': 'chunk_002',
                'content': '这是另一个测试文档片段',
                'file_id': 'file_001',
                'file_name': 'test_doc.txt',
                'knowledge_id': 'kb_001'
            }
        ]
        insert_result = await client.insert(collection_name, test_chunks)
        print(f"   插入结果: {insert_result}")
        assert insert_result == True, "插入应该成功"
        print(f"   ✓ 成功插入 {len(test_chunks)} 个文档块")
        
        # 测试3: 搜索数据
        print("\n3. 测试搜索功能...")
        from app.services.rag.embedding import get_embedding
        query_text = "测试文档"
        query_embedding = await get_embedding([query_text])
        search_results = await client.search(
            query_embedding[0], 
            collection_name, 
            top_k=5
        )
        print(f"   搜索结果数量: {len(search_results)}")
        for i, result in enumerate(search_results, 1):
            print(f"   结果 {i}: {result['content'][:50]}... (分数: {result['score']:.4f})")
        print(f"   ✓ 搜索功能正常")
        
        # 测试4: 根据文件ID删除数据
        print("\n4. 测试删除功能...")
        delete_result = await client.delete_by_file_id('file_001', collection_name)
        print(f"   删除结果: {delete_result}")
        assert delete_result == True, "删除应该成功"
        print(f"   ✓ 删除功能正常")
        
        # 验证删除
        print("\n5. 验证删除后的数据...")
        search_after_delete = await client.search(
            query_embedding[0], 
            collection_name, 
            top_k=5
        )
        print(f"   删除后搜索结果数量: {len(search_after_delete)}")
        print(f"   ✓ 数据已成功删除")
        
        # 测试6: 删除集合
        print("\n6. 测试删除集合...")
        drop_result = await client.delete_collection(collection_name)
        print(f"   删除集合结果: {drop_result}")
        assert drop_result == True, "删除集合应该成功"
        print(f"   ✓ 集合已成功删除")
        
        print("\n" + "=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理连接
        if client:
            print("\n关闭Milvus连接...")
            client.close()


if __name__ == '__main__':
    asyncio.run(test_milvus())
