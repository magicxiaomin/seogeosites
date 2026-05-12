from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]
MIN_ACCEPTED_SOURCES = 2
REVIEW_ONLY_STATUS = "Needs Review"
VALID_STATUSES = {"Pass", "Needs Review", "Block"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def accepted_source_count(source_verification):
    return sum(
        1
        for source in source_verification.get("candidate_sources", [])
        if source.get("status") == "accepted"
        and source.get("reachable") is True
        and str(source.get("url", "")).startswith(("http://", "https://"))
    )


def main():
    parser = argparse.ArgumentParser(description="Validate SEO/GEO publish gates for a factory batch.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    parser.add_argument("--min-accepted-sources", type=int, default=MIN_ACCEPTED_SOURCES)
    args = parser.parse_args()

    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    batch_path = run / "outputs" / "batch_publish_report.json"
    if not batch_path.exists():
        raise SystemExit(f"Missing batch publish report: {batch_path}")

    batch = load_json(batch_path)
    pages = batch.get("generated_pages", [])
    errors = []
    warnings = []

    if batch.get("status") not in VALID_STATUSES:
        errors.append(f"Invalid batch status: {batch.get('status')}")
    if batch.get("publish_allowed") is True and batch.get("status") != "Pass":
        errors.append("Batch publish_allowed=true is only valid when status is Pass")

    for page in pages:
        oid = page.get("opportunity_id", "<missing-id>")
        status = page.get("qa_status")
        flags = page.get("review_flags", {})
        active_flags = [k for k, v in flags.items() if v]
        required = page.get("required_before_publish", [])
        sv_path = run / "outputs" / "pages" / oid / "source_verification.json"

        if status not in VALID_STATUSES:
            errors.append(f"{oid}: invalid qa_status {status}")
        if status == "Pass" and active_flags:
            errors.append(f"{oid}: cannot be Pass while review flags are active: {active_flags}")
        if status == "Pass" and required:
            errors.append(f"{oid}: cannot be Pass while required_before_publish is non-empty")
        if not sv_path.exists():
            errors.append(f"{oid}: missing source_verification.json")
            continue

        sv = load_json(sv_path)
        accepted = accepted_source_count(sv)
        if status == "Pass" and accepted < args.min_accepted_sources:
            errors.append(f"{oid}: Pass requires at least {args.min_accepted_sources} accepted reachable sources, found {accepted}")
        if accepted < args.min_accepted_sources:
            warnings.append(f"{oid}: has {accepted}/{args.min_accepted_sources} accepted reachable sources")

    if batch.get("publish_allowed") is True:
        not_pass = [p.get("opportunity_id") for p in pages if p.get("qa_status") != "Pass"]
        if not_pass:
            errors.append("Batch publish_allowed=true but not all pages are Pass: " + ", ".join(not_pass))

    result = {
        "run": str(run.relative_to(root)),
        "pages": len(pages),
        "batch_status": batch.get("status"),
        "publish_allowed": batch.get("publish_allowed"),
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
