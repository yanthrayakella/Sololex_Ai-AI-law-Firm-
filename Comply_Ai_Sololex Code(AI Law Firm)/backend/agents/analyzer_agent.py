import json
from typing import Any

from sqlalchemy.orm import Session

from db import Contract, Regulation, clauses_json_dump, clauses_json_load
from services.document_parser import risk_score_from_clauses


def _category_matches(clause_cat: str, reg_tags: list[str]) -> bool:
    m = {
        "termination": "termination",
        "liability": "liability",
        "data privacy": "data privacy",
        "payment": "payment",
        "general": "general",
    }
    tag = m.get(clause_cat.lower(), "general")
    return tag in reg_tags or "general" in reg_tags


def analyze_contracts_for_regulation(db: Session, regulation: Regulation) -> list[tuple[Contract, list[dict]]]:
    if not regulation.parsed_json:
        return []
    meta: dict[str, Any] = json.loads(regulation.parsed_json)
    types_ok = set(meta.get("contract_types_affected") or [])
    clauses_tags = list(meta.get("clauses_affected") or [])
    sev: str = str(meta.get("severity") or "MEDIUM")
    penalty = str(meta.get("penalty_amount") or "")
    actions = meta.get("actions_required") or ["Review and update clauses"]

    contracts = db.query(Contract).all()
    touched: list[tuple[Contract, list[dict]]] = []
    for c in contracts:
        if types_ok and c.type not in types_ok:
            continue
        clauses = clauses_json_load(c.clauses_json)
        changed = False
        for cl in clauses:
            if not _category_matches(cl.get("category") or "general", clauses_tags):
                continue
            if cl.get("status") == "compliant":
                if sev in ("HIGH", "MEDIUM"):
                    cl["status"] = "review"
                else:
                    cl["status"] = "review"
                cl["regulation_ref"] = regulation.title
                cl["fine_amount"] = penalty
                cl["suggested_fix"] = "; ".join(str(a) for a in actions[:2])
                changed = True
            elif cl.get("status") == "review":
                cl["status"] = "non_compliant"
                cl["regulation_ref"] = regulation.title
                cl["fine_amount"] = penalty
                cl["suggested_fix"] = "; ".join(str(a) for a in actions[:2])
                changed = True
            elif cl.get("status") == "non_compliant":
                cl["regulation_ref"] = f"{cl.get('regulation_ref') or ''}; {regulation.title}".strip("; ")
                changed = True
        if changed:
            c.clauses_json = clauses_json_dump(clauses)
            c.risk_score = risk_score_from_clauses(clauses)
            touched.append((c, clauses))
    db.commit()
    return touched


def run_analyzer(db: Session, regulations: list[Regulation]) -> list[tuple[Contract, list[dict]]]:
    results: list[tuple[Contract, list[dict]]] = []
    for reg in regulations:
        if not reg.parsed_json:
            continue
        results.extend(analyze_contracts_for_regulation(db, reg))
    return results


def regulation_already_processed_alert(db: Session, contract_id: str, regulation_id: str) -> bool:
    from db import Alert

    return (
        db.query(Alert)
        .filter(Alert.contract_id == contract_id, Alert.regulation_id == regulation_id)
        .first()
        is not None
    )
