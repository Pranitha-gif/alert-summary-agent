"""The agent: plan -> act (tools) -> observe -> write summary."""
from .grouping import group_alerts
from .ingest import load_alerts
from .models import Summary
from .summarizer import RuleBasedSummarizer, Summarizer


class AlertSummaryAgent:
    def __init__(self, summarizer: Summarizer | None = None, min_severity: str = "info"):
        self.summarizer = summarizer or RuleBasedSummarizer()
        self.min_severity = min_severity

    def run(self, path: str) -> Summary:
        steps = []

        steps.append("PLAN: load alerts -> filter by severity -> group duplicates -> rank -> summarize")

        alerts, skipped = load_alerts(path)
        steps.append(f"ACT load_alerts: {len(alerts)} valid, {skipped} skipped (malformed/duplicate id)")

        from .models import SEVERITY_ORDER
        floor = SEVERITY_ORDER[self.min_severity]
        kept = [a for a in alerts if a.severity_rank >= floor]
        steps.append(f"ACT filter(min_severity={self.min_severity}): {len(kept)} kept")

        groups = group_alerts(kept)
        steps.append(f"ACT group_alerts: {len(kept)} alerts -> {len(groups)} groups")

        # Observe: if everything is one huge group, note it for the reader
        if groups and groups[0].count > 0.5 * max(len(kept), 1) and len(groups) > 1:
            steps.append(f"OBSERVE: '{groups[0].service}' dominates ({groups[0].count} alerts) — likely a single root cause")

        headline, body = self.summarizer.summarize(groups, len(kept))
        steps.append("ACT summarize: digest written")
        return Summary(headline=headline, body=body, groups=groups, steps=steps)
