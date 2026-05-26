"""skill_loader 三层工具输出展示 - 查看各场景下的实际输出"""
import asyncio
import sys
import io
from app.tools.skill_loader.action import (
    load_skill, list_skill_resources, read_skill_resource,
    _load_skill, _read_resource, _build_skill_list_text,
    SKILL_REGISTRY,
)

# 解决 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


async def show_all_outputs():
    print("=" * 60)
    print("第1层: load_skill(name) 只返回 name + description")
    print("=" * 60)
    result = await _load_skill("docx")
    print(result)
    print()

    print("=" * 60)
    print("第2层: load_skill(name, detail=True) 返回完整指令")
    print("=" * 60)
    result = await _load_skill("docx", detail=True)
    print(result[:500])
    print("... (省略)")
    print()

    print("=" * 60)
    print("list_skill_resources(name) 按需查看资源文件列表")
    print("=" * 60)
    result = await list_skill_resources.ainvoke({"skill_name": "pdf"})
    print(result)
    print()

    print("=" * 60)
    print("第3层: read_skill_resource(name, path) 读取具体资源")
    print("=" * 60)
    result = await _read_resource("pdf", "reference.md")
    print(result[:400])
    print("... (省略)")
    print()

    print("=" * 60)
    print("不存在的 Skill")
    print("=" * 60)
    result = await _load_skill("nonexistent")
    print(result)
    print()

    print("=" * 60)
    print("非法路径")
    print("=" * 60)
    result = await _read_resource("docx", "../../etc/passwd")
    print(result)
    print()

    print("=" * 60)
    print("不存在的资源文件")
    print("=" * 60)
    result = await _read_resource("docx", "nonexistent.md")
    print(result[:400])
    print()

    print("=" * 60)
    print("工具调用对比: ainvoke 轻量 vs 详细")
    print("=" * 60)
    r1 = await load_skill.ainvoke({"skill_name": "pptx"})
    print(f"[轻量] 长度={len(r1)} 字符")
    print(r1)
    print()
    r2 = await load_skill.ainvoke({"skill_name": "pptx", "detail": True})
    print(f"[详细] 长度={len(r2)} 字符")
    print(r2[:300])
    print("... (省略)")
    print()
    print(f"Token 节省: 轻量模式只占详细模式的 {len(r1)/len(r2)*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(show_all_outputs())
