"""Extract plain text from uploaded resume files (PDF / DOCX / TXT)."""
import io


def extract_resume_text(filename: str, content: bytes, content_type: str = "") -> str:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()

    if name.endswith(".pdf") or "pdf" in ctype:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        except Exception:
            return ""

    if name.endswith(".docx") or "word" in ctype or "officedocument" in ctype:
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception:
            return ""

    try:
        return content.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
