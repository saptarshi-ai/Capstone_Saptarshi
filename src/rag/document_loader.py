"""
Document Loaders — multi-format ingestion for the RAG pipeline.

Supports: .txt, .md, .docx, .doc (legacy), .pdf (native), .pdf (OCR fallback).
Each loader inherits from BaseDocumentLoader and exposes a synchronous load() -> str.
DocumentLoadFactory.get_loader(path) returns the right loader automatically.

Usage:
    loader = DocumentLoadFactory.get_loader("report.pdf")
    text = loader.load()
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar


class BaseDocumentLoader(ABC):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @abstractmethod
    def load(self) -> str:
        """Load document and return plain text."""
        ...


# ── .txt ──────────────────────────────────────────────────────────────────────

class TextLoader(BaseDocumentLoader):
    """Reads plain-text .txt files."""

    def load(self) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")
        return self.path.read_text(encoding="utf-8")


# ── .md ───────────────────────────────────────────────────────────────────────

class MarkdownLoader(BaseDocumentLoader):
    """Reads Markdown .md files; returns raw markdown text."""

    def load(self) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")
        return self.path.read_text(encoding="utf-8")


# ── .docx ─────────────────────────────────────────────────────────────────────

class DocxLoader(BaseDocumentLoader):
    """
    Reads .docx files using python-docx.
    Extracts paragraph text in order; ignores headers/footers.
    Install: pip install python-docx
    """

    def load(self) -> str:
        try:
            import docx  # python-docx
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")

        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        doc = docx.Document(str(self.path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)


# ── .doc (legacy Word) ────────────────────────────────────────────────────────

class DocLoader(BaseDocumentLoader):
    """
    Reads legacy .doc files via python-docx2txt or antiword fallback.
    Install: pip install docx2txt
    """

    def load(self) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        try:
            import docx2txt
            text = docx2txt.process(str(self.path))
            return text.strip() if text else ""
        except ImportError:
            raise ImportError(
                "Install docx2txt for .doc support: pip install docx2txt"
            )


# ── .pdf (native text) ────────────────────────────────────────────────────────

class PDFLoader(BaseDocumentLoader):
    """
    Reads native (text-layer) PDF files using pdfplumber.
    Falls back to pypdf if pdfplumber is not installed.
    Install: pip install pdfplumber
    """

    def load(self) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        # Try pdfplumber first (better layout handling)
        try:
            import pdfplumber
            pages: list[str] = []
            with pdfplumber.open(str(self.path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages.append(page_text)
            return "\n\n".join(pages)
        except ImportError:
            pass

        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(self.path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(p for p in pages if p.strip())
        except ImportError:
            raise ImportError(
                "Install pdfplumber or pypdf: pip install pdfplumber"
            )


# ── .pdf (OCR fallback for scanned docs) ─────────────────────────────────────

class PDFOcrLoader(BaseDocumentLoader):
    """
    Extracts text from scanned/image-only PDFs using pytesseract + pdf2image.
    Use this when PDFLoader returns empty/garbled text (no text layer).
    Install: pip install pytesseract pdf2image
             brew install tesseract   # macOS
             sudo apt install tesseract-ocr  # Linux
    """

    def load(self) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError(
                "Install OCR deps: pip install pytesseract pdf2image\n"
                "Also install Tesseract binary (see module docstring)."
            )

        images = convert_from_path(str(self.path))
        pages: list[str] = []
        for img in images:
            text = pytesseract.image_to_string(img)
            if text.strip():
                pages.append(text)
        return "\n\n".join(pages)


# ── Factory ───────────────────────────────────────────────────────────────────

class DocumentLoadFactory:
    """
    Auto-selects the right loader from the file extension.

    Supported extensions:
        .txt  → TextLoader
        .md   → MarkdownLoader
        .docx → DocxLoader
        .doc  → DocLoader
        .pdf  → PDFLoader (native text layer)
        .pdfocr → PDFOcrLoader (scanned / OCR)
    """

    _REGISTRY: ClassVar[dict[str, type[BaseDocumentLoader]]] = {
        ".txt":    TextLoader,
        ".md":     MarkdownLoader,
        ".docx":   DocxLoader,
        ".doc":    DocLoader,
        ".pdf":    PDFLoader,
        ".pdfocr": PDFOcrLoader,
    }

    @classmethod
    def get_loader(cls, file_path: str | Path) -> BaseDocumentLoader:
        path = Path(file_path)
        ext = path.suffix.lower()

        loader_cls = cls._REGISTRY.get(ext)
        if loader_cls is None:
            supported = ", ".join(cls._REGISTRY)
            raise ValueError(
                f"Unsupported extension '{ext}' for '{path.name}'. "
                f"Supported: {supported}"
            )
        return loader_cls(path)

    @classmethod
    def load(cls, file_path: str | Path) -> str:
        """Convenience one-liner: get loader and call load()."""
        return cls.get_loader(file_path).load()
