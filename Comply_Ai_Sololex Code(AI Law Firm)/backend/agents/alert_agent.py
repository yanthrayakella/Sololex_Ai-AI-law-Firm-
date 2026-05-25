import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from db import Alert, Contract, Regulation, User
from services.email_notify import send_alert_email
from services.wechat_notify import fingerprint_openid_stub, send_template_message

from .analyzer_agent import regulation_already_processed_alert


def run_alerts(
    db: Session,
    regulation: Regulation,
    analyzed: list[tuple[Contract, list[dict]]],
) -> list[Alert]:
    if not regulation.parsed_json:
        return []
    meta: dict[str, Any] = json.loads(regulation.parsed_json)
    sev = str(meta.get("severity") or "MEDIUM")
    penalty = str(meta.get("penalty_amount") or "See regulation")
    action = "; ".join(str(a) for a in (meta.get("actions_required") or [])[:2])

    created: list[Alert] = []
    for contract, clauses in analyzed:
        bad = [c for c in clauses if c.get("status") in ("non_compliant", "review")]
        if not bad:
            continue
        if regulation_already_processed_alert(db, contract.id, regulation.id):
            continue

        first = bad[0]
        title = f"Regulatory change affects “{contract.name}”"
        message = (
            f"Regulation: {regulation.title}\n"
            f"Clause: {first.get('title')}\n"
            f"Status: {first.get('status')}\n"
            f"Action: {action}"
        )
        alert = Alert(
            id=str(uuid.uuid4()),
            user_id=contract.user_id,
            contract_id=contract.id,
            regulation_id=regulation.id,
            severity=sev,
            title=title,
            message=message,
            is_read=False,
        )
        db.add(alert)
        created.append(alert)

        user = db.query(User).filter(User.id == contract.user_id).first()
        if user:
            send_alert_email(
                to_email=user.email,
                regulation_title=regulation.title,
                contract_name=contract.name,
                clause_description=str(first.get("text", ""))[:500],
                penalty_amount=penalty,
                action_required=action,
            )
            openid = user.wechat_openid or fingerprint_openid_stub(user.email)
            send_template_message(
                openid=openid,
                regulation_title=regulation.title,
                contract_name=contract.name,
                severity=sev,
                action_required=action,
            )

    db.commit()
    for a in created:
        db.refresh(a)
    return created
