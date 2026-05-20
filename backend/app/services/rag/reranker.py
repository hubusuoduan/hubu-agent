"""文档重排序服务"""
from typing import List
from dataclasses import dataclass
from loguru import logger


@dataclass
class RerankedDocument:
    """重排序后的文档"""
    content: str
    score: float


class SimpleReranker:
    """简化版文档重排序器"""
    
    @classmethod
    async def rerank_documents(cls, query: str, documents: List[str]) -> List[RerankedDocument]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            重排序后的文档列表
        """
        # 简化实现：基于关键词匹配度排序
        #TODO 实际项目中应该使用Cross-Encoder模型进行重排序
        
        reranked_docs = []
        query_words = set(query.lower().split())
        
        for doc in documents:
            # 计算关键词匹配度
            doc_words = set(doc.lower().split())
            if not doc_words:
                score = 0.0
            else:
                # 简单计算交集比例
                overlap = len(query_words & doc_words)
                score = overlap / len(query_words) if query_words else 0.0
            
            reranked_docs.append(RerankedDocument(content=doc, score=score))
        
        # 按分数降序排序
        reranked_docs.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"重排序完成，返回 {len(reranked_docs)} 个文档")
        return reranked_docs


# 全局重排序器实例
reranker = SimpleReranker()
