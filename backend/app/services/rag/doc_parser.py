"""文档解析器"""
from typing import List
from pathlib import Path
from loguru import logger
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


class SimpleDocParser:
    """基于LangChain的文档解析器"""
    
    # 文本分割器配置
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    @classmethod
    def _get_text_splitter(cls) -> RecursiveCharacterTextSplitter:
        """获取文本分割器"""
        return RecursiveCharacterTextSplitter(
            chunk_size=cls.CHUNK_SIZE,
            chunk_overlap=cls.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
    
    @staticmethod
    def parse_text(file_path: str) -> List[str]:
        """
        解析文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            
            text_splitter = SimpleDocParser._get_text_splitter()
            chunks = text_splitter.split_documents(documents)
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            
            logger.info(f"解析文本文件 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析文本文件失败: {e}")
            return []
    
    @staticmethod
    def parse_markdown(file_path: str) -> List[str]:
        """
        解析Markdown文件（使用简单文本加载器）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            # 使用TextLoader读取Markdown文件内容
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            
            text_splitter = SimpleDocParser._get_text_splitter()
            chunks = text_splitter.split_documents(documents)
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            
            logger.info(f"解析Markdown文件 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析Markdown文件失败: {e}")
            return []
    
    @staticmethod
    def parse_pdf(file_path: str) -> List[str]:
        """
        解析PDF文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            text_splitter = SimpleDocParser._get_text_splitter()
            chunks = text_splitter.split_documents(documents)
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            
            logger.info(f"解析PDF文件 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析PDF文件失败: {e}")
            return []
    
    @staticmethod
    def parse_word(file_path: str) -> List[str]:
        """
        解析Word文档 (.docx)
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            
            text_splitter = SimpleDocParser._get_text_splitter()
            chunks = text_splitter.split_documents(documents)
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            
            logger.info(f"解析Word文档 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析Word文档失败: {e}")
            return []
    
    @staticmethod
    def parse_html(file_path: str) -> List[str]:
        """
        解析HTML文件（使用BeautifulSoup提取文本）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 使用BeautifulSoup提取纯文本
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            
            # 创建临时文档对象
            from langchain_core.documents import Document
            doc = Document(page_content=text)
            
            text_splitter = SimpleDocParser._get_text_splitter()
            chunks = text_splitter.split_documents([doc])
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            
            logger.info(f"解析HTML文件 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析HTML文件失败: {e}")
            return []
    
    @staticmethod
    def parse_csv(file_path: str) -> List[str]:
        """
        解析CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            loader = CSVLoader(file_path, encoding='utf-8')
            documents = loader.load()
            
            # CSV每行是一个document，直接拼接
            chunk_texts = [
                doc.page_content.strip() 
                for doc in documents 
                if doc.page_content.strip()
            ]
            
            logger.info(f"解析CSV文件 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析CSV文件失败: {e}")
            return []
    
    @staticmethod
    def parse_json(file_path: str) -> List[str]:
        """
        解析JSON文件（简单实现）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 将JSON转换为字符串
            if isinstance(data, (dict, list)):
                text_content = json.dumps(data, ensure_ascii=False, indent=2)
            else:
                text_content = str(data)
            
            # 创建临时文档对象
            from langchain_core.documents import Document
            doc = Document(page_content=text_content)
            
            text_splitter = SimpleDocParser._get_text_splitter()
            chunks = text_splitter.split_documents([doc])
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            
            logger.info(f"解析JSON文件 {file_path}，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"解析JSON文件失败: {e}")
            return []
    
    @classmethod
    def parse_content(cls, content: str) -> List[str]:
        """
        直接解析文本内容
        
        Args:
            content: 文本内容
            
        Returns:
            文本块列表
        """
        try:
            from langchain_core.documents import Document
            doc = Document(page_content=content)
            
            text_splitter = cls._get_text_splitter()
            chunks = text_splitter.split_documents([doc])
            
            chunk_texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
            logger.info(f"解析文本内容，得到 {len(chunk_texts)} 个文本块")
            return chunk_texts
        except Exception as e:
            logger.error(f"解析文本内容失败: {e}")
            return []

    @classmethod
    def parse_file(cls, file_path: str) -> List[str]:
        """
        根据文件类型解析文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        suffix = Path(file_path).suffix.lower()
        
        # 文本文件
        if suffix in ['.txt', '.text']:
            return cls.parse_text(file_path)
        # Markdown
        elif suffix == '.md':
            return cls.parse_markdown(file_path)
        # PDF
        elif suffix == '.pdf':
            return cls.parse_pdf(file_path)
        # Word文档
        elif suffix in ['.docx', '.doc']:
            if suffix == '.doc':
                logger.warning(".doc格式不支持，请使用.docx格式")
                return []
            return cls.parse_word(file_path)
        # HTML
        elif suffix in ['.html', '.htm']:
            return cls.parse_html(file_path)
        # CSV
        elif suffix == '.csv':
            return cls.parse_csv(file_path)
        # JSON
        elif suffix == '.json':
            return cls.parse_json(file_path)
        else:
            logger.warning(f"不支持的文件类型: {suffix}")
            return []
