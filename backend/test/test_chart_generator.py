"""chart_generator 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
import os
from app.tools.chart_generator.action import (
    chart_generator,
    _generate_chart,
    _build_file_path,
    _get_color_palette,
    _setup_chinese_font,
    SUPPORTED_CHART_TYPES,
    SUPPORTED_IMAGE_FORMATS,
)


async def test_empty_title():
    """测试空标题"""
    result = await _generate_chart(
        title="", chart_type="bar",
        labels=["A", "B"], datasets=[{"name": "test", "data": [1, 2]}]
    )
    assert "标题不能为空" in result
    print("✅ 空标题校验 测试通过")


async def test_invalid_chart_type():
    """测试无效图表类型"""
    result = await _generate_chart(
        title="测试", chart_type="bubble",
        labels=["A", "B"], datasets=[{"name": "test", "data": [1, 2]}]
    )
    assert "不支持" in result
    print("✅ 无效图表类型校验 测试通过")


async def test_empty_labels():
    """测试空标签"""
    result = await _generate_chart(
        title="测试", chart_type="bar",
        labels=[], datasets=[{"name": "test", "data": [1, 2]}]
    )
    assert "标签" in result or "不能为空" in result
    print("✅ 空标签校验 测试通过")


async def test_empty_datasets():
    """测试空数据集"""
    result = await _generate_chart(
        title="测试", chart_type="bar",
        labels=["A", "B"], datasets=[]
    )
    assert "数据集" in result or "不能为空" in result
    print("✅ 空数据集校验 测试通过")


async def test_invalid_image_format():
    """测试无效图片格式"""
    result = await _generate_chart(
        title="测试", chart_type="bar",
        labels=["A", "B"], datasets=[{"name": "test", "data": [1, 2]}],
        image_format="gif"
    )
    assert "不支持" in result
    print("✅ 无效图片格式校验 测试通过")


async def test_build_file_path():
    """测试文件路径构建"""
    file_name, file_path = _build_file_path("测试图表", "png")
    assert file_name.endswith(".png")
    assert "测试图表" in file_name
    print(f"✅ 文件路径构建 测试通过 - {file_name}")


async def test_build_file_path_special_chars():
    """测试特殊字符标题"""
    file_name, file_path = _build_file_path("图表:测试/特殊*字符", "jpg")
    assert ":" not in file_name
    assert "/" not in file_name
    assert "*" not in file_name
    assert file_name.endswith(".jpg")
    print("✅ 特殊字符标题 测试通过")


async def test_build_file_path_svg():
    """测试SVG格式路径"""
    file_name, file_path = _build_file_path("SVG图表", "svg")
    assert file_name.endswith(".svg")
    print("✅ SVG格式路径 测试通过")


async def test_color_palette():
    """测试调色板"""
    colors = _get_color_palette(3)
    assert len(colors) == 3
    assert colors[0] == "#4E79A7"
    print("✅ 调色板 测试通过")


async def test_color_palette_large():
    """测试大量颜色的调色板"""
    colors = _get_color_palette(20)
    assert len(colors) == 20
    print("✅ 大量颜色调色板 测试通过")


async def test_supported_types():
    """测试支持的图表类型"""
    assert "bar" in SUPPORTED_CHART_TYPES
    assert "line" in SUPPORTED_CHART_TYPES
    assert "pie" in SUPPORTED_CHART_TYPES
    assert "scatter" in SUPPORTED_CHART_TYPES
    assert "radar" in SUPPORTED_CHART_TYPES
    print("✅ 支持的图表类型 测试通过")


async def test_supported_formats():
    """测试支持的图片格式"""
    assert "png" in SUPPORTED_IMAGE_FORMATS
    assert "jpg" in SUPPORTED_IMAGE_FORMATS
    assert "svg" in SUPPORTED_IMAGE_FORMATS
    print("✅ 支持的图片格式 测试通过")


async def test_tool_interface():
    """测试工具接口"""
    assert chart_generator.name == "chart_generator"
    desc = chart_generator.description
    assert "图表" in desc or "可视化" in desc
    print("✅ 工具接口 测试通过")


async def test_generate_bar_chart():
    """测试生成柱状图"""
    result = await _generate_chart(
        title="季度销售额",
        chart_type="bar",
        labels=["Q1", "Q2", "Q3", "Q4"],
        datasets=[{"name": "销售额", "data": [100, 200, 150, 300]}],
        x_label="季度",
        y_label="销售额（万元）",
    )
    assert "图表生成成功" in result
    assert "下载链接" in result
    assert "bar" in result
    print("✅ 生成柱状图 测试通过")


async def test_generate_line_chart():
    """测试生成折线图"""
    result = await _generate_chart(
        title="月度趋势",
        chart_type="line",
        labels=["1月", "2月", "3月", "4月", "5月"],
        datasets=[{"name": "收入", "data": [50, 80, 120, 90, 150]}],
    )
    assert "图表生成成功" in result
    assert "line" in result
    print("✅ 生成折线图 测试通过")


async def test_generate_pie_chart():
    """测试生成饼图"""
    result = await _generate_chart(
        title="部门占比",
        chart_type="pie",
        labels=["研发部", "市场部", "销售部", "行政部"],
        datasets=[{"name": "人数", "data": [40, 25, 20, 15]}],
    )
    assert "图表生成成功" in result
    assert "pie" in result
    print("✅ 生成饼图 测试通过")


async def test_generate_scatter_chart():
    """测试生成散点图"""
    result = await _generate_chart(
        title="身高体重分布",
        chart_type="scatter",
        labels=["点"],
        datasets=[{"name": "数据", "data": [[160, 50], [170, 65], [180, 75]]}],
        x_label="身高(cm)",
        y_label="体重(kg)",
    )
    assert "图表生成成功" in result
    assert "scatter" in result
    print("✅ 生成散点图 测试通过")


async def test_generate_radar_chart():
    """测试生成雷达图"""
    result = await _generate_chart(
        title="能力评估",
        chart_type="radar",
        labels=["编程", "设计", "沟通", "管理", "创新"],
        datasets=[{"name": "张三", "data": [90, 70, 85, 60, 80]}],
    )
    assert "图表生成成功" in result
    assert "radar" in result
    print("✅ 生成雷达图 测试通过")


async def test_generate_multi_dataset_bar():
    """测试多数据集柱状图"""
    result = await _generate_chart(
        title="多产品对比",
        chart_type="bar",
        labels=["Q1", "Q2", "Q3", "Q4"],
        datasets=[
            {"name": "产品A", "data": [100, 150, 120, 180]},
            {"name": "产品B", "data": [80, 120, 160, 140]},
        ],
    )
    assert "图表生成成功" in result
    print("✅ 多数据集柱状图 测试通过")


async def test_generate_svg_chart():
    """测试生成SVG格式图表"""
    result = await _generate_chart(
        title="SVG测试",
        chart_type="bar",
        labels=["A", "B", "C"],
        datasets=[{"name": "数据", "data": [10, 20, 15]}],
        image_format="svg",
    )
    assert "图表生成成功" in result
    assert ".svg" in result
    print("✅ SVG格式图表 测试通过")


async def test_data_length_mismatch():
    """测试数据长度不匹配时自动补零"""
    result = await _generate_chart(
        title="数据补零测试",
        chart_type="bar",
        labels=["A", "B", "C", "D"],
        datasets=[{"name": "数据", "data": [10, 20]}],  # 只有2个数据点，4个标签
    )
    assert "图表生成成功" in result
    print("✅ 数据长度不匹配自动补零 测试通过")


async def main():
    await test_empty_title()
    await test_invalid_chart_type()
    await test_empty_labels()
    await test_empty_datasets()
    await test_invalid_image_format()
    await test_build_file_path()
    await test_build_file_path_special_chars()
    await test_build_file_path_svg()
    await test_color_palette()
    await test_color_palette_large()
    await test_supported_types()
    await test_supported_formats()
    await test_tool_interface()
    await test_generate_bar_chart()
    await test_generate_line_chart()
    await test_generate_pie_chart()
    await test_generate_scatter_chart()
    await test_generate_radar_chart()
    await test_generate_multi_dataset_bar()
    await test_generate_svg_chart()
    await test_data_length_mismatch()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
