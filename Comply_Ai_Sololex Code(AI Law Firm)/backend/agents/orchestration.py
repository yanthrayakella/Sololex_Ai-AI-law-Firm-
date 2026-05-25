import logging

from sqlalchemy.orm import Session

from agents.alert_agent import run_alerts
from agents.analyzer_agent import analyze_contracts_for_regulation
from agents.parser_agent import run_parser
from agents.scraper import run_scraper
from db import SessionLocal

logger = logging.getLogger(__name__)


def run_all_agents() -> None:
    db: Session = SessionLocal()
    try:
        new_regs = run_scraper(db)
        to_parse = new_regs if new_regs else None
        parsed = run_parser(db, to_parse)
        if not parsed and not new_regs:
            parsed = run_parser(db, None)
        logger.info("Agents cycle: new_regs=%s parsed=%s", len(new_regs), len(parsed))
        for reg in parsed:
            touched = analyze_contracts_for_regulation(db, reg)
            run_alerts(db, reg, touched)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent pipeline failed: %s", exc)
    finally:
        db.close()
