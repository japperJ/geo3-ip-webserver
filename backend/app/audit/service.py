import csv
import io
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from app.db.models.audit import AccessDecision


@dataclass(frozen=True)
class AuditEvent:
    timestamp: datetime
    site_id: str
    client_ip: str | None
    ip_geo_country: str | None
    decision: AccessDecision
    reason: str | None
    artifact_path: str | None


MAX_EVENTS = 1000
_EVENTS: deque[AuditEvent] = deque(maxlen=MAX_EVENTS)
_LOCK = Lock()


def clear() -> None:
    with _LOCK:
        _EVENTS.clear()


def log_block(
    *,
    site_id: str,
    client_ip: str | None = None,
    ip_geo_country: str | None = None,
    reason: str | None = None,
    artifact_path: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        timestamp=datetime.now(timezone.utc),
        site_id=site_id,
        client_ip=client_ip,
        ip_geo_country=ip_geo_country,
        decision=AccessDecision.BLOCKED,
        reason=reason,
        artifact_path=artifact_path,
    )
    with _LOCK:
        _EVENTS.append(event)
    return event


def export_csv() -> str:
    with _LOCK:
        events = list(_EVENTS)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "timestamp",
            "site_id",
            "client_ip",
            "ip_geo_country",
            "decision",
            "reason",
            "artifact_path",
        ]
    )
    for event in events:
        writer.writerow(
            [
                event.timestamp.isoformat(),
                event.site_id,
                event.client_ip or "",
                event.ip_geo_country or "",
                event.decision.value,
                event.reason or "",
                event.artifact_path or "",
            ]
        )
    return output.getvalue()
