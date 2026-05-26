"""skill_loader detail模式 & 动态注册表 测试"""
import asyncio
from app.tools.skill_loader.action import (
    load_skill, read_skill_resource,
    _load_skill, _scan_skills, _build_skill_list_text,
    SKILL_REGISTRY, SKILLS_DIR,
)


def test_scan_skills():
    """测试动态扫描 skills 目录"""
    registry = _scan_skills()
    # 应该只有实际存在 SKILL.md 的目录
    assert "docx" in registry
    assert "pdf" in registry
    assert "pptx" in registry
    assert "xlsx" in registry
    assert "skill-creator" in registry
    # 不存在的 skill 不应在注册表中
    assert "algorithmic-art" not in registry
    assert "brand-guidelines" not in registry
    # description 不应为空（这些 skill 都有 description）
    assert registry["docx"] != ""
    assert registry["pdf"] != ""
    print("✅ _scan_skills 动态扫描 测试通过")


def test_registry_is_from_scan():
    """测试 SKILL_REGISTRY 确实来自动态扫描"""
    assert SKILL_REGISTRY == _scan_skills()
    print("✅ SKILL_REGISTRY 来自动态扫描 测试通过")


def test_build_skill_list_text():
    """测试构建 Skill 列表文本"""
    text = _build_skill_list_text()
    assert "docx:" in text
    assert "pdf:" in text
    assert "pptx:" in text
    assert "xlsx:" in text
    print("✅ _build_skill_list_text 测试通过")


async def test_load_skill_lightweight():
    """测试轻量模式：只返回 name + description"""
    result = await _load_skill("docx")
    assert "🔧 Skill: docx" in result
    assert "📝 描述:" in result
    assert "detail=true" in result
    # 轻量模式不应包含 SKILL.md 正文内容
    assert "A .docx file is a ZIP archive" not in result
    print("✅ 轻量模式 测试通过")


async def test_load_skill_detail():
    """测试详细模式：返回完整指令"""
    result = await _load_skill("docx", detail=True)
    assert "🔧 Skill: docx" in result
    assert "📝 描述:" in result
    # 详细模式应包含 SKILL.md 正文内容
    assert "A .docx file is a ZIP archive" in result
    print("✅ 详细模式 测试通过")


async def test_load_nonexistent_skill():
    """测试加载不存在的 Skill（动态注册表校验）"""
    result = await _load_skill("nonexistent-xyz")
    assert "不存在" in result
    assert "可用 Skill:" in result
    # 应列出实际存在的 skill
    assert "docx:" in result
    print("✅ 加载不存在Skill 测试通过")


async def test_tool_invoke_lightweight():
    """测试工具调用 - 轻量模式"""
    result = await load_skill.ainvoke({"skill_name": "docx"})
    assert "🔧 Skill: docx" in result
    assert "detail=true" in result
    assert "A .docx file is a ZIP archive" not in result
    print("✅ load_skill 轻量模式工具调用 测试通过")


async def test_tool_invoke_detail():
    """测试工具调用 - 详细模式"""
    result = await load_skill.ainvoke({"skill_name": "docx", "detail": True})
    assert "🔧 Skill: docx" in result
    assert "A .docx file is a ZIP archive" in result
    print("✅ load_skill 详细模式工具调用 测试通过")


async def test_read_resource_nonexistent_skill():
    """测试读取不存在 Skill 的资源"""
    result = await read_skill_resource.ainvoke({
        "skill_name": "nonexistent-xyz",
        "resource_path": "some_file.md"
    })
    assert "不存在" in result
    print("✅ 读取不存在Skill资源 测试通过")


async def main():
    test_scan_skills()
    test_registry_is_from_scan()
    test_build_skill_list_text()
    await test_load_skill_lightweight()
    await test_load_skill_detail()
    await test_load_nonexistent_skill()
    await test_tool_invoke_lightweight()
    await test_tool_invoke_detail()
    await test_read_resource_nonexistent_skill()
    print("\n🎉 所有 detail 模式测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
