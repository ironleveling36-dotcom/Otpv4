"""
checkers.py — Swiggy Checker integration.

Calls the OTPCart Swiggy checker API to determine whether a mobile number is
already registered on Swiggy.

API:
    POST https://checker.otpcart.xyz/api/check-swiggy
    body: {"mobile": "XXXXXXXXXX"}   (10-digit local number, no country code)
    resp: {"status": "registered" | "unregistered", "mobile": "XXXXXXXXXX"}
"""

from __future__ import annotations

import logging
import httpx

from config import CHECKER_API_URL

logger = logging.getLogger(__name__)


def _local_number(phone: str) -> str:
    """Strip country code / non-digits → return the last 10 digits."""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


async def check_swiggy(phone: str) -> str:
    """
    Returns one of: "registered", "unregistered", "unknown".
    Never raises — on any error returns "unknown" so callers can decide safely.
    """
    mobile = _local_number(phone)
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                CHECKER_API_URL,
                json={"mobile": mobile},
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
        status = str(data.get("status", "")).strip().lower()
        if status in ("registered", "unregistered"):
            logger.info("Swiggy check %s -> %s", mobile, status)
            return status
        logger.warning("Swiggy check %s -> unexpected payload: %s", mobile, data)
        return "unknown"
    except Exception as e:
        logger.error("Swiggy check failed for %s: %s", mobile, e)
        return "unknown"


async def is_swiggy_unregistered(phone: str) -> bool:
    """Convenience wrapper — True only if the API explicitly says 'unregistered'."""
    return (await check_swiggy(phone)) == "unregistered"


async def is_myntra_unregistered(phone: str) -> bool:
    raise NotImplementedError("Myntra Checker is not available.")
