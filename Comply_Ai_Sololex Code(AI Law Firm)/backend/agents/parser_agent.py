import json
import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from db import Regulation


def _detect_contract_types(text: str) -> list[str]:
    t = text.lower()
    out: set[str] = set()
    if any(k in t for k in ["劳动", "雇佣", "employment", "employee", "labor", "mohrss"]):
        out.add("employment")
    if any(k in t for k in ["供应", "采购", "supplier", "vendor", "commercial", "samr"]):
        out.add("supplier")
    if any(k in t for k in ["租赁", "lease", "tenant"]):
        out.add("lease")
    if any(k in t for k in ["服务", "service agreement", "saas"]):
        out.add("service")
    if not out:
        out.update(["employment", "supplier", "lease", "service"])
    return sorted(out)


def _detect_clauses(text: str) -> list[str]:
    tags: set[str] = set()
    pairs = [
        (r"终止|解除|termination", "termination"),
        (r"责任|赔偿|赔偿|liability|indemn", "liability"),
        (r"数据|个人信息|隐私|privacy|pipl|跨境", "data privacy"),
        (r"付款|支付|payment|价款", "payment"),
    ]
    for pat, name in pairs:
        if re.search(pat, text, re.I):
            tags.add(name)
    if not tags:
        tags.add("general")
    return sorted(tags)


def _severity(text: str) -> str:
    if re.search(r"罚|刑事|没收|严重", text):
        return "HIGH"
    if re.search(r"应当|必须|不得", text):
        return "MEDIUM"
    return "LOW"


def _penalty(text: str) -> str:
    m = re.search(r"(?:罚款|罚金|人民币|¥)\s*([0-9,.万]+)", text)
    if m:
        return m.group(0)[:120]
    m = re.search(r"illegal gains|fine up to", text, re.I)
    if m:
        return "Fines referenced in text — verify with counsel"
    return "See regulation text / enforcement guidance"


def _actions(clauses: list[str]) -> list[str]:
    actions = []
    if "data privacy" in clauses:
        actions.append("Add or modify data processing clauses; obtain consents for cross-border transfers.")
    if "liability" in clauses:
        actions.append("Revise liability caps and indemnities for Civil Code compatibility.")
    if "termination" in clauses:
        actions.append("Align termination rights with statutory fairness and notice requirements.")
    if not actions:
        actions.append("Review contract against new regulatory text and update affected clauses.")
    return actions


def parse_regulation(reg: Regulation) -> dict[str, Any]:
    text = reg.full_text or ""
    clause_tags = _detect_clauses(text)
    parsed = {
        "id": str(uuid.uuid4()),
        "regulation_id": reg.id,
        "title": reg.title,
        "contract_types_affected": _detect_contract_types(text),
        "clauses_affected": clause_tags,
        "actions_required": _actions(clause_tags),
        "severity": _severity(text),
        "penalty_amount": _penalty(text),
        "summary": text[:800],
    }
    return parsed


def run_parser(db: Session, regulations: list[Regulation] | None = None) -> list[Regulation]:
    if regulations:
        to_parse = [r for r in regulations if not r.parsed_json]
    else:
        to_parse = db.query(Regulation).filter(Regulation.parsed_json.is_(None)).all()
    updated: list[Regulation] = []
    for reg in to_parse:
        parsed = parse_regulation(reg)
        reg.parsed_json = json.dumps(parsed, ensure_ascii=False)
        updated.append(reg)
    db.commit()
    return updated
