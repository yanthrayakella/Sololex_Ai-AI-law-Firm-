import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from config import settings
from db import Regulation, ScraperSnapshot, utcnow

logger = logging.getLogger(__name__)

SOURCES = [
    ("https://www.npc.gov.cn", "npc", "NPC — laws"),
    ("https://www.gov.cn", "gov.cn", "State Council — regulations"),
    ("https://www.cac.gov.cn", "cac", "CAC — privacy / PIPL"),
    ("http://www.mohrss.gov.cn", "mohrss", "MOHRSS — labor"),
    ("https://www.court.gov.cn", "court", "Court interpretations"),
    ("https://www.samr.gov.cn", "samr", "SAMR — commercial"),
]


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def fetch_page(url: str, timeout: float = 20.0) -> Optional[tuple[str, str]]:
    try:
        headers = {
            "User-Agent": "ComplyAI-Bot/1.0 (+https://github.com/complyai)",
            "Accept": "text/html,application/xhtml+xml",
        }
        r = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        title_el = soup.find("title")
        title = title_el.get_text(strip=True) if title_el else url
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)[:200_000]
        return title[:500], text
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scraper fetch failed %s: %s", url, exc)
        return None


def run_scraper(db: Session) -> list[Regulation]:
    new_regs: list[Regulation] = []
    for url, slug, label in SOURCES:
        snap = db.query(ScraperSnapshot).filter(ScraperSnapshot.source_url == url).first()
        fetched = fetch_page(url)
        if not fetched:
            if settings.scraper_use_mock_fallback:
                title, body = _mock_snapshot(url, label)
                content_hash = _hash_content(body)
                if snap and snap.content_hash == content_hash:
                    continue
                if snap:
                    snap.content_hash = content_hash
                    snap.last_title = title
                    snap.updated_at = utcnow()
                else:
                    db.add(
                        ScraperSnapshot(
                            source_url=url,
                            content_hash=content_hash,
                            last_title=title,
                            updated_at=utcnow(),
                        )
                    )
                reg = Regulation(
                    id=str(uuid.uuid4()),
                    title=f"[Monitor] {label} — snapshot update",
                    source_url=url,
                    publish_date=datetime.now(timezone.utc).date().isoformat(),
                    full_text=body[:50_000],
                    parsed_json=None,
                )
                db.add(reg)
                new_regs.append(reg)
            continue

        title, body = fetched
        content_hash = _hash_content(title + body[:5000])
        if snap and snap.content_hash == content_hash:
            continue

        if snap:
            snap.content_hash = content_hash
            snap.last_title = title
            snap.updated_at = utcnow()
        else:
            db.add(
                ScraperSnapshot(
                    source_url=url,
                    content_hash=content_hash,
                    last_title=title,
                    updated_at=utcnow(),
                )
            )

        reg = Regulation(
            id=str(uuid.uuid4()),
            title=f"{title}"[:500] or label,
            source_url=url,
            publish_date=datetime.now(timezone.utc).date().isoformat(),
            full_text=body[:50_000],
            parsed_json=None,
        )
        db.add(reg)
        new_regs.append(reg)

    db.commit()
    for r in new_regs:
        db.refresh(r)
    return new_regs


def _mock_snapshot(url: str, label: str) -> tuple[str, str]:
    day = datetime.now(timezone.utc).date().isoformat()
    body = (
        f"Compliance monitoring snapshot for {label}.\n"
        f"Source: {url}\n"
        f"Date: {day}\n"
        "Organizations should review employment termination fairness, cross-border "
        "personal information processing under PIPL, and liability limitation clauses "
        "under Civil Code Article 506.\n"
    )
    return f"{label} — connectivity placeholder", body
