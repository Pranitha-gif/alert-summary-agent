"""CLI: python main.py sample_alerts.json [--min-severity medium] [--trace] [--llm] [--out digest.md]"""
import argparse
from pathlib import Path

from agent.agent import AlertSummaryAgent
from agent.models import SEVERITY_ORDER
from agent.summarizer import LLMSummarizer, RuleBasedSummarizer


def main():
    p = argparse.ArgumentParser(description="Alert summary agent")
    p.add_argument("path", help="alerts file (.json or .csv)")
    p.add_argument("--min-severity", default="info", choices=list(SEVERITY_ORDER))
    p.add_argument("--llm", action="store_true", help="use the Anthropic API for the summary text")
    p.add_argument("--trace", action="store_true", help="show the agent's steps")
    p.add_argument("--out", help="write the digest to a Markdown file")
    args = p.parse_args()

    summarizer = LLMSummarizer() if args.llm else RuleBasedSummarizer()
    result = AlertSummaryAgent(summarizer, args.min_severity).run(args.path)

    text = f"# {result.headline}\n\n{result.body}\n"
    if args.trace:
        text += "\n## Agent trace\n" + "\n".join(f"- {s}" for s in result.steps) + "\n"
    print(text)
    if args.out:
        Path(args.out).write_text(text)
        print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
