"""初始化 RAG 测试数据 - 同时写入 MySQL 和 Milvus"""
import asyncio
from sqlmodel import Session
from app.database.engine import engine
from app.database.models import KnowledgeTable, KnowledgeFileTable
from app.services.rag.handler import RagHandler


async def init_rag_test_data():
    """初始化 RAG 测试数据"""
    print("=" * 60)
    print("开始初始化 RAG 测试数据")
    print("=" * 60)
    
    # 1. 在 MySQL 中创建知识库
    print("\n1. 在 MySQL 中创建知识库...")
    with Session(engine) as session:
        # 检查是否已存在
        from sqlmodel import select
        statement = select(KnowledgeTable).where(KnowledgeTable.name == "测试知识库")
        existing = session.exec(statement).first()
        
        if existing:
            print(f"   ✓ 知识库已存在: {existing.id}")
            knowledge_id = existing.id
        else:
            # 创建新知识库
            knowledge = KnowledgeTable(
                name="测试知识库",
                description="用于测试 RAG 功能的示例知识库"
            )
            session.add(knowledge)
            session.commit()
            session.refresh(knowledge)
            knowledge_id = knowledge.id
            print(f"   ✓ 创建知识库成功: {knowledge_id}")
        
        # 2. 在 MySQL 中创建文件记录
        print("\n2. 在 MySQL 中创建文件记录...")
        statement = select(KnowledgeFileTable).where(
            KnowledgeFileTable.file_name == "rag_test_intro.txt"
        ).where(KnowledgeFileTable.knowledge_id == knowledge_id)
        existing_file = session.exec(statement).first()
        
        if existing_file:
            print(f"   ✓ 文件记录已存在: {existing_file.id}")
            file_id = existing_file.id
        else:
            file_record = KnowledgeFileTable(
                file_name="rag_test_intro.txt",
                knowledge_id=knowledge_id,
                file_size=1024,
                status="indexed",
                user_id="test_user"  # 添加测试用户ID
            )
            session.add(file_record)
            session.commit()
            session.refresh(file_record)
            file_id = file_record.id
            print(f"   ✓ 创建文件记录成功: {file_id}")
    
    # 3. 在 Milvus 中索引文档内容
    print("\n3. 在 Milvus 中索引文档内容...")
    test_content = """Hubu Agent 是一个基于 FastAPI 和 LangChain 的智能对话系统。
该项目使用了 Milvus 作为向量数据库来存储文档切片。
Redis 用于缓存聊天历史记录，提高响应速度。
RAG (Retrieval-Augmented Generation) 技术结合了检索和生成模型。
MySQL 数据库中存储了知识库的元数据和文件信息。
系统支持多种文档格式，包括 PDF、Word、TXT 等。
用户可以通过前端界面上传文档到知识库。
Agent 可以自动从知识库中检索相关信息来回答问题。"""
    
    try:
        chunk_ids = await RagHandler.index_documents(
            knowledge_id=knowledge_id,
            file_id=file_id,
            file_name="rag_test_intro.txt",
            content=test_content
        )
        
        if chunk_ids:
            print(f"   ✓ 成功索引 {len(chunk_ids)} 个文档切片到 Milvus")
            for i, chunk_id in enumerate(chunk_ids, 1):
                print(f"      - 切片 {i}: {chunk_id}")
        else:
            print("   ✗ 索引失败")
            
    except Exception as e:
        print(f"   ✗ 索引出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 验证检索
    print("\n4. 验证 RAG 检索功能...")
    try:
        result = await RagHandler.query(
            query="这个项目用了什么技术？",
            knowledge_ids=[knowledge_id],
            top_k=3,
            min_score=0.1  # 降低阈值以便看到结果
        )
        print(f"   ✓ 检索结果:\n{result}\n")
    except Exception as e:
        print(f"   ✗ 检索出错: {e}")
    
    print("=" * 60)
    print("✓ RAG 测试数据初始化完成")
    print("=" * 60)
    print(f"\n现在你可以在前端看到:")
    print(f"  - 知识库名称: 测试知识库")
    print(f"  - 知识库 ID: {knowledge_id}")
    print(f"  - 文件名称: rag_test_intro.txt")
    print(f"\n可以在聊天页面选择该知识库进行测试！")


if __name__ == "__main__":
    asyncio.run(init_rag_test_data())
