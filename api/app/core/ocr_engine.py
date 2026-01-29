"""
OCR 引擎 - 使用 PaddleOCR 进行文字识别

支持：
- PDF 页面渲染为图片
- 批量 OCR 识别
- 进度回调
- 置信度评估
"""
import os
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import tempfile
import shutil


class OCREngine:
    """PaddleOCR 引擎封装"""

    def __init__(self):
        self._engine = None
        self._is_initialized = False

    def _initialize(self):
        """延迟初始化 OCR 引擎（只在需要时加载）"""
        if self._is_initialized:
            return

        try:
            from paddleocr import PaddleOCR
            print("🔧 正在初始化 PaddleOCR 引擎...")

            # 使用轻量级模型（更快、内存占用更小）
            self._engine = PaddleOCR(
                use_angle_cls=True,  # 启用文字方向分类
                lang='ch',           # 中文
                use_gpu=False,       # 不使用 GPU（兼容性更好）
                show_log=False,      # 关闭详细日志
                # 使用轻量级模型
                det_model_dir=None,  # 使用默认轻量检测模型
                rec_model_dir=None,  # 使用默认轻量识别模型
                cls_model_dir=None   # 使用默认方向分类模型
            )

            self._is_initialized = True
            print("✅ PaddleOCR 引擎初始化完成")

        except ImportError:
            raise ImportError(
                "PaddleOCR 未安装。请运行: pip install paddleocr"
            )
        except Exception as e:
            raise RuntimeError(f"PaddleOCR 初始化失败: {e}")

    def process_pdf_page(
        self,
        pdf_path: str,
        page_num: int,
        dpi: int = 200,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        处理 PDF 的单个页面

        Args:
            pdf_path: PDF 文件路径
            page_num: 页码（从0开始）
            dpi: 渲染 DPI（越高越清晰但越慢）
            progress_callback: 进度回调函数 callback(current_page, total_pages)

        Returns:
            {
                'page_num': int,
                'text': str,
                'confidence': float,
                'blocks': List[Dict],  # 识别的文本块
                'success': bool,
                'error': str or None
            }
        """
        self._initialize()

        try:
            # 打开 PDF
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # 渲染页面为图片
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # 保存为临时图片文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img_path = tmp.name
                pix.save(img_path)

            try:
                # OCR 识别
                result = self._engine.ocr(img_path, cls=True)

                # 提取文本和置信度
                text_parts = []
                confidence_scores = []
                blocks = []

                if result and result[0]:
                    for line in result[0]:
                        if line:
                            box = line[0]  # 边界框坐标
                            text_info = line[1]  # (text, confidence)
                            text = text_info[0]
                            confidence = text_info[1]

                            text_parts.append(text)
                            confidence_scores.append(confidence)

                            blocks.append({
                                'text': text,
                                'confidence': confidence,
                                'box': box
                            })

                # 计算平均置信度
                avg_confidence = (
                    sum(confidence_scores) / len(confidence_scores)
                    if confidence_scores else 0.0
                )

                # 合并文本
                full_text = '\n'.join(text_parts)

                return {
                    'page_num': page_num + 1,  # 转为1-based
                    'text': full_text,
                    'confidence': avg_confidence,
                    'blocks': blocks,
                    'success': True,
                    'error': None
                }

            finally:
                # 清理临时图片
                if os.path.exists(img_path):
                    os.remove(img_path)

        except Exception as e:
            return {
                'page_num': page_num + 1,
                'text': '',
                'confidence': 0.0,
                'blocks': [],
                'success': False,
                'error': str(e)
            }

    def process_pdf(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None,
        dpi: int = 200,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        处理整个 PDF 或指定页面

        Args:
            pdf_path: PDF 文件路径
            pages: 要处理的页码列表（None表示全部页面）
            dpi: 渲染 DPI
            progress_callback: 进度回调 callback(current, total, message)

        Returns:
            {
                'success': bool,
                'total_pages': int,
                'processed_pages': int,
                'pages': List[Dict],  # 每页的结果
                'full_text': str,     # 完整文本
                'avg_confidence': float,
                'errors': List[str]
            }
        """
        self._initialize()

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            # 确定要处理的页面
            if pages is None:
                pages_to_process = list(range(total_pages))
            else:
                pages_to_process = [p - 1 for p in pages]  # 转为0-based

            print(f"\n{'='*60}")
            print(f"📖 开始 OCR 处理")
            print(f"   文件: {pdf_path}")
            print(f"   总页数: {total_pages}")
            print(f"   处理页数: {len(pages_to_process)}")
            print(f"   DPI: {dpi}")
            print(f"{'='*60}\n")

            results = []
            errors = []
            all_text_parts = []
            confidence_scores = []

            for idx, page_num in enumerate(pages_to_process):
                # 报告进度
                if progress_callback:
                    progress_callback(
                        idx + 1,
                        len(pages_to_process),
                        f"正在识别第 {page_num + 1}/{total_pages} 页..."
                    )
                else:
                    print(f"🔄 [{idx+1}/{len(pages_to_process)}] 正在处理第 {page_num+1} 页...")

                # 处理单页
                result = self.process_pdf_page(pdf_path, page_num, dpi)

                if result['success']:
                    results.append(result)
                    all_text_parts.append(result['text'])
                    if result['confidence'] > 0:
                        confidence_scores.append(result['confidence'])
                else:
                    errors.append(f"第{page_num+1}页: {result['error']}")

            # 计算统计信息
            avg_confidence = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores else 0.0
            )

            full_text = '\n\n'.join(all_text_parts)

            print(f"\n{'='*60}")
            print(f"✅ OCR 处理完成")
            print(f"   成功: {len(results)}/{len(pages_to_process)} 页")
            print(f"   平均置信度: {avg_confidence:.1%}")
            if errors:
                print(f"   错误: {len(errors)} 页")
            print(f"   文本长度: {len(full_text)} 字符")
            print(f"{'='*60}\n")

            return {
                'success': True,
                'total_pages': total_pages,
                'processed_pages': len(results),
                'pages': results,
                'full_text': full_text,
                'avg_confidence': avg_confidence,
                'errors': errors
            }

        except Exception as e:
            print(f"❌ OCR 处理失败: {e}")
            return {
                'success': False,
                'total_pages': 0,
                'processed_pages': 0,
                'pages': [],
                'full_text': '',
                'avg_confidence': 0.0,
                'errors': [str(e)]
            }


# 全局 OCR 引擎实例（单例模式）
_ocr_engine_instance = None

def get_ocr_engine() -> OCREngine:
    """获取 OCR 引擎单例"""
    global _ocr_engine_instance
    if _ocr_engine_instance is None:
        _ocr_engine_instance = OCREngine()
    return _ocr_engine_instance
