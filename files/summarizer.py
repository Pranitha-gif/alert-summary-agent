"""Summarizers. RuleBasedSummarizer works offline; LLMSummarizer is optional."""
import os
from collections import Counter
from typing import Protocol

from .models import AlertGroup


class Summarizer(Protocol):
    def summarize(self, groups: list[AlertGroup], total_alerts: int) -> tuple[str, str]:
        """Return (headline, body)."""


class RuleBasedSummarizer:
    def __init__(self, top_n: int = 5):
        self.top_n = top_n

    def summarize(self, groups, total_alerts):
        if not groups:
            return "No alerts", "Nothing to report."

        sev = Counter()
        for g in groups:
            sev[g.severity] += g.count
        critical = sev.get("critical", 0)
        services = sorted({g.service for g in groups})

        headline = (f"{total_alerts} alerts across {len(services)} services "
                    f"collapsed into {len(groups)} issues"
                    + (f" — {critical} CRITICAL" if critical else ""))

        lines = ["Severity mix: " + ", ".join(f"{k}={v}" for k, v in sev.most_common()), "",
                 f"Top {min(self.top_n, len(groups))} issues:"]
        for i, g in enumerate(groups[: self.top_n], 1):
            lines.append(f"{i}. [{g.severity.upper()}] {g.service}: {g.sample_message} "
                         f"(x{g.count}, {g.first_seen} → {g.last_seen})")
        noisy = [g for g in groups if g.count >= 5 and g.severity in ("low", "info")]
        if noisy:
            lines += ["", "Noisy low-value alerts (consider tuning thresholds): "
                      + ", ".join(f"{g.service} ({g.count}x)" for g in noisy)]
        return headline, "\n".join(lines)


class LLMSummarizer:
    """Optional: uses the Anthropic API (pip install anthropic; set ANTHROPIC_API_KEY).
    Falls back to the rule-based summary if anything goes wrong."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
        self.fallback = RuleBasedSummarizer()

    def summarize(self, groups, total_alerts):
        headline, body = self.fallback.summarize(groups, total_alerts)
        try:
            import anthropic
            client = anthropic.Anthropic()
            prompt = ("You are an on-call assistant. Rewrite this alert digest as a concise "
                      "incident summary (max 120 words) with a suggested first action.\n\n"
                      f"{headline}\n{body}")
            resp = client.messages.create(model=self.model, max_tokens=400,
                                          messages=[{"role": "user", "content": prompt}])
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            return headline, text or body
        except Exception as exc:  # no key / no network / SDK missing
            return headline, body + f"\n\n(LLM unavailable, used rules: {type(exc).__name__})"
