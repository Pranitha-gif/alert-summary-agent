# alert-summary-agent

A small agent that reads monitoring alerts (JSON/CSV), removes duplicates, groups repeats,
ranks by severity, and writes a short on-call digest. Python 3.10+, standard library only.
The LLM summary is optional.

## Agent loop
`PLAN -> ACT (load, filter, group) -> OBSERVE (dominant issue?) -> ACT (summarize)`
Use `--trace` to print every step.

## Structure
```
main.py                CLI
sample_alerts.json     demo data (includes a malformed row)
agent/models.py        Alert, AlertGroup, Summary
agent/ingest.py        load + validate JSON/CSV
agent/grouping.py      normalize messages, group, rank
agent/summarizer.py    RuleBasedSummarizer (offline) + LLMSummarizer (optional)
agent/agent.py         the agent loop
tests/test_agent.py
```

## Usage
```bash
python main.py sample_alerts.json --trace
python main.py sample_alerts.json --min-severity medium --out digest.md
pip install anthropic && export ANTHROPIC_API_KEY=... && python main.py sample_alerts.json --llm
```
CSV columns: `alert_id,source,service,severity,message,timestamp`.

## Ideas to extend
Slack/email delivery, live alert feeds (webhooks), time-window grouping, runbook lookup tool, persisting digests.
