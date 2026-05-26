"""skill_loader 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
from pathlib import Path
from unittest.mock import patch
from app.tools.skill_loader.action import (
    load_skill, read_skill_resource,
    _load_skill, _read_resource, _parse_frontmatter,
    _list_resources, _get_skill_dir,
    SKILL_REGISTRY, SKILLS_DIR,
)


# ─── 辅助函数测试 ───

def test_parse_frontmatter():
    """测试 YAML frontmatter 解析"""
    content = """---
name: docx
description: Word文档处理
---
# Docx Skill
这是正文内容。
"""
    meta, body = _parse_frontmatter(content)
    assert meta["name"] == "docx"
    assert meta["description"] == "Word文档处理"
    assert "正文内容" in body
    print("✅ _parse_frontmatter 正常解析 测试通过")


def test_parse_frontmatter_no_meta():
    """测试无 frontmatter 的内容"""
    content = "# Just a normal markdown"
    meta, body = _parse_frontmatter(content)
    assert meta == {}
    assert body == content
    print("✅ _parse_frontmatter 无元数据 测试通过")


def test_skill_registry():
    """测试 Skill 注册表"""
    assert len(SKILL_REGISTRY) > 0
    assert "docx" in SKILL_REGISTRY
    assert "pdf" in SKILL_REGISTRY
    assert "pptx" in SKILL_REGISTRY
    assert "xlsx" in SKILL_REGISTRY
    print("✅ SKILL_REGISTRY 测试通过")


def test_get_skill_dir():
    """测试 Skill 目录路径"""
    skill_dir = _get_skill_dir("docx")
    assert skill_dir == SKILLS_DIR / "docx"
    print("✅ _get_skill_dir 测试通过")


def test_list_resources():
    """测试列出资源文件"""
    # 对存在的 skill 目录测试
    for skill_name in ["docx", "pdf", "pptx", "xlsx"]:
        resources = _list_resources(skill_name)
        # 只要不报错就行，资源文件列表可能为空
        assert isinstance(resources, list)
    print("✅ _list_resources 测试通过")


# ─── 加载 Skill 测试 ───

async def test_load_existing_skill():
    """测试加载已存在的 Skill"""
    for skill_name in ["docx", "pdf", "pptx", "xlsx"]:
        result = await _load_skill(skill_name)
        # 成功加载应包含 Skill 名称或描述
        assert skill_name in result or "Skill" in result
    print("✅ 加载已存在Skill 测试通过")


async def test_load_nonexistent_skill():
    """测试加载不存在的 Skill"""
    result = await _load_skill("nonexistent-skill-xyz")
    assert "不存在" in result
    assert "可用 Skill" in result
    print("✅ 加载不存在Skill 测试通过")


# ─── 读取资源文件测试 ───

async def test_read_resource_illegal_path():
    """测试非法路径读取"""
    result = await _read_resource("docx", "../../etc/passwd")
    assert "非法路径" in result
    print("✅ 非法路径读取 测试通过")


async def test_read_resource_nonexistent():
    """测试读取不存在的资源文件"""
    result = await _read_resource("docx", "nonexistent_file.md")
    assert "不存在" in result
    print("✅ 读取不存在资源 测试通过")


# ─── 工具接口测试 ───

async def test_tool_interface():
    """测试工具接口"""
    assert load_skill.name == "load_skill"
    assert "加载" in load_skill.description or "Skill" in load_skill.description

    assert read_skill_resource.name == "read_skill_resource"
    assert "资源" in read_skill_resource.description or "读取" in read_skill_resource.description
    print("✅ 工具接口 测试通过")


async def test_tool_invoke_load_skill():
    """测试工具调用 - load_skill"""
    result = await load_skill.ainvoke({"skill_name": "docx"})
    assert "docx" in result or "Skill" in result
    print("✅ load_skill 工具调用 测试通过")


async def test_tool_invoke_read_resource():
    """测试工具调用 - read_skill_resource"""
    result = await read_skill_resource.ainvoke({
        "skill_name": "docx",
        "resource_path": "nonexistent.md"
    })
    assert "不存在" in result
    print("✅ read_skill_resource 工具调用 测试通过")


async def main():
    test_parse_frontmatter()
    test_parse_frontmatter_no_meta()
    test_skill_registry()
    test_get_skill_dir()
    test_list_resources()
    await test_load_existing_skill()
    await test_load_nonexistent_skill()
    await test_read_resource_illegal_path()
    await test_read_resource_nonexistent()
    await test_tool_interface()
    await test_tool_invoke_load_skill()
    await test_tool_invoke_read_resource()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
