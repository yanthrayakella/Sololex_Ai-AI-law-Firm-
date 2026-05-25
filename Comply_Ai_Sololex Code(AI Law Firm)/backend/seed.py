import json
import uuid

from auth_utils import hash_password
from config import settings
from db import Alert, Contract, Regulation, SessionLocal, User, utcnow


def _write_upload(name: str, body: str) -> str:
    path = settings.UPLOADS_DIR / name
    path.write_text(body, encoding="utf-8")
    return str(path)


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(User).first():
            return

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email="demo@complyai.com",
            password_hash=hash_password("demo123"),
            name="Demo User",
            company="Demo Holdings",
            subscription_tier="pro",
            wechat_openid=None,
            created_at=utcnow(),
        )
        db.add(user)

        emp_path = _write_upload(
            "employment_demo.txt",
            "Employment Agreement\n\n"
            "The employer may terminate this contract at any time without notice or compensation. "
            "The employee waives all claims.",
        )
        sup_path = _write_upload(
            "supplier_demo.txt",
            "Supplier Agreement\n\n"
            "Supplier shall have zero liability for any indirect damages. "
            "Buyer indemnifies Supplier for all claims without limitation.",
        )
        lease_path = _write_upload(
            "lease_demo.txt",
            "Lease Agreement\n\nPayment terms: monthly rent due on the 1st. "
            "Either party may terminate with 60 days written notice per statutory requirements.",
        )

        employment_clauses = [
            {
                "id": str(uuid.uuid4()),
                "title": "Termination",
                "text": "The employer may terminate this contract at any time without notice or compensation.",
                "category": "termination",
                "status": "non_compliant",
                "regulation_ref": "Labor Contract Law — fairness of termination",
                "fine_amount": "Administrative fines; labor arbitration exposure",
                "suggested_fix": "Replace with mutual notice periods, statutory grounds, and severance rules.",
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Compensation",
                "text": "The employee waives all statutory compensation entitlements.",
                "category": "payment",
                "status": "review",
                "regulation_ref": "MOHRSS guidance on compensation",
                "fine_amount": "Back-pay and penalties",
                "suggested_fix": "Remove blanket waivers; align with mandatory labor standards.",
            },
        ]

        supplier_clauses = [
            {
                "id": str(uuid.uuid4()),
                "title": "Liability cap",
                "text": "Supplier shall have zero liability for any indirect damages.",
                "category": "liability",
                "status": "non_compliant",
                "regulation_ref": "Civil Code Article 506 — invalid exemption clauses",
                "fine_amount": "Contract invalidity risk; damages",
                "suggested_fix": "Cap liability proportionally; carve out fraud/wilful misconduct and mandatory law.",
            }
        ]

        lease_clauses = [
            {
                "id": str(uuid.uuid4()),
                "title": "Rent",
                "text": "Monthly rent payable on the 1st.",
                "category": "payment",
                "status": "compliant",
                "regulation_ref": None,
                "fine_amount": None,
                "suggested_fix": None,
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Termination notice",
                "text": "Either party may terminate with 60 days written notice per statutory requirements.",
                "category": "termination",
                "status": "compliant",
                "regulation_ref": None,
                "fine_amount": None,
                "suggested_fix": None,
            },
        ]

        c1 = Contract(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Employment Contract — Sales Lead",
            type="employment",
            file_path=emp_path,
            clauses_json=json.dumps(employment_clauses, ensure_ascii=False),
            risk_score=56,
            created_at=utcnow(),
        )
        c2 = Contract(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Supplier Master Agreement",
            type="supplier",
            file_path=sup_path,
            clauses_json=json.dumps(supplier_clauses, ensure_ascii=False),
            risk_score=62,
            created_at=utcnow(),
        )
        c3 = Contract(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Shanghai Office Lease",
            type="lease",
            file_path=lease_path,
            clauses_json=json.dumps(lease_clauses, ensure_ascii=False),
            risk_score=94,
            created_at=utcnow(),
        )
        db.add_all([c1, c2, c3])

        reg_pi = Regulation(
            id=str(uuid.uuid4()),
            title="PIPL Amendment — Cross-border personal information",
            source_url="https://www.cac.gov.cn/",
            publish_date="2025-11-01",
            full_text="Personal information processors must obtain informed consent and complete security assessment "
            "for cross-border transfers. Data privacy clauses must specify purpose, retention, and localization.",
            parsed_json=None,
            created_at=utcnow(),
        )
        reg_cc = Regulation(
            id=str(uuid.uuid4()),
            title="Civil Code Article 506 — Liability and indemnity",
            source_url="https://www.npc.gov.cn/",
            publish_date="2024-06-01",
            full_text="Article 506: Exemption clauses that exclude statutory liability for personal injury or "
            "property damage caused by intentional or gross negligence are void. Commercial contracts must keep "
            "liability and indemnity proportional.",
            parsed_json=None,
            created_at=utcnow(),
        )
        db.add_all([reg_pi, reg_cc])
        db.commit()
        db.refresh(reg_pi)
        db.refresh(reg_cc)

        from agents.parser_agent import parse_regulation

        for reg in (reg_pi, reg_cc):
            reg.parsed_json = json.dumps(parse_regulation(reg), ensure_ascii=False)
        db.commit()

        a1 = Alert(
            id=str(uuid.uuid4()),
            user_id=user_id,
            contract_id=c1.id,
            regulation_id=reg_pi.id,
            severity="HIGH",
            title="Data localization review suggested",
            message="New PIPL guidance may require updates to data clauses for employment records.",
            is_read=False,
            created_at=utcnow(),
        )
        a2 = Alert(
            id=str(uuid.uuid4()),
            user_id=user_id,
            contract_id=c2.id,
            regulation_id=reg_cc.id,
            severity="MEDIUM",
            title="Liability clause may run afoul of Civil Code Art. 506",
            message="Supplier agreement contains broad indemnity — align with Article 506 proportionality.",
            is_read=False,
            created_at=utcnow(),
        )
        db.add_all([a1, a2])
        db.commit()
    finally:
        db.close()
