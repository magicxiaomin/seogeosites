from pathlib import Path
import argparse
import json
import re

root = Path(__file__).resolve().parents[2]

REQUIRED_PHRASES = [
    "## Direct answer",
    "## Practical template",
    "### Inputs to collect",
    "### Step-by-step workflow",
    "### Reusable AI prompt block",
    "### Expected outputs",
    "### Human QA checks",
    "## Evidence and source notes",
    "### Accepted sources",
    "### Editorial guardrails",
]

FORBIDDEN_PLACEHOLDERS = [
    "lorem ipsum",
    "tbd",
    "todo:",
    "placeholder",
    "No accepted source URLs are recorded yet",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def count_numbered_steps(text):
    return len(re.findall(r"^\d+\. ", text, flags=re.M))


def count_bullets_under(text, heading):
    start = text.find(heading)
    if start == -1:
        return 0
    next_heading = text.find("\n## ", start + len(heading))
    section = text[start:] if next_heading == -1 else text[start:next_heading]
    return len(re.findall(r"^- ", section, flags=re.M))


def validate_page(run, page):
    rel = page["draft_path"]
    path = root / rel
    text = path.read_text(encoding="utf-8")
    errors = []
    warnings = []
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            errors.append(f"missing required section: {phrase}")
    if "```text" not in text:
        errors.append("missing fenced text prompt block")
    if count_numbered_steps(text) < 4:
        errors.append("expected at least 4 numbered workflow steps")
    if count_bullets_under(text, "### Inputs to collect") < 3:
        errors.append("expected at least 3 input bullets")
    if count_bullets_under(text, "### Expected outputs") < 3:
        errors.append("expected at least 3 expected-output bullets")
    lowered = text.lower()
    for forbidden in FORBIDDEN_PLACEHOLDERS:
        if forbidden.lower() in lowered:
            warnings.append(f"possible placeholder text: {forbidden}")
    sv = load_json(run / "outputs" / "pages" / page["opportunity_id"] / "source_verification.json")
    accepted = [s for s in sv.get("candidate_sources", []) if s.get("status") == "accepted" and s.get("reachable") is True]
    if len(accepted) < 2:
        errors.append("expected at least 2 accepted reachable sources")
    for source in accepted:
        if source.get("url") not in text:
            errors.append(f"accepted source URL not visible in page body: {source.get('url')}")
    if page.get("qa_status") not in {"Pass", "Needs Review", "Block"}:
        errors.append(f"invalid qa_status: {page.get('qa_status')}")
    return {
        "opportunity_id": page["opportunity_id"],
        "slug": page["slug"],
        "draft_path": rel,
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate staged page content quality for the pilot batch.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    batch = load_json(run / "outputs" / "batch_publish_report.json")
    results = [validate_page(run, page) for page in batch.get("generated_pages", [])]
    report = {
        "run": str(run.relative_to(root)),
        "pages": len(results),
        "ok": all(item["ok"] for item in results) and batch.get("publish_allowed") is False,
        "production_publish_allowed": batch.get("publish_allowed"),
        "results": results,
    }
    out = run / "outputs" / "content_quality_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit("Content quality validation failed")


if __name__ == "__main__":
    main()
