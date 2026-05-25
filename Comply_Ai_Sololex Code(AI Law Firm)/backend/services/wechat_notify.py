import hashlib
import logging
import time
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def _get_access_token() -> Optional[str]:
    if not settings.wechat_app_id or not settings.wechat_app_secret:
        return None
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return str(_token_cache["access_token"])
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": settings.wechat_app_id,
        "secret": settings.wechat_app_secret,
    }
    try:
        r = httpx.get(url, params=params, timeout=15.0)
        data = r.json()
        token = data.get("access_token")
        expires = int(data.get("expires_in", 7200))
        if token:
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = now + expires - 60
            return str(token)
    except Exception as exc:  # noqa: BLE001
        logger.warning("WeChat token error: %s", exc)
    return None


def send_template_message(
    openid: str,
    regulation_title: str,
    contract_name: str,
    severity: str,
    action_required: str,
) -> None:
    link = f"{settings.dashboard_base_url}/dashboard"
    text_body = (
        "⚠ CONTRACT ALERT\n"
        f"Regulation: {regulation_title}\n"
        f"Affected Contract: {contract_name}\n"
        f"Severity: {severity}\n"
        f"Action Required: {action_required}\n"
        f"View in dashboard: {link}\n"
    )
    token = _get_access_token()
    if not token:
        logger.info("WeChat not configured or token failed; message for %s:\n%s", openid, text_body)
        return

    payload = {
        "touser": openid,
        "template_id": settings.wechat_template_id or "TEMPLATE_ID",
        "url": link,
        "data": {
            "thing1": {"value": regulation_title[:20]},
            "thing2": {"value": contract_name[:20]},
            "thing3": {"value": severity[:10]},
            "thing4": {"value": action_required[:30]},
        },
    }
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    try:
        r = httpx.post(url, json=payload, timeout=15.0)
        logger.info("WeChat API response: %s %s", r.status_code, r.text[:200])
    except Exception as exc:  # noqa: BLE001
        logger.warning("WeChat send failed: %s", exc)


def fingerprint_openid_stub(email: str) -> str:
    """Deterministic fake openid for demos when WeChat is not linked."""
    return hashlib.sha256(f"wechat-stub:{email}".encode()).hexdigest()[:28]
