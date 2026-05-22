"""图表生成工具 - 将数据可视化为图表图片"""
import os
import io
from datetime import datetime
from typing import List, Optional
from loguru import logger
from langchain.tools import tool

from app.config import settings

# 图表文件存储目录（与报告共用 reports 目录）
CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "reports")

# 支持的图表类型
SUPPORTED_CHART_TYPES = {"bar", "line", "pie", "scatter", "radar"}

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {"png", "jpg", "svg"}

# 最大数据点数量
MAX_DATA_POINTS = 100


@tool(parse_docstring=True)
async def chart_generator(
    title: str,
    chart_type: str,
    labels: List[str],
    datasets: List[dict],
    image_format: str = "png",
    x_label: str = "",
    y_label: str = "",
    width: int = 10,
    height: int = 6,
) -> str:
    """
    生成数据可视化图表并返回下载信息。当用户需要将数据以图表形式展示、进行数据可视化、画图、绘制图表时调用此工具。支持柱状图、折线图、饼图、散点图和雷达图。

    Args:
        title (str): 图表标题。
        chart_type (str): 图表类型，可选 "bar"（柱状图）、"line"（折线图）、"pie"（饼图）、"scatter"（散点图）、"radar"（雷达图）。
        labels (List[str]): 数据标签列表，如 ["一月", "二月", "三月"]。饼图时为各扇区标签。
        datasets (List[dict]): 数据集列表，每个数据集为字典。格式示例: [{"name": "销售额", "data": [100, 200, 150]}]。饼图只需一个数据集，data 为数值列表。散点图 data 为 [[x1,y1], [x2,y2], ...]。
        image_format (str): 图片格式，可选 "png"、"jpg"、"svg"，默认为 "png"。
        x_label (str): X轴标签（饼图和雷达图可忽略），默认为空。
        y_label (str): Y轴标签（饼图和雷达图可忽略），默认为空。
        width (int): 图表宽度（英寸），默认10。
        height (int): 图表高度（英寸），默认6。

    Returns:
        str: 图表生成结果，包含图表ID、文件名和下载链接。

    Examples:
        - "帮我画一个柱状图" -> chart_type="bar", labels=["A","B","C"], datasets=[{"name":"销量","data":[10,20,15]}]
        - "画一个饼图展示占比" -> chart_type="pie", labels=["产品A","产品B","产品C"], datasets=[{"name":"占比","data":[40,35,25]}]
        - "用折线图展示趋势" -> chart_type="line", labels=["1月","2月","3月"], datasets=[{"name":"收入","data":[100,150,180]}]
    """
    return await _generate_chart(title, chart_type, labels, datasets, image_format, x_label, y_label, width, height)


async def _generate_chart(
    title: str,
    chart_type: str,
    labels: List[str],
    datasets: List[dict],
    image_format: str = "png",
    x_label: str = "",
    y_label: str = "",
    width: int = 10,
    height: int = 6,
) -> str:
    """执行图表生成"""

    # 参数校验
    if not title or not title.strip():
        return "图表标题不能为空"

    chart_type = chart_type.strip().lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        types_str = "、".join(SUPPORTED_CHART_TYPES)
        return f"不支持的图表类型: {chart_type}，支持的类型: {types_str}"

    if not labels or len(labels) == 0:
        return "数据标签(labels)不能为空"

    if not datasets or len(datasets) == 0:
        return "数据集(datasets)不能为空"

    image_format = image_format.strip().lower()
    if image_format not in SUPPORTED_IMAGE_FORMATS:
        formats_str = "、".join(SUPPORTED_IMAGE_FORMATS)
        return f"不支持的图片格式: {image_format}，支持的格式: {formats_str}"

    # 数据点数量限制
    if len(labels) > MAX_DATA_POINTS:
        return f"数据点数量超过限制（最大 {MAX_DATA_POINTS}），当前 {len(labels)}"

    try:
        import matplotlib
        matplotlib.use("Agg")  # 非交互式后端，服务器环境必须
        import matplotlib.pyplot as plt
        import numpy as np

        # 设置中文字体
        _setup_chinese_font(plt)

        # 创建图表
        fig, ax = plt.subplots(figsize=(width, height), dpi=150)

        # 根据图表类型绘制
        if chart_type == "bar":
            _draw_bar(ax, title, labels, datasets, x_label, y_label)
        elif chart_type == "line":
            _draw_line(ax, title, labels, datasets, x_label, y_label)
        elif chart_type == "pie":
            _draw_pie(ax, title, labels, datasets)
        elif chart_type == "scatter":
            _draw_scatter(ax, title, labels, datasets, x_label, y_label)
        elif chart_type == "radar":
            fig, ax = _draw_radar(title, labels, datasets, width, height)

        # 调整布局
        fig.tight_layout()

        # 保存到文件
        file_name, file_path = _build_file_path(title, image_format)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        fig.savefig(file_path, format=image_format, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        file_size = os.path.getsize(file_path)

        # 保存记录到数据库（复用 ReportTable）
        report_id = await _save_chart_record(title, file_name, file_path, image_format, file_size)

        # 构建下载链接
        download_url = f"/api/v1/report/download/{report_id}"

        # 构建返回结果
        result_parts = [
            "📊 图表生成成功！",
            f"📋 标题: {title}",
            f"📈 类型: {chart_type}",
            f"📁 文件名: {file_name}",
            f"📦 格式: {image_format}",
            f"💾 大小: {file_size} 字节",
            f"🔗 下载链接: {download_url}",
            "💡 用户可通过下载链接获取图表文件",
        ]

        return "\n".join(result_parts)

    except ImportError as e:
        logger.error(f"缺少依赖库: {e}")
        return "图表生成失败：缺少依赖库 matplotlib，请安装后重试"
    except Exception as e:
        logger.error(f"图表生成失败: {e}")
        return f"图表生成失败: {str(e)}"


def _setup_chinese_font(plt):
    """设置中文字体，解决中文乱码问题"""
    import matplotlib
    import platform

    system = platform.system()

    # 候选中文字体列表
    candidates = []
    if system == "Windows":
        candidates = ["SimHei", "Microsoft YaHei", "KaiTi", "FangSong"]
    elif system == "Darwin":
        candidates = ["PingFang SC", "Heiti SC", "STHeiti", "Arial Unicode MS"]
    else:
        candidates = ["WenQuanYi Micro Hei", "Noto Sans CJK SC", "DejaVu Sans"]

    # 尝试查找可用字体
    available_fonts = set([f.name for f in matplotlib.font_manager.fontManager.ttflist])

    for font_name in candidates:
        if font_name in available_fonts:
            plt.rcParams["font.sans-serif"] = [font_name]
            plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
            logger.debug(f"设置中文字体: {font_name}")
            return

    # 未找到中文字体，使用默认字体并关闭警告
    plt.rcParams["axes.unicode_minus"] = False
    logger.warning(f"未找到中文字体，图表中文可能显示为方块。候选字体: {candidates}")


def _draw_bar(ax, title, labels, datasets, x_label, y_label):
    """绘制柱状图"""
    import numpy as np

    x = np.arange(len(labels))
    n_datasets = len(datasets)
    bar_width = 0.8 / max(n_datasets, 1)

    # 预定义颜色
    colors = _get_color_palette(n_datasets)

    for i, ds in enumerate(datasets):
        name = ds.get("name", f"数据集{i+1}")
        data = ds.get("data", [])
        if len(data) != len(labels):
            data = data[:len(labels)] + [0] * (len(labels) - len(data))

        offset = (i - n_datasets / 2 + 0.5) * bar_width
        bars = ax.bar(x + offset, data, bar_width * 0.9, label=name, color=colors[i], edgecolor="white", linewidth=0.5)

        # 在柱子上方显示数值
        for bar, val in zip(bars, data):
            if val != 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{val}", ha="center", va="bottom", fontsize=8)

    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    if x_label:
        ax.set_xlabel(x_label, fontsize=12)
    if y_label:
        ax.set_ylabel(y_label, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _draw_line(ax, title, labels, datasets, x_label, y_label):
    """绘制折线图"""
    import numpy as np

    x = np.arange(len(labels))
    colors = _get_color_palette(len(datasets))
    markers = ["o", "s", "^", "D", "v", "p", "*", "h"]

    for i, ds in enumerate(datasets):
        name = ds.get("name", f"数据集{i+1}")
        data = ds.get("data", [])
        if len(data) != len(labels):
            data = data[:len(labels)] + [0] * (len(labels) - len(data))

        marker = markers[i % len(markers)]
        ax.plot(x, data, marker=marker, label=name, color=colors[i],
                linewidth=2, markersize=6, markeredgecolor="white", markeredgewidth=1)

        # 在数据点旁显示数值
        for xi, val in zip(x, data):
            if val != 0:
                ax.annotate(f"{val}", (xi, val), textcoords="offset points",
                           xytext=(0, 10), ha="center", fontsize=8)

    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    if x_label:
        ax.set_xlabel(x_label, fontsize=12)
    if y_label:
        ax.set_ylabel(y_label, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _draw_pie(ax, title, labels, datasets):
    """绘制饼图"""
    ds = datasets[0]
    data = ds.get("data", [])
    if len(data) != len(labels):
        data = data[:len(labels)] + [0] * (len(labels) - len(data))

    # 过滤掉0值
    filtered_labels = []
    filtered_data = []
    for label, val in zip(labels, data):
        if val > 0:
            filtered_labels.append(label)
            filtered_data.append(val)

    if not filtered_data:
        raise ValueError("饼图数据全为0，无法绘制")

    colors = _get_color_palette(len(filtered_labels))

    # 突出最大扇区
    max_idx = filtered_data.index(max(filtered_data))
    explode = [0.05] * len(filtered_data)
    explode[max_idx] = 0.1

    wedges, texts, autotexts = ax.pie(
        filtered_data,
        labels=filtered_labels,
        autopct="%1.1f%%",
        colors=colors,
        explode=explode,
        startangle=90,
        pctdistance=0.85,
        shadow=False,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )

    # 美化文字
    for text in texts:
        text.set_fontsize(11)
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)


def _draw_scatter(ax, title, labels, datasets, x_label, y_label):
    """绘制散点图"""
    import numpy as np

    colors = _get_color_palette(len(datasets))

    for i, ds in enumerate(datasets):
        name = ds.get("name", f"数据集{i+1}")
        data = ds.get("data", [])

        # 散点图 data 格式: [[x1,y1], [x2,y2], ...]
        if data and isinstance(data[0], (list, tuple)):
            x_vals = [point[0] for point in data]
            y_vals = [point[1] for point in data]
        else:
            # 如果只给了一维数据，用索引作为 x
            x_vals = list(range(len(data)))
            y_vals = data

        ax.scatter(x_vals, y_vals, label=name, color=colors[i],
                   s=80, alpha=0.7, edgecolors="white", linewidth=1)

    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    if x_label:
        ax.set_xlabel(x_label, fontsize=12)
    if y_label:
        ax.set_ylabel(y_label, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _draw_radar(title, labels, datasets, width, height):
    """绘制雷达图"""
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt

    # 雷达图需要极坐标
    fig = plt.figure(figsize=(width, height), dpi=150)
    ax = fig.add_subplot(111, polar=True)

    # 计算角度
    n_labels = len(labels)
    angles = np.linspace(0, 2 * np.pi, n_labels, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    colors = _get_color_palette(len(datasets))

    for i, ds in enumerate(datasets):
        name = ds.get("name", f"数据集{i+1}")
        data = ds.get("data", [])
        if len(data) != n_labels:
            data = data[:n_labels] + [0] * (n_labels - len(data))

        # 归一化数据到 0-1
        max_val = max(data) if max(data) > 0 else 1
        normalized = [d / max_val for d in data]
        normalized += normalized[:1]  # 闭合

        ax.plot(angles, normalized, "o-", label=name, color=colors[i], linewidth=2, markersize=6)
        ax.fill(angles, normalized, alpha=0.15, color=colors[i])

    # 设置标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=30)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
    ax.set_ylim(0, 1.1)

    return fig, ax


def _get_color_palette(n: int) -> list:
    """获取美观的调色板"""
    palette = [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
        "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
        "#86BCB6", "#8CD17D", "#B6992D", "#499894", "#E15759",
    ]
    if n <= len(palette):
        return palette[:n]
    # 如果需要更多颜色，循环使用
    return [palette[i % len(palette)] for i in range(n)]


def _build_file_path(title: str, image_format: str) -> tuple:
    """构建文件名和存储路径"""
    # 清理标题中的非法文件名字符
    safe_title = title
    for char in ["\\", "/", ":", "*", "?", "<", ">", "|"]:
        safe_title = safe_title.replace(char, "_")
    # 单独处理双引号
    safe_title = safe_title.replace('"', "_")

    # 限制文件名长度
    if len(safe_title) > 100:
        safe_title = safe_title[:100]

    # 日期目录
    date_dir = datetime.now().strftime("%Y%m")

    # 扩展名映射
    ext_map = {
        "png": ".png",
        "jpg": ".jpg",
        "svg": ".svg",
    }
    ext = ext_map.get(image_format, ".png")

    # 时间戳后缀避免重名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{safe_title}_{timestamp}{ext}"

    # 完整路径
    file_path = os.path.join(CHART_DIR, date_dir, file_name)

    return file_name, file_path


async def _save_chart_record(title: str, file_name: str, file_path: str, image_format: str, file_size: int) -> str:
    """保存图表记录到数据库（复用 ReportTable）"""
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.database.engine import async_engine
    from app.database.models.report import ReportTable, ReportStatus

    if async_engine is None:
        # 数据库未连接，返回临时ID
        import hashlib
        return hashlib.md5(file_path.encode()).hexdigest()[:16]

    async with AsyncSession(async_engine) as session:
        report = ReportTable(
            title=title,
            file_name=file_name,
            file_path=file_path,
            file_format=image_format,  # 用 image_format 作为 file_format
            file_size=file_size,
            status=ReportStatus.COMPLETED,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report.id
