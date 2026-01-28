"""
Document processing utilities for PDF, TXT, and DOCX files.
Extracts text, identifies chapters, and creates chunks for embedding.
"""
import io
from typing import List, Dict, Tuple, Optional
from pypdf import PdfReader
from docx import Document as DocxDocument


# ============== PDF Processing ==============
def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, Dict[str, any]]:
    """
    Extract text and metadata from PDF file.

    Args:
        file_bytes: Raw PDF file content

    Returns:
        Tuple of (extracted_text, metadata_dict)
    """
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)

    # Extract text from all pages
    text_content = []
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            text_content.append(text)

    full_text = "\n\n".join(text_content)

    # Extract metadata
    metadata = {
        "total_pages": len(reader.pages),
        "title": reader.metadata.get("/Title", "") if reader.metadata else "",
        "author": reader.metadata.get("/Author", "") if reader.metadata else ""
    }

    return full_text, metadata


# ============== TXT Processing ==============
def extract_text_from_txt(file_bytes: bytes, encoding: str = "utf-8") -> str:
    """
    Extract text from TXT file.

    Args:
        file_bytes: Raw TXT file content
        encoding: File encoding (default: utf-8)

    Returns:
        Extracted text content
    """
    try:
        return file_bytes.decode(encoding)
    except UnicodeDecodeError:
        # Try common encodings
        for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                return file_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("Unable to decode file with common encodings")


# ============== DOCX Processing ==============
def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX file.

    Args:
        file_bytes: Raw DOCX file content

    Returns:
        Extracted text content
    """
    docx_file = io.BytesIO(file_bytes)
    doc = DocxDocument(docx_file)

    paragraphs = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n\n".join(paragraphs)


# ============== Chapter Detection ==============
def detect_chapters(text: str) -> List[Dict[str, any]]:
    """
    Detect chapter structure in text.

    Args:
        text: Full document text

    Returns:
        List of chapter dictionaries with title, start_index, content
    """
    chapters = []

    # Common chapter patterns (Chinese and English)
    chapter_patterns = [
        r"第[一二三四五六七八九十百千\d]+章[\s\.:：]*(.+)",
        r"Chapter[\s\d]+[\.:]*(.+)",
        r"[\d]+\s*(.+)",  # Number sections
    ]

    # For now, use a simple heuristic
    # In production, use NLP or more sophisticated pattern matching
    lines = text.split("\n")
    current_chapter = None
    chapter_content = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Detect chapter headers (simplified)
        if line.startswith("第") and "章" in line:
            # Save previous chapter
            if current_chapter:
                chapters.append({
                    "title": current_chapter,
                    "content": "\n".join(chapter_content)
                })

            # Start new chapter
            current_chapter = line
            chapter_content = []
        elif line.startswith("Chapter ") or line.startswith("CHAPTER "):
            # Save previous chapter
            if current_chapter:
                chapters.append({
                    "title": current_chapter,
                    "content": "\n".join(chapter_content)
                })

            # Start new chapter
            current_chapter = line
            chapter_content = []
        else:
            chapter_content.append(line)

    # Don't forget the last chapter
    if current_chapter and chapter_content:
        chapters.append({
            "title": current_chapter,
            "content": "\n".join(chapter_content)
        })

    # If no chapters detected, treat entire document as one chapter
    if not chapters:
        chapters = [{
            "title": "全文",
            "content": text
        }]

    return chapters


# ============== Text Chunking ==============
def chunk_text_by_chapter(
    chapters: List[Dict[str, any]],
    max_chunk_size: int = 1000,
    overlap: int = 100
) -> List[Dict[str, any]]:
    """
    Split chapters into chunks for embedding.

    Args:
        chapters: List of chapter dictionaries
        max_chunk_size: Maximum characters per chunk
        overlap: Character overlap between chunks

    Returns:
        List of chunk dictionaries with text, chapter, chunk_index
    """
    chunks = []

    for chapter_idx, chapter in enumerate(chapters):
        chapter_title = chapter["title"]
        chapter_content = chapter["content"]

        # Split content into chunks
        chunk_index = 0
        start = 0

        while start < len(chapter_content):
            end = start + max_chunk_size
            chunk_text = chapter_content[start:end]

            chunks.append({
                "text": chunk_text,
                "chapter": chapter_title,
                "chapter_number": chapter_idx + 1,
                "chunk_index": chunk_index,
                "start_char": start,
                "end_char": end
            })

            chunk_index += 1
            start = end - overlap  # Overlap for context

    return chunks


# ============== Main Processing Pipeline ==============
async def process_document(
    file_bytes: bytes,
    filename: str,
    file_type: str
) -> Tuple[str, List[Dict[str, any]], Dict[str, any]]:
    """
    Main document processing pipeline.

    Args:
        file_bytes: Raw file content
        filename: Original filename
        file_type: File type (pdf, txt, docx)

    Returns:
        Tuple of (full_text, chunks, metadata)
    """
    # Extract text based on file type
    if file_type == "pdf":
        text, metadata = extract_text_from_pdf(file_bytes)
    elif file_type == "txt":
        text = extract_text_from_txt(file_bytes)
        metadata = {"total_pages": 0, "title": filename}
    elif file_type == "docx":
        text = extract_text_from_docx(file_bytes)
        metadata = {"total_pages": 0, "title": filename}
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # Detect chapters
    chapters = detect_chapters(text)

    # Create chunks
    chunks = chunk_text_by_chapter(chapters)

    # Update metadata
    metadata["total_chapters"] = len(chapters)
    metadata["total_chunks"] = len(chunks)

    return text, chunks, metadata
