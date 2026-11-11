"""Deduplicate alerts into groups and rank them."""
import re
from collections import defaultdict

from .models import SEVERITY_ORDER, Alert, AlertGroup


def normalize_message(msg: str) -> str:
    """Strip numbers, ids and hex so 'Task 17 failed' and 'Task 42 failed' group together."""
    m = msg.lower()
    m = re.sub(r"0x[0-9a-f]+", "<hex>", m)
    m = re.sub(r"\b[0-9a-f]{8,}\b", "<id>", m)
    m = re.sub(r"\d+(\.\d+)?", "<n>", m)
    return re.sub(r"\s+", " ", m).strip()


def group_alerts(alerts: list[Alert]) -> list[AlertGroup]:
    buckets: dict[str, list[Alert]] = defaultdict(list)
    for a in alerts:
        buckets[f"{a.service}|{normalize_message(a.message)}"].append(a)

    groups = []
    for key, items in buckets.items():
        top = max(items, key=lambda a: a.severity_rank)
        groups.append(AlertGroup(key=key, service=items[0].service,
                                 severity=top.severity,
                                 sample_message=top.message, alerts=items))
    return rank_groups(groups)


def rank_groups(groups: list[AlertGroup]) -> list[AlertGroup]:
    """Highest severity first, then most frequent, then most recent."""
    return sorted(groups, key=lambda g: (-SEVERITY_ORDER[g.severity], -g.count, g.last_seen),
                  reverse=False)
