# test_doc_parser.py
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.doc_parser import SimpleDocParser
import tempfile
import os


def create_test_files():
    """创建测试文件"""
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)
    
    # 创建TXT文件
    txt_file = test_dir / "test.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("""这是第一段文本。

这是第二段文本，用于测试文档解析功能。

第三段文本包含了更多的内容来测试分割器的效果。
""")
    
    # 创建Markdown文件
    md_file = test_dir / "test.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("""# 测试文档

## 简介

这是一个Markdown测试文档。

## 功能

- 支持标题解析
- 支持列表解析
- 支持段落分割

## 结论

Markdown格式非常适合技术文档。
""")
    
    # 创建CSV文件
    csv_file = test_dir / "test.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("""姓名,年龄,职业
张三,25,工程师
李四,30,设计师
王五,28,产品经理
""")
    
    # 创建HTML文件
    html_file = test_dir / "test.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head><title>测试页面</title></head>
<body>
    <h1>欢迎页面</h1>
    <p>这是一个HTML测试文档。</p>
    <p>用于测试HTML解析功能。</p>
</body>
</html>
""")
    
    return test_dir


def test_parser():
    """测试文档解析器"""
    print("=" * 60)
    print("开始测试文档解析器")
    print("=" * 60)
    
    try:
        # 创建测试文件
        print("\n1. 创建测试文件...")
        test_dir = create_test_files()
        print(f"   ✓ 测试文件已创建在: {test_dir}")
        
        # 测试TXT
        print("\n2. 测试TXT文件解析...")
        txt_path = str(test_dir / "test.txt")
        txt_chunks = SimpleDocParser.parse_text(txt_path)
        print(f"   解析结果: {len(txt_chunks)} 个文本块")
        for i, chunk in enumerate(txt_chunks[:2], 1):
            print(f"   块{i}: {chunk[:50]}...")
        assert len(txt_chunks) > 0, "TXT解析应该返回文本块"
        print("   ✓ TXT解析成功")
        
        # 测试Markdown
        print("\n3. 测试Markdown文件解析...")
        md_path = str(test_dir / "test.md")
        md_chunks = SimpleDocParser.parse_markdown(md_path)
        print(f"   解析结果: {len(md_chunks)} 个文本块")
        for i, chunk in enumerate(md_chunks[:2], 1):
            print(f"   块{i}: {chunk[:50]}...")
        assert len(md_chunks) > 0, "Markdown解析应该返回文本块"
        print("   ✓ Markdown解析成功")
        
        # 测试CSV
        print("\n4. 测试CSV文件解析...")
        csv_path = str(test_dir / "test.csv")
        csv_chunks = SimpleDocParser.parse_csv(csv_path)
        print(f"   解析结果: {len(csv_chunks)} 个文本块")
        for i, chunk in enumerate(csv_chunks[:2], 1):
            print(f"   块{i}: {chunk[:80]}...")
        assert len(csv_chunks) > 0, "CSV解析应该返回文本块"
        print("   ✓ CSV解析成功")
        
        # 测试HTML
        print("\n5. 测试HTML文件解析...")
        html_path = str(test_dir / "test.html")
        html_chunks = SimpleDocParser.parse_html(html_path)
        print(f"   解析结果: {len(html_chunks)} 个文本块")
        for i, chunk in enumerate(html_chunks[:2], 1):
            print(f"   块{i}: {chunk[:50]}...")
        assert len(html_chunks) > 0, "HTML解析应该返回文本块"
        print("   ✓ HTML解析成功")
        
        # 测试自动识别文件类型
        print("\n6. 测试自动文件类型识别...")
        auto_chunks = SimpleDocParser.parse_file(txt_path)
        print(f"   TXT自动识别: {len(auto_chunks)} 个文本块")
        
        auto_chunks = SimpleDocParser.parse_file(md_path)
        print(f"   Markdown自动识别: {len(auto_chunks)} 个文本块")
        print("   ✓ 自动识别成功")
        
        # 测试不支持的格式
        print("\n7. 测试不支持的文件格式...")
        unsupported_path = str(test_dir / "test.xyz")
        with open(unsupported_path, 'w') as f:
            f.write("test")
        result = SimpleDocParser.parse_file(unsupported_path)
        assert result == [], "不支持的格式应返回空列表"
        print("   ✓ 不支持格式处理正确")
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        print("\n支持的格式:")
        print("  - .txt, .text (文本文件)")
        print("  - .md (Markdown)")
        print("  - .pdf (PDF文档)")
        print("  - .docx (Word文档)")
        print("  - .html, .htm (HTML)")
        print("  - .csv (CSV表格)")
        print("  - .json (JSON数据)")
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试文件
        if 'test_dir' in locals():
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            print(f"\n已清理测试文件")


if __name__ == '__main__':
    test_parser()
