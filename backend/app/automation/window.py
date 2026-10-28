from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


def berlin_local(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("Generation window checks require a timezone-aware datetime.")
    return moment.astimezone(BERLIN)


def in_generation_window(moment: datetime) -> bool:
    """True on calendar days 1, 2, and 3 in Europe/Berlin, including DST changes."""
    local = berlin_local(moment)
    return local.day in {1, 2, 3}


def window_report(moment: datetime | None = None) -> dict:
    moment = moment or datetime.now(timezone.utc)
    local = berlin_local(moment)
    return {
        "utc": moment.astimezone(timezone.utc).isoformat(),
        "europeBerlin": local.isoformat(),
        "berlinDay": local.day,
        "inWindow": local.day in {1, 2, 3},
        "operational": False,
        "reason": "The date rule is implemented and tested. Unattended generation is not operational: no provider credentials were configured and this process was not verified as a live scheduler.",
    }
