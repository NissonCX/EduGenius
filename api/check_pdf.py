"""
PDF 检查工具
用于快速检查 PDF 文件是否有可提取的文本层

使用方法：
    python api/check_pdf.py /path/to/your/file.pdf
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.pdf_validator import print_pdf_validation_report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python api/check_pdf.py <pdf文件路径>")
        print("示例: python api/check_pdf.py /path/to/textbook.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        sys.exit(1)

    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ 不是 PDF 文件: {pdf_path}")
        sys.exit(1)

    print_pdf_validation_report(pdf_path)
