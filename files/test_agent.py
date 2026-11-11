import sys, pathlib, json, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent.agent import AlertSummaryAgent
from agent.grouping import group_alerts, normalize_message
from agent.ingest import load_alerts


def _alerts_file(rows):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(rows, f); f.close()
    return f.name


def _row(i, svc="svc", sev="high", msg="Task 1 failed", ts="2026-11-10T01:00:00"):
    return dict(alert_id=f"A{i}", source="s", service=svc, severity=sev, message=msg, timestamp=ts)


def test_normalize_message():
    assert normalize_message("Task 17 failed") == normalize_message("Task 42 failed")


def test_grouping_and_ranking():
    path = _alerts_file([_row(1, msg="Task 1 failed"), _row(2, msg="Task 2 failed"),
                         _row(3, svc="db", sev="critical", msg="Disk full")])
    alerts, _ = load_alerts(path)
    groups = group_alerts(alerts)
    assert len(groups) == 2
    assert groups[0].severity == "critical"          # critical ranks first
    assert groups[1].count == 2


def test_skips_malformed_and_duplicates():
    path = _alerts_file([_row(1), _row(1), dict(alert_id="X", service="")])
    alerts, skipped = load_alerts(path)
    assert len(alerts) == 1 and skipped == 2


def test_agent_end_to_end():
    path = _alerts_file([_row(i) for i in range(5)] + [_row(9, sev="low", msg="noise")])
    res = AlertSummaryAgent(min_severity="medium").run(path)
    assert "5 alerts" in res.headline
    assert any("PLAN" in s for s in res.steps)
