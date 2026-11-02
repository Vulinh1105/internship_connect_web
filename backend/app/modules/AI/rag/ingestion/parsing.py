"""
doc_processing.parsing
=======================
Module T07 (PDF Parser) + T08 (DOCX/TXT Parser) Gá»˜P CHUNG thÃ nh 1 file, 1
entrypoint duy nháº¥t: `parse_document()`. LÃ½ do gá»™p: pipeline.py/ingestion.py
chá»‰ cáº§n gá»i 1 hÃ m, khÃ´ng pháº£i if/else theo loáº¡i file á»Ÿ táº§ng trÃªn -> giáº£m
Ä‘iá»ƒm cÃ³ thá»ƒ phÃ¡t sinh lá»—i khi cÃ¡c nhÃ³m khÃ¡c (G3, G4) tÃ­ch há»£p vÃ o.

TÃ­ch há»£p vá»›i pháº§n code Ä‘Ã£ cÃ³ sáºµn (G4 - app/services/document_service.py):
    File váº­t lÃ½ lÆ°u trÃªn Ä‘Ä©a Ä‘Æ°á»£c Ä‘áº·t tÃªn theo `str(document.id)` vÃ  KHÃ”NG
    cÃ³ pháº§n má»Ÿ rá»™ng (xem DocumentService.create_document). VÃ¬ váº­y loáº¡i file
    PHáº¢I Ä‘Æ°á»£c xÃ¡c Ä‘á»‹nh qua `Document.original_filename` (tÃªn lÃºc upload),
    KHÃ”NG Ä‘Æ°á»£c xÃ¡c Ä‘á»‹nh qua Ä‘uÃ´i cá»§a file váº­t lÃ½ trÃªn Ä‘Ä©a.

Input : Ä‘Æ°á»ng dáº«n file trÃªn Ä‘Ä©a + tÃªn file gá»‘c lÃºc upload + document_id.
Output: list "parsed block" - input trá»±c tiáº¿p cho chunking.py:
    {"document_id": int, "page": int, "text": str}

CÃ i Ä‘áº·t: pip install pymupdf python-docx (Ä‘Ã£ cÃ³ trong
app/doc_processing/requirements.txt).
"""

from __future__ import annotations

import logging
import sys
import unicodedata
from pathlib import Path
from typing import Protocol

# ThÃªm thÆ° má»¥c `backend` vÃ o sys.path khi cháº¡y script trá»±c tiáº¿p (python backend/app/doc_processing/parsing.py)
import pymupdf as fitz  # PyMuPDF - "import fitz" kiá»ƒu cÅ© Ä‘Ã£ deprecated
from docx import Document as DocxDocument
from docx.opc.exceptions import PackageNotFoundError

logger = logging.getLogger(__name__)


class DocumentLike(Protocol):
    id: int
    file_path: str
    original_filename: str


# ---------------------------------------------------------------------------
# Cáº¥u hÃ¬nh dÃ¹ng chung toÃ n há»‡ thá»‘ng
# ---------------------------------------------------------------------------

# 3 Ä‘á»‹nh dáº¡ng MVP há»— trá»£ theo Kick-off Guide & SRS (PDF/DOCX/TXT).
# ÄÃ‚Y LÃ€ "single source of truth" cho toÃ n bá»™ backend: ingestion.py vÃ 
# endpoint upload (app/api/v1/endpoints/document.py) Ä‘á»u import biáº¿n nÃ y
# thay vÃ¬ tá»± khai bÃ¡o láº¡i danh sÃ¡ch Ä‘uÃ´i file - trÃ¡nh tÃ¬nh tráº¡ng lá»‡ch nhau
# (vÃ­ dá»¥: endpoint cho phÃ©p .csv nhÆ°ng parser chÆ°a há»— trá»£ -> lá»—i runtime khi
# indexing, chá»‰ phÃ¡t hiá»‡n ra sau khi user Ä‘Ã£ upload xong).
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt"})


class ParsingError(Exception):
    """Lá»—i phÃ¡t sinh khi trÃ­ch xuáº¥t text tá»« file (file há»ng, corrupt, thÆ° viá»‡n lá»—i...)."""


class UnsupportedFileTypeError(ParsingError):
    """Raised khi original_filename cÃ³ Ä‘uÃ´i mÃ  parser chÆ°a há»— trá»£."""


# ---------------------------------------------------------------------------
# Tiá»‡n Ã­ch ná»™i bá»™
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Chuáº©n hoÃ¡ text thÃ´ trÆ°á»›c khi Ä‘Æ°a sang chunking.py:
    - Chuáº©n hoÃ¡ Unicode NFC (trÃ¡nh kÃ½ tá»± tiáº¿ng Viá»‡t tá»• há»£p bá»‹ tÃ¡ch thÃ nh
      nhiá»u code point, lÃ m sai Ä‘á»™ dÃ i chunk á»Ÿ bÆ°á»›c sau).
    - ÄÆ°a CRLF/CR vá» LF, gá»™p nhiá»u dÃ²ng trá»‘ng liÃªn tiáº¿p thÃ nh tá»‘i Ä‘a 1 dÃ²ng.
    - Trim khoáº£ng tráº¯ng Ä‘áº§u/cuá»‘i.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [line.rstrip() for line in text.split("\n")]
    cleaned_lines: list[str] = []
    blank_streak = 0
    for line in lines:
        if line == "":
            blank_streak += 1
            if blank_streak > 1:
                continue
        else:
            blank_streak = 0
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _parse_pdf(file_path: Path, document_id: int) -> list[dict]:
    """T07 - PDF Parser: trÃ­ch text theo tá»«ng trang, GIá»® sá»‘ trang (page) lÃ m
    evidence hiá»ƒn thá»‹ citation (North Star trong Kick-off Guide: "KhÃ´ng cÃ³
    evidence phÃ¹ há»£p -> khÃ´ng bá»‹a cÃ¢u tráº£ lá»i")."""
    try:
        doc = fitz.open(file_path)
    except Exception as exc:  # PyMuPDF nÃ©m nhiá»u loáº¡i lá»—i khÃ¡c nhau khi file há»ng
        raise ParsingError(f"KhÃ´ng thá»ƒ má»Ÿ file PDF '{file_path.name}': {exc}") from exc

    blocks: list[dict] = []
    try:
        for page_number in range(1, doc.page_count + 1):
            page = doc.load_page(page_number - 1)
            text = _clean_text(page.get_text("text"))
            if not text:
                # Trang trá»‘ng hoáº·c trang scan (áº£nh) khÃ´ng cÃ³ text layer.
                # KHÃ”NG raise lá»—i á»Ÿ Ä‘Ã¢y vÃ¬ cÃ¡c trang khÃ¡c trong cÃ¹ng file váº«n
                # cÃ³ thá»ƒ há»£p lá»‡ - chá»‰ log cáº£nh bÃ¡o Ä‘á»ƒ G1 (evaluation) biáº¿t
                # tÃ i liá»‡u nÃ y cÃ³ thá»ƒ cáº§n OCR sau nÃ y (ngoÃ i pháº¡m vi MVP).
                logger.warning(
                    "PDF '%s' trang %s khÃ´ng trÃ­ch Ä‘Æ°á»£c text (cÃ³ thá»ƒ lÃ  trang scan/áº£nh).",
                    file_path.name, page_number,
                )
                continue
            blocks.append({
                "document_id": document_id,
                "page": page_number,
                "text": text,
            })
    finally:
        doc.close()
    return blocks


def _parse_docx(file_path: Path, document_id: int, group_size: int = 10) -> list[dict]:
    """T08 - DOCX Parser: python-docx khÃ´ng cÃ³ khÃ¡i niá»‡m 'trang' (trang phá»¥
    thuá»™c engine render cá»§a Word, khÃ´ng tá»“n táº¡i trong file .docx), nÃªn gá»™p
    má»—i `group_size` Ä‘oáº¡n vÄƒn thÃ nh 1 "pseudo-page" Ä‘á»ƒ field 'page' luÃ´n
    Ä‘á»“ng nháº¥t vá»›i PDF/TXT á»Ÿ táº§ng chunking/citation phÃ­a sau."""
    if group_size <= 0:
        raise ValueError("group_size pháº£i lá»›n hÆ¡n 0 Ä‘á»ƒ chia vÄƒn báº£n DOCX thÃ nh cÃ¡c pseudo-page há»£p lá»‡.")

    try:
        docx_doc = DocxDocument(str(file_path))
    except PackageNotFoundError as exc:
        raise ParsingError(f"File DOCX '{file_path.name}' bá»‹ há»ng hoáº·c sai Ä‘á»‹nh dáº¡ng: {exc}") from exc
    except Exception as exc:
        raise ParsingError(f"KhÃ´ng thá»ƒ Ä‘á»c file DOCX '{file_path.name}': {exc}") from exc

    paragraphs = [p.text for p in docx_doc.paragraphs if p.text.strip()]

    blocks: list[dict] = []
    for i in range(0, len(paragraphs), group_size):
        group_text = _clean_text("\n".join(paragraphs[i:i + group_size]))
        if not group_text:
            continue
        blocks.append({
            "document_id": document_id,
            "page": i // group_size + 1,
            "text": group_text,
        })
    return blocks


def _parse_txt(file_path: Path, document_id: int) -> list[dict]:
    """T08 - TXT Parser: Ä‘á»c toÃ n bá»™ file. Thá»­ UTF-8 trÆ°á»›c, náº¿u lá»—i encoding
    thÃ¬ fallback sang latin-1 (errors="ignore") Ä‘á»ƒ 1 file lá»—i encoding khÃ´ng
    lÃ m crash toÃ n bá»™ pipeline khi xá»­ lÃ½ hÃ ng loáº¡t tÃ i liá»‡u."""
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("File TXT '%s' khÃ´ng pháº£i UTF-8, fallback sang latin-1.", file_path.name)
        raw_text = file_path.read_text(encoding="latin-1", errors="ignore")

    text = _clean_text(raw_text)
    if not text:
        return []
    return [{
        "document_id": document_id,
        "page": 1,
        "text": text,
    }]


# Báº£ng dispatch: má»—i Ä‘uÃ´i file á»©ng vá»›i 1 parser cá»¥ thá»ƒ, nhÆ°ng ngÆ°á»i gá»i bÃªn
# ngoÃ i (ingestion.py, pipeline.py) KHÃ”NG cáº§n biáº¿t báº£ng nÃ y tá»“n táº¡i - chá»‰
# cáº§n gá»i duy nháº¥t parse_document().
_PARSERS = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".txt": _parse_txt,
}


# ---------------------------------------------------------------------------
# Entrypoint DUY NHáº¤T - nÆ¡i "gá»™p 2 kiá»ƒu parsing lÃ m 1"
# ---------------------------------------------------------------------------

def parse_document(file_path: Path | str, original_filename: str, document_id: int) -> list[dict]:
    """
    Entrypoint chÃ­nh - dÃ¹ng chung cho cáº£ PDF láº«n DOCX/TXT (T07 + T08 gá»™p
    thÃ nh 1 hÃ m). ÄÃ¢y lÃ  hÃ m DUY NHáº¤T mÃ  ingestion.py/pipeline.py cáº§n gá»i.

    Args:
        file_path: Ä‘Æ°á»ng dáº«n file tháº­t trÃªn Ä‘Ä©a (Document.file_path - KHÃ”NG
            cÃ³ Ä‘uÃ´i má»Ÿ rá»™ng, xem lÆ°u Ã½ á»Ÿ Ä‘áº§u file).
        original_filename: tÃªn file gá»‘c lÃºc upload (Document.original_filename)
            - dÃ¹ng Ä‘á»ƒ xÃ¡c Ä‘á»‹nh loáº¡i file cáº§n parser nÃ o.
        document_id: Document.id trong DB, gáº¯n vÃ o tá»«ng block Ä‘á»ƒ chunking.py
            vÃ  bÆ°á»›c index sau nÃ y biáº¿t chunk thuá»™c tÃ i liá»‡u nÃ o.

    Returns:
        list[dict]: danh sÃ¡ch "parsed block" {document_id, page, text}.

    Raises:
        FileNotFoundError: file váº­t lÃ½ khÃ´ng tá»“n táº¡i trÃªn Ä‘Ä©a.
        UnsupportedFileTypeError: Ä‘uÃ´i file khÃ´ng náº±m trong SUPPORTED_EXTENSIONS.
        ParsingError: file tá»“n táº¡i, Ä‘Ãºng Ä‘á»‹nh dáº¡ng nhÆ°ng bá»‹ há»ng/khÃ´ng Ä‘á»c Ä‘Æ°á»£c.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"KhÃ´ng tÃ¬m tháº¥y file váº­t lÃ½ cho document_id={document_id}: '{path}'. "
            f"CÃ³ thá»ƒ file Ä‘Ã£ bá»‹ xoÃ¡ khá»i storage hoáº·c DocumentService chÆ°a ghi xong."
        )

    ext = ""
    for candidate in (original_filename, file_path):
        candidate_str = str(candidate).strip()
        if not candidate_str:
            continue
        suffix = Path(candidate_str).suffix.lower()
        if suffix:
            ext = suffix
            break

    parser = _PARSERS.get(ext)
    if parser is None:
        raise UnsupportedFileTypeError(
            f"parsing.py chÆ°a há»— trá»£ Ä‘uÃ´i file: {ext!r} (original_filename={original_filename!r}). "
            f"ÄÃ£ há»— trá»£: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    logger.info("Báº¯t Ä‘áº§u parse document_id=%s (%s)", document_id, original_filename)
    blocks = parser(path, document_id)
    logger.info("Parse xong document_id=%s: %s block.", document_id, len(blocks))
    return blocks


def parse_document_model(document: DocumentLike) -> list[dict]:
    """Tiá»‡n Ã­ch: parse trá»±c tiáº¿p tá»« 1 ORM `Document` object (láº¥y tá»« DB qua
    DocumentRepository cá»§a G4) thay vÃ¬ pháº£i truyá»n tay 3 field riÃªng láº».
    DÃ¹ng trong ingestion.py khi Ä‘Ã£ query Ä‘Æ°á»£c document."""
    return parse_document(document.file_path, document.original_filename, document.id)


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(level=logging.INFO)
    print(
        "parsing.py khÃ´ng cÃ³ file demo máº·c Ä‘á»‹nh. "
        "HÃ£y gá»i parse_document() vá»›i Ä‘Æ°á»ng dáº«n file tháº­t, "
        "hoáº·c cháº¡y pipeline/test code/test_ingestion.py Ä‘á»ƒ test tÃ i liá»‡u trong storage."
    )
