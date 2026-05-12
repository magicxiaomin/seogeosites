from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_queries(page):
    topic = page["topic"]
    flags = page.get("review_flags", {})
    queries = [
        f"official docs {topic}",
        f"help center {topic}",
        f"{topic} privacy policy official docs" if flags.get("privacy_review_required") else None,
        f"{topic} copyright policy official docs" if flags.get("copyright_review_required") else None,
        f"{topic} affiliate disclosure guidelines" if flags.get("monetization_review_required") else None,
    ]
    return [q for q in queries if q]


def page_source_state(run, opportunity_id):
    sv_path = run / "outputs" / "pages" / opportunity_id / "source_verification.json"
    if not sv_path.exists():
        return {"summary": {}, "candidate_sources": [], "accepted_sources": []}
    sv = load_json(sv_path)
    candidates = sv.get("candidate_sources", [])
    accepted = [s for s in candidates if s.get("status") in {"checked", "accepted"}]
    return {
        "summary": sv.get("summary", {}),
        "candidate_sources": candidates,
        "accepted_sources": accepted,
    }


def task_status(page, state):
    flags = page.get("review_flags", {})
    if flags.get("missing_concrete_source_urls"):
        if state["candidate_sources"]:
            return "candidate_urls_need_acceptance"
        return "open"
    if flags.get("privacy_review_required") or flags.get("copyright_review_required") or flags.get("monetization_review_required"):
        return "sources_resolved_review_flags_remain"
    return "source_ready_human_review_required"


def main():
    parser = argparse.ArgumentParser(description="Generate source research tasks from a factory batch report.")
    parser.add_argument("--run", required=True, help="Run directory, e.g. factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    report_path = run / "outputs" / "batch_publish_report.json"
    if not report_path.exists():
        raise SystemExit(f"Missing batch report: {report_path}")
    report = load_json(report_path)
    tasks = []
    for page in report["generated_pages"]:
        state = page_source_state(run, page["opportunity_id"])
        tasks.append({
            "opportunity_id": page["opportunity_id"],
            "topic": page["topic"],
            "draft_path": page["draft_path"],
            "priority": "high" if page["review_flags"].get("missing_concrete_source_urls") else "medium",
            "required_evidence": [
                "At least 2 concrete official/source URLs",
                "One source supporting factual tool/platform capability claims",
                "One source or original editorial note for workflow/template rationale",
            ],
            "recommended_queries": source_queries(page),
            "source_summary": state["summary"],
            "candidate_sources": state["candidate_sources"],
            "accepted_sources": state["accepted_sources"],
            "review_flags": page["review_flags"],
            "status": task_status(page, state),
        })
    out_json = run / "outputs" / "source_research_tasks.json"
    out_md = run / "outputs" / "source_research_tasks.md"
    out_json.write_text(json.dumps({"run": str(run.relative_to(root)), "tasks": tasks}, indent=2), encoding="utf-8")
    lines = ["# Source Research Tasks", "", f"Run: `{run.relative_to(root)}`", "", "These tasks must be resolved before any page can move from `Needs Review` to `Pass`.", ""]
    for task in tasks:
        flags = ", ".join([k for k, v in task["review_flags"].items() if v]) or "none"
        lines += [
            f"## {task['topic']}",
            "",
            f"- Opportunity: `{task['opportunity_id']}`",
            f"- Draft: `{task['draft_path']}`",
            f"- Status: {task['status']}",
            f"- Priority: {task['priority']}",
            f"- Review flags: {flags}",
            f"- Source summary: `{task['source_summary']}`",
        ]
        if task["candidate_sources"]:
            lines += ["- Candidate sources:"]
            for source in task["candidate_sources"]:
                lines.append(
                    f"  - {source.get('url')} — status `{source.get('status')}`, final `{source.get('final_status', 'not_checked')}`, HTTP `{source.get('http_status', 'n/a')}`"
                )
        lines += ["- Required evidence:"]
        lines += [f"  - {x}" for x in task["required_evidence"]]
        lines += ["- Recommended queries:"]
        lines += [f"  - `{q}`" for q in task["recommended_queries"]]
        lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {len(tasks)} source research task(s) for {run.relative_to(root)}")


if __name__ == "__main__":
    main()
