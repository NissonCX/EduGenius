"""
PDF 预检查工具
在上传前检查 PDF 是否有可提取的文本层
"""
import fitz  # PyMuPDF
from typing import Dict, Any


def validate_pdf_before_upload(file_path: str) -> Dict[str, Any]:
    """
    预检查 PDF 文件，判断是否有文本层

    Returns:
        {
            'has_text': bool,           # 是否有可提取的文本
            'total_pages': int,          # 总页数
            'text_pages': int,           # 有文本的页数
            'image_pages': int,          # 纯图片页数
            'text_ratio': float,         # 文本页占比
            'is_scan': bool,             # 是否是扫描版
            'recommendation': str,       # 建议
            'sample_text': str           # 提取的示例文本（前200字符）
        }
    """
    result = {
        'has_text': False,
        'total_pages': 0,
        'text_pages': 0,
        'image_pages': 0,
        'text_ratio': 0.0,
        'is_scan': False,
        'recommendation': '',
        'sample_text': ''
    }

    try:
        with fitz.open(file_path) as doc:
            result['total_pages'] = len(doc)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if text.strip():
                    result['text_pages'] += 1
                    # 保存第一页的示例文本
                    if not result['sample_text']:
                        result['sample_text'] = text[:200]
                else:
                    result['image_pages'] += 1

            # 计算文本页占比
            if result['total_pages'] > 0:
                result['text_ratio'] = result['text_pages'] / result['total_pages']

            # 判断是否有文本
            result['has_text'] = result['text_pages'] > 0

            # 判断是否是扫描版
            # 如果超过 80% 的页面没有文本，认为是扫描版
            result['is_scan'] = result['text_ratio'] < 0.2

            # 生成建议
            if result['is_scan']:
                result['recommendation'] = (
                    f"⚠️ 这个 PDF 可能是扫描版（{result['text_pages']}/{result['total_pages']} 页有文本）。\n"
                    f"💡 建议：\n"
                    f"   1. 使用 PDF 转文字工具（如 Adobe Acrobat、ABBYY FineReader）处理\n"
                    f"   2. 寻找该教材的电子版（通常出版社会提供）\n"
                    f"   3. 系统将添加 OCR 支持功能，敬请期待"
                )
            elif result['text_ratio'] < 0.5:
                result['recommendation'] = (
                    f"⚠️ 这个 PDF 部分页面是扫描版（{result['text_pages']}/{result['total_pages']} 页有文本）。\n"
                    f"💡 建议：\n"
                    f"   1. 可以上传，但部分内容可能无法识别\n"
                    f"   2. 系统会尽量提取有文本的页面"
                )
            else:
                result['recommendation'] = (
                    f"✅ 这个 PDF 可以正常处理（{result['text_pages']}/{result['total_pages']} 页有文本）。\n"
                    f"💡 可以上传使用"
                )

    except Exception as e:
        result['recommendation'] = f"❌ PDF 文件损坏或格式不支持: {str(e)}"

    return result


def print_pdf_validation_report(file_path: str) -> None:
    """打印 PDF 验证报告（用于调试）"""
    result = validate_pdf_before_upload(file_path)

    print("\n" + "="*60)
    print("📋 PDF 预检查报告")
    print("="*60)
    print(f"总页数: {result['total_pages']}")
    print(f"文本页: {result['text_pages']}")
    print(f"图片页: {result['image_pages']}")
    print(f"文本占比: {result['text_ratio']:.1%}")
    print(f"是否有文本: {'✅ 是' if result['has_text'] else '❌ 否'}")
    print(f"是否扫描版: {'⚠️  是' if result['is_scan'] else '✅ 否'}")

    if result['sample_text']:
        print(f"\n📝 示例文本（前200字符）:")
        print(f"   {result['sample_text'][:100]}...")

    print(f"\n💡 建议:")
    for line in result['recommendation'].split('\n'):
        print(f"   {line}")

    print("="*60 + "\n")
