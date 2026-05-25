import uuid
from typing import Any, Optional

from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from config import settings
from db import Contract, UpdatedContract, User, clauses_json_dump, clauses_json_load
from services.document_parser import risk_score_from_clauses


def _build_compliant_text(original: str, suggested: str) -> str:
    base = suggested.strip() or (
        "The parties agree to amend this clause to conform with applicable PRC law, "
        "including fair termination notice, liability proportionality, and data processing consent as required."
    )
    return f"{base}\n\n[Replaces prior wording materially summarized as: {original[:200]}…]"


def generate_updated_files(
    db: Session,
    user: User,
    contract: Contract,
    clause_id: str,
    apply_automatic: bool,
) -> tuple[UpdatedContract, str, str]:
    clauses = clauses_json_load(contract.clauses_json)
    target: Optional[dict[str, Any]] = None
    for cl in clauses:
        if cl.get("id") == clause_id:
            target = cl
            break
    if not target:
        raise ValueError("Clause not found")

    original = str(target.get("text") or "")
    suggested = str(target.get("suggested_fix") or "")
    compliant = _build_compliant_text(original, suggested)

    tier = user.subscription_tier or "basic"
    if apply_automatic and tier != "pro":
        raise ValueError("Automatic apply requires Pro subscription")

    if not apply_automatic:
        summary = f"Guidance for clause '{target.get('title')}' — {suggested}"
        doc_text = (
            "ComplyAI — Remediation guidance\n\n"
            f"Contract: {contract.name}\n"
            f"Clause: {target.get('title')}\n\n"
            "Original:\n"
            f"{original[:2000]}\n\n"
            "Suggested compliant wording:\n"
            f"{compliant}\n"
        )
    else:
        summary = f"Applied compliant rewrite for clause '{target.get('title')}'."
        doc_text = f"FULL UPDATED CONTRACT (DRAFT)\n{contract.name}\n\n"
        for cl in clauses:
            body = compliant if cl.get("id") == clause_id else str(cl.get("text") or "")
            doc_text += f"\n## {cl.get('title')}\n{body}\n"

    uid = str(uuid.uuid4())
    out_docx = settings.OUTPUTS_DIR / f"{uid}.docx"
    out_pdf = settings.OUTPUTS_DIR / f"{uid}.pdf"

    doc = Document()
    for line in doc_text.split("\n"):
        doc.add_paragraph(line)
    doc.save(str(out_docx))

    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    width, height = letter
    y = height - 50
    for line in doc_text.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line[:120])
        y -= 14
    c.save()

    row = UpdatedContract(
        id=str(uuid.uuid4()),
        user_id=user.id,
        original_contract_id=contract.id,
        updated_file_path=str(out_docx),
        changes_summary=summary,
        subscription_tier=tier,
    )
    db.add(row)

    if apply_automatic:
        for cl in clauses:
            if cl.get("id") == clause_id:
                cl["text"] = compliant
                cl["status"] = "compliant"
                cl["regulation_ref"] = None
                cl["fine_amount"] = None
        contract.clauses_json = clauses_json_dump(clauses)
        contract.risk_score = risk_score_from_clauses(clauses)

    db.commit()
    db.refresh(row)
    return row, str(out_docx), str(out_pdf)
