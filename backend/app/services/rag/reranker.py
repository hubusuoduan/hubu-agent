"""文档重排序服务 - 优化版"""
from typing import List
from dataclasses import dataclass
from loguru import logger

from app.config import settings


@dataclass
class RerankedDocument:
    """重排序后的文档"""
    content: str
    score: float
    metadata: dict = None


class HybridReranker:
    """混合重排序器 - 结合BM25和语义匹配"""
    
    @classmethod
    async def rerank_documents(
        cls, 
        query: str, 
        documents: List[str],
        documents_metadata: List[dict] = None
    ) -> List[RerankedDocument]:
        """
        对文档进行混合重排序
        
        Args:
            query: 查询文本
            documents: 文档内容列表
            documents_metadata: 文档元数据列表(可选)
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        # 解析混合权重配置
        from app.services.settings_service import SettingsFactory
        hybrid_weights = SettingsFactory.get(key="RAG_HYBRID_WEIGHTS")
        weights = [float(w) for w in hybrid_weights.split(",")]
        bm25_weight = weights[0]
        semantic_weight = weights[1]
        
        logger.info(f"混合权重配置: BM25={bm25_weight}, 语义={semantic_weight}")
        
        # 方法1: BM25关键词匹配
        bm25_scores = cls._calculate_bm25_scores(query, documents)
        
        # 方法2: 语义相似度 - 基于关键词密度和长度匹配
        semantic_scores = cls._calculate_semantic_similarity(query, documents)
        
        # 混合评分: 使用配置的权重
        reranked_docs = []
        for i, doc in enumerate(documents):
            bm25_score = bm25_scores[i]
            semantic_score = semantic_scores[i]
            final_score = bm25_weight * bm25_score + semantic_weight * semantic_score
            
            metadata = documents_metadata[i] if documents_metadata else {}
            reranked_docs.append(RerankedDocument(
                content=doc,
                score=final_score,
                metadata=metadata
            ))
        
        # 按分数降序排序
        reranked_docs.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"混合重排序完成: {len(documents)} 个文档, "
                   f"最高分: {reranked_docs[0].score:.3f}, "
                   f"最低分: {reranked_docs[-1].score:.3f}")
        
        return reranked_docs
    
    @classmethod
    def _calculate_bm25_scores(cls, query: str, documents: List[str]) -> List[float]:
        """
        计算BM25关键词匹配分数
        
        BM25公式: score(q,d) = Σ IDF(q_i) * (f(q_i,d) * (k1 + 1)) / (f(q_i,d) + k1 * (1 - b + b * |d|/avgdl))
        """
        import math
        
        # 参数设置
        k1 = 1.2  # 词频饱和度参数
        b = 0.75  # 文档长度归一化参数
        
        # 分词(简化版,实际应该用jieba等中文分词)
        query_terms = cls._tokenize(query)
        doc_terms_list = [cls._tokenize(doc) for doc in documents]
        
        # 计算文档平均长度
        doc_lengths = [len(terms) for terms in doc_terms_list]
        avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1
        
        # 计算每个查询词在文档集合中的文档频率(DF)
        N = len(documents)  # 文档总数
        df = {}  # 文档频率
        for term in query_terms:
            df[term] = sum(1 for terms in doc_terms_list if term in terms)
        
        # 计算每个文档的BM25分数
        scores = []
        for doc_terms in doc_terms_list:
            score = 0.0
            doc_len = len(doc_terms)
            
            for term in query_terms:
                # 词频(TF)
                tf = doc_terms.count(term)
                
                # 逆文档频率(IDF)
                idf = math.log((N - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
                
                # BM25核心公式
                term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avgdl))
                score += term_score
            
            scores.append(score)
        
        # 归一化到0-1
        if scores:
            max_score = max(scores)
            if max_score > 0:
                scores = [s / max_score for s in scores]
        
        return scores
    
    @classmethod
    def _calculate_semantic_similarity(cls, query: str, documents: List[str]) -> List[float]:
        """
        计算语义相似度(简化版)
        
        考虑因素:
        1. 查询词覆盖率
        2. 关键词密度
        3. 文档长度匹配度
        """
        query_terms = set(cls._tokenize(query))
        scores = []
        
        # 查询的平均词数(用于长度匹配)
        query_len = len(query_terms)
        
        for doc in documents:
            doc_terms = set(cls._tokenize(doc))
            doc_len = len(doc_terms)
            
            if not doc_terms or not query_terms:
                scores.append(0.0)
                continue
            
            # 1. 词覆盖率 (40%)
            coverage = len(query_terms & doc_terms) / len(query_terms)
            
            # 2. 关键词密度 (30%)
            doc_words = cls._tokenize(doc)
            keyword_count = sum(1 for word in doc_words if word in query_terms)
            density = keyword_count / len(doc_words) if doc_words else 0
            
            # 3. 长度匹配度 (30%)
            # 理想长度是查询长度的2-5倍
            if query_len == 0:
                length_match = 0.0
            else:
                ratio = doc_len / query_len
                if 2 <= ratio <= 5:
                    length_match = 1.0
                elif 1 <= ratio < 2:
                    length_match = 0.6
                elif 5 < ratio <= 10:
                    length_match = 0.5
                else:
                    length_match = 0.2
            
            # 综合分数
            final_score = 0.4 * coverage + 0.3 * density + 0.3 * length_match
            scores.append(final_score)
        
        return scores
    
    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """
        简化版分词
        
        支持:
        - 英文按空格分词
        - 中文按字符分词(简化)
        - 去除标点符号和停用词
        """
        import re
        
        # 移除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        # 转小写
        text = text.lower()
        
        # 分词(简化版)
        # 英文: 按空格分
        # 中文: 按字符分(实际应该用jieba)
        words = []
        for word in text.split():
            if len(word) >= 2:  # 英文单词
                words.append(word)
            else:  # 中文字符
                words.extend(list(word))
        
        # 移除停用词
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', 
            '不', '人', '都', '一', '一个', '这', '这个', '那',
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'to',
            'and', 'or', 'but', 'in', 'with', 'for', 'of'
        }
        words = [w for w in words if w not in stopwords and len(w.strip()) > 0]
        
        return words


# 全局重排序器实例
reranker = HybridReranker()
