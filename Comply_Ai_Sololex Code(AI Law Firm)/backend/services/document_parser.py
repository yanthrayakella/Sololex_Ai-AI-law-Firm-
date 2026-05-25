import re
import uuid
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from db import clauses_json_dump


def read_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            parts.append(t)
        return "\n".join(parts)
    if suffix == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_to_clauses(full_text: str, contract_type: str) -> list[dict]:
    """Split contract text into pseudo-clauses with heuristic risk labels."""
    cleaned = re.sub(r"\s+", " ", full_text).strip()
    if not cleaned:
        return []

    chunks = re.split(r"(?<=[。；\n])\s*|(?<=\.)\s+", full_text)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 40][:40]
    if not chunks:
        step = max(len(cleaned) // 8, 200)
        chunks = [cleaned[i : i + step] for i in range(0, len(cleaned), step)][:12]

    clauses: list[dict] = []
    categories = ["termination", "liability", "data privacy", "payment", "general"]
    risk_patterns = [
        (r"无条件|无责|不承担|免除.*责任", "non_compliant", "Civil Code / liability caps"),
        (r"随时终止|立即解除|无需赔偿", "review", "Termination fairness review"),
        (r"数据|个人信息|出境|跨境", "review", "PIPL data processing"),
    ]

    for i, text in enumerate(chunks):
        status = "compliant"
        regulation_ref = None
        fine_amount = None
        suggested_fix = None
        category = categories[i % len(categories)]

        lower = text.lower()
        for pat, st, ref in risk_patterns:
            if re.search(pat, text, re.I):
                status = st
                regulation_ref = ref
                if status == "non_compliant":
                    fine_amount = "Up to 5x illegal gains (subject to enforcement)"
                    suggested_fix = (
                        "Limit unilateral termination; add mutual notice period and "
                        "statutory liability carve-outs per Civil Code."
                    )
                else:
                    suggested_fix = "Add explicit consent and purpose limitation clauses for PIPL processing."
                break

        if contract_type == "lease" and status != "compliant":
            status = "compliant"
            regulation_ref = None
            fine_amount = None
            suggested_fix = None

        clauses.append(
            {
                "id": str(uuid.uuid4()),
                "title": f"Clause {i + 1}",
                "text": text[:2000],
                "category": category,
                "status": status,
                "regulation_ref": regulation_ref,
                "fine_amount": fine_amount,
                "suggested_fix": suggested_fix,
            }
        )

    return clauses


def risk_score_from_clauses(clauses: list[dict]) -> int:
    if not clauses:
        return 100
    bad = sum(1 for c in clauses if c.get("status") == "non_compliant")
    review = sum(1 for c in clauses if c.get("status") == "review")
    deduct = bad * 22 + review * 9
    return max(0, 100 - min(100, deduct))


def build_clauses_for_upload(file_path: Path, contract_type: str) -> tuple[str, int]:
    text = read_text_from_file(file_path)
    clauses = chunk_to_clauses(text, contract_type)
    return clauses_json_dump(clauses), risk_score_from_clauses(clauses)
