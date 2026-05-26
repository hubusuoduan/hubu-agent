"""技能管理API"""
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
from loguru import logger

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.tools.skill_loader.action import SKILLS_DIR, SKILL_REGISTRY, _scan_skills, _parse_frontmatter

router = APIRouter(prefix="/skills", tags=["技能管理"])


@router.get("/list", summary="获取技能列表")
async def list_skills(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """获取技能列表（分页 + 关键词搜索）

    Args:
        page: 页码，从1开始
        page_size: 每页数量
        keyword: 搜索关键词（匹配 name 或 description）
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    # 从 SKILL_REGISTRY 获取所有技能
    items = []
    for name, description in SKILL_REGISTRY.items():
        if keyword:
            if keyword.lower() not in name.lower() and keyword.lower() not in description.lower():
                continue
        # 获取目录名（用于删除等操作）
        dir_name = name
        # 尝试匹配实际目录名
        if SKILLS_DIR.exists():
            for d in SKILLS_DIR.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    content = (d / "SKILL.md").read_text(encoding="utf-8")
                    meta, _ = _parse_frontmatter(content)
                    if meta.get("name", d.name) == name:
                        dir_name = d.name
                        break
        items.append({
            "name": name,
            "description": description,
            "dir_name": dir_name,
        })

    total = len(items)
    offset = (page - 1) * page_size
    paged = items[offset:offset + page_size]

    return {
        "total": total,
        "items": paged,
        "page": page,
        "page_size": page_size,
    }


@router.post("/add", summary="添加技能")
async def add_skill(
    name: str,
    description: str = "",
    skill_md_content: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """添加一个新技能（创建目录和 SKILL.md）

    Args:
        name: 技能名称（同时作为目录名，仅允许字母数字和连字符）
        description: 技能描述
        skill_md_content: SKILL.md 的完整内容（可选，不提供则自动生成）
    """
    # 校验名称格式
    if not name or not name.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="技能名称仅允许字母、数字、连字符和下划线")

    # 检查是否已存在
    if name in SKILL_REGISTRY:
        raise HTTPException(status_code=400, detail=f"技能 '{name}' 已存在")

    skill_dir = SKILLS_DIR / name
    if skill_dir.exists():
        raise HTTPException(status_code=400, detail=f"技能目录 '{name}' 已存在")

    # 创建目录
    skill_dir.mkdir(parents=True, exist_ok=True)

    # 生成 SKILL.md
    if skill_md_content:
        md_content = skill_md_content
    else:
        md_content = f"""---
name: {name}
description: "{description}"
---

# {name} Skill

{description}
"""

    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(md_content, encoding="utf-8")

    # 刷新注册表
    SKILL_REGISTRY.update(_scan_skills())

    logger.info(f"技能 '{name}' 创建成功")

    return {
        "name": name,
        "description": description,
        "message": "技能创建成功",
    }


@router.post("/upload", summary="上传技能包")
async def upload_skill(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """上传技能包（ZIP 文件），自动解压到 skills 目录

    优先从 ZIP 中的 SKILL.md frontmatter 提取 name 和 description；
    如果 SKILL.md 不存在或缺少字段，则使用请求参数中的 name/description 作为 fallback。
    """
    # name 和 description 将在解压后从 SKILL.md 提取，此处暂不校验

    # 校验文件类型
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持上传 ZIP 格式的技能包")

    import tempfile
    import zipfile

    # 保存上传的 ZIP 到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # 临时解压目录
    tmp_extract = Path(tempfile.mkdtemp(prefix="skill_upload_"))

    try:
        # 第一步：解压 ZIP 到临时目录
        with zipfile.ZipFile(tmp_path, "r") as zf:
            names = zf.namelist()

            # 如果 ZIP 根目录直接包含文件
            has_root_files = any(not n.startswith("__MACOSX") and "/" not in n.rstrip("/") for n in names if not n.endswith("/"))

            if has_root_files:
                for member in zf.namelist():
                    if member.startswith("__MACOSX") or member.endswith("/"):
                        continue
                    source = zf.open(member)
                    target = tmp_extract / member
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with open(target, "wb") as f:
                        f.write(source.read())
            else:
                # ZIP 内可能有一层子目录，取第一个子目录的内容
                prefix = None
                for n in names:
                    parts = n.split("/")
                    if len(parts) > 1 and parts[0] and not parts[0].startswith("__MACOSX"):
                        prefix = parts[0] + "/"
                        break

                if prefix:
                    for member in zf.namelist():
                        if member.startswith("__MACOSX") or member.endswith("/"):
                            continue
                        if not member.startswith(prefix):
                            continue
                        relative = member[len(prefix):]
                        if not relative:
                            continue
                        source = zf.open(member)
                        target = tmp_extract / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with open(target, "wb") as f:
                            f.write(source.read())

        # 第二步：从 SKILL.md 提取 name 和 description
        skill_md_path = tmp_extract / "SKILL.md"
        extracted_name = None
        extracted_desc = None

        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            meta, _ = _parse_frontmatter(content)
            extracted_name = meta.get("name")
            extracted_desc = meta.get("description")

        # 优先使用 SKILL.md 中的值，fallback 到请求参数
        final_name = extracted_name or name
        final_desc = extracted_desc or description or ""

        # 如果仍然没有 name，尝试用 ZIP 文件名
        if not final_name and file.filename:
            final_name = Path(file.filename).stem

        if not final_name:
            raise HTTPException(status_code=400, detail="无法确定技能名称，ZIP 中缺少 SKILL.md 且未提供 name 参数")

        # 校验名称格式
        if not final_name.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(status_code=400, detail="技能名称仅允许字母、数字、连字符和下划线")

        if final_name in SKILL_REGISTRY:
            raise HTTPException(status_code=400, detail=f"技能 '{final_name}' 已存在")

        skill_dir = SKILLS_DIR / final_name
        if skill_dir.exists():
            raise HTTPException(status_code=400, detail=f"技能目录 '{final_name}' 已存在")

        # 第三步：如果没有 SKILL.md，自动生成
        if not skill_md_path.exists():
            md_content = f"""---
name: {final_name}
description: "{final_desc}"
---

# {final_name} Skill

{final_desc}
"""
            (tmp_extract / "SKILL.md").write_text(md_content, encoding="utf-8")

        # 第四步：移动到正式目录
        shutil.move(str(tmp_extract), str(skill_dir))

        # 刷新注册表
        SKILL_REGISTRY.update(_scan_skills())

        logger.info(f"技能包 '{final_name}' 上传成功")

        return {
            "name": final_name,
            "description": final_desc,
            "message": "技能包上传成功",
        }
    except zipfile.BadZipFile:
        # 清理临时解压目录
        if tmp_extract.exists():
            shutil.rmtree(tmp_extract)
        raise HTTPException(status_code=400, detail="无效的 ZIP 文件")
    except HTTPException:
        # 清理临时解压目录（校验失败等情况）
        if tmp_extract.exists():
            shutil.rmtree(tmp_extract)
        raise
    except Exception as e:
        # 清理临时解压目录
        if tmp_extract.exists():
            shutil.rmtree(tmp_extract)
        logger.error(f"上传技能包失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传技能包失败: {str(e)}")
    finally:
        import os
        try:
            os.remove(tmp_path)
        except:
            pass


@router.delete("/{skill_name}", summary="删除技能")
async def delete_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user),
):
    """删除指定技能（删除整个目录）

    Args:
        skill_name: 技能名称
    """
    if skill_name not in SKILL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在")

    skill_dir = SKILLS_DIR / skill_name

    # 也尝试按目录名查找
    if not skill_dir.exists():
        # 按注册表中的 name 查找实际目录
        found = False
        if SKILLS_DIR.exists():
            for d in SKILLS_DIR.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    content = (d / "SKILL.md").read_text(encoding="utf-8")
                    meta, _ = _parse_frontmatter(content)
                    if meta.get("name", d.name) == skill_name:
                        skill_dir = d
                        found = True
                        break
        if not found:
            raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 目录不存在")

    # 安全检查：确保路径在 skills 目录内
    try:
        skill_dir.resolve().relative_to(SKILLS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    # 删除目录
    shutil.rmtree(skill_dir)

    # 刷新注册表
    SKILL_REGISTRY.clear()
    SKILL_REGISTRY.update(_scan_skills())

    logger.info(f"技能 '{skill_name}' 已删除")

    return {"message": f"技能 '{skill_name}' 删除成功"}
