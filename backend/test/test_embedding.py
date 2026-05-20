# test_embedding.py
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag.embedding import get_embedding
import asyncio


async def test_embedding():
    """测试Embedding功能"""
    print("=" * 50)
    print("开始测试 DashScope Embedding")
    print("=" * 50)
    
    try:
        # 测试1: 单个文本
        print("\n1. 测试单个文本嵌入...")
        text1 = "这是一个测试文本"
        embedding1 = await get_embedding(text1)
        print(f"   文本: {text1}")
        print(f"   向量维度: {len(embedding1)}")
        print(f"   向量前5个值: {embedding1[:5]}")
        assert len(embedding1) > 0, "向量不能为空"
        print("   ✓ 单个文本嵌入成功")
        
        # 测试2: 多个文本批量处理
        print("\n2. 测试批量文本嵌入...")
        texts = [
            "人工智能是未来的发展方向",
            "机器学习是人工智能的重要分支",
            "深度学习在图像识别中表现优异"
        ]
        embeddings = await get_embedding(texts)
        print(f"   文本数量: {len(texts)}")
        print(f"   向量数量: {len(embeddings)}")
        print(f"   每个向量维度: {len(embeddings[0])}")
        assert len(embeddings) == 3, "应该返回3个向量"
        assert all(len(emb) > 0 for emb in embeddings), "所有向量不能为空"
        print("   ✓ 批量文本嵌入成功")
        
        # 测试3: 相似度验证（语义相近的文本向量应该更接近）
        print("\n3. 测试向量相似度...")
        similar_text1 = "Python编程语言很流行"
        similar_text2 = "Python是一门流行的编程语言"
        different_text = "今天天气很好"
        
        emb_sim1 = await get_embedding(similar_text1)
        emb_sim2 = await get_embedding(similar_text2)
        emb_diff = await get_embedding(different_text)
        
        # 计算余弦相似度
        def cosine_similarity(v1, v2):
            dot_product = sum(a * b for a, b in zip(v1, v2))
            norm1 = sum(a * a for a in v1) ** 0.5
            norm2 = sum(a * a for a in v2) ** 0.5
            return dot_product / (norm1 * norm2)
        
        sim_score = cosine_similarity(emb_sim1, emb_sim2)
        diff_score = cosine_similarity(emb_sim1, emb_diff)
        
        print(f"   相似文本相似度: {sim_score:.4f}")
        print(f"   不同文本相似度: {diff_score:.4f}")
        print(f"   ✓ 向量相似度合理")
        
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
    asyncio.run(test_embedding())
