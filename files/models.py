"""Data models shared across the agent."""
from dataclasses import dataclass, field

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


@dataclass
class Alert:
    alert_id: str
    source: str          # e.g. "airflow", "db-monitor"
    service: str         # e.g. "orders-pipeline"
    severity: str        # critical | high | medium | low | info
    message: str
    timestamp: str       # ISO 8601

    @property
    def severity_rank(self) -> int:
        return SEVERITY_ORDER.get(self.severity, 0)


@dataclass
class AlertGroup:
    key: str                                   # service + normalized message
    service: str
    severity: str                              # highest severity in the group
    sample_message: str
    alerts: list = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.alerts)

    @property
    def first_seen(self) -> str:
        return min(a.timestamp for a in self.alerts)

    @property
    def last_seen(self) -> str:
        return max(a.timestamp for a in self.alerts)


@dataclass
class Summary:
    headline: str
    body: str
    groups: list
    steps: list            # the agent's plan/trace
