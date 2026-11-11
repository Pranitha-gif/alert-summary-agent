"""Load and normalize alerts from JSON or CSV files."""
import csv
import json
from pathlib import Path

from .models import SEVERITY_ORDER, Alert

REQUIRED = ("alert_id", "source", "service", "severity", "message", "timestamp")


def _normalize(raw: dict) -> Alert | None:
    if any(not str(raw.get(k, "")).strip() for k in REQUIRED):
        return None  # skip malformed rows
    sev = str(raw["severity"]).strip().lower()
    if sev not in SEVERITY_ORDER:
        sev = "info"
    return Alert(
        alert_id=str(raw["alert_id"]).strip(),
        source=str(raw["source"]).strip(),
        service=str(raw["service"]).strip(),
        severity=sev,
        message=str(raw["message"]).strip(),
        timestamp=str(raw["timestamp"]).strip(),
    )


def load_alerts(path: str) -> tuple[list[Alert], int]:
    """Return (valid alerts, number of skipped rows)."""
    p = Path(path)
    if p.suffix.lower() == ".json":
        rows = json.loads(p.read_text())
    elif p.suffix.lower() == ".csv":
        with open(p, newline="") as f:
            rows = list(csv.DictReader(f))
    else:
        raise ValueError(f"Unsupported file type: {p.suffix}")

    alerts, skipped = [], 0
    seen_ids = set()
    for raw in rows:
        a = _normalize(raw)
        if a is None or a.alert_id in seen_ids:
            skipped += 1
            continue
        seen_ids.add(a.alert_id)
        alerts.append(a)
    return alerts, skipped
