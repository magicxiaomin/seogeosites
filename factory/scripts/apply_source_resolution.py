from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]
ACCEPTED = {"checked", "accepted"}
REJECTED = {"rejected"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def summarize_sources(candidate_sources):
    total = len(candidate_sources)
    concrete = sum(1 for s in candidate_sources if str(s.get("url", "")).startswith(("http://", "https://")))
    accepted = sum(1 for s in candidate_sources if s.get("status") in ACCEPTED)
    rejected = sum(1 for s in candidate_sources if s.get("status") in REJECTED)
    return {"total_sources": total, "concrete_urls": concrete, "accepted_or_checked": accepted, "rejected": rejected, "all_sources_publish_ready": total >= 2 and accepted >= 2}


def main():
    parser = argparse.ArgumentParser(description="Apply source resolution input to factory QA/source artifacts.")
    parser.add_argument("--run", required=True)
    parser.add_argument("--input", required=True, help="JSON source resolution input file")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    inp = Path(args.input)
    if not inp.is_absolute():
        inp = root / inp
    data = load_json(inp)
    by_id = {r["opportunity_id"]: r for r in data.get("resolutions", [])}
    pages_dir = run / "outputs" / "pages"
    updated = []
    for page_dir in sorted(pages_dir.glob("*")):
        oid = page_dir.name
        if oid not in by_id:
            continue
        resolution = by_id[oid]
        sv_path = page_dir / "source_verification.json"
        qa_path = page_dir / "qa_report.json"
        sv = load_json(sv_path)
        qa = load_json(qa_path)
        candidate_sources = resolution.get("candidate_sources", [])
        sv["candidate_sources"] = candidate_sources
        sv["summary"].update(summarize_sources(candidate_sources))
        ready = sv["summary"]["all_sources_publish_ready"]
        sv["review_flags"]["missing_concrete_source_urls"] = not ready
        qa["review_flags"]["missing_concrete_source_urls"] = not ready
        req = [x for x in qa.get("required_before_publish", []) if "concrete official URLs" not in x]
        if not ready:
            req.append("Replace source-plan placeholders with at least 2 checked concrete source URLs")
        qa["required_before_publish"] = req
        qa["checks"]["evidence_source_integrity"] = "Needs Review: source URLs need verification" if not ready else "Pass"
        # Do not auto-Pass overall: human review remains required.
        qa["status"] = "Block" if qa.get("blockers") else "Needs Review"
        write_json(sv_path, sv)
        write_json(qa_path, qa)
        updated.append(oid)
    # Refresh top-level first-page artifacts and batch summary if possible.
    first = sorted(pages_dir.glob("*"))[0]
    for name in ["source_verification.json", "qa_report.json"]:
        write_json(run / "outputs" / name, load_json(first / name))
    batch_path = run / "outputs" / "batch_publish_report.json"
    if batch_path.exists():
        batch = load_json(batch_path)
        for rec in batch.get("generated_pages", []):
            oid = rec["opportunity_id"]
            page_qa = pages_dir / oid / "qa_report.json"
            if page_qa.exists():
                qa = load_json(page_qa)
                rec["qa_status"] = qa["status"]
                rec["review_flags"] = qa["review_flags"]
                rec["required_before_publish"] = qa["required_before_publish"]
        flag_counts = {}
        status_counts = {}
        for rec in batch.get("generated_pages", []):
            status_counts[rec["qa_status"]] = status_counts.get(rec["qa_status"], 0) + 1
            for flag, value in rec["review_flags"].items():
                if value:
                    flag_counts[flag] = flag_counts.get(flag, 0) + 1
        batch["batch_qa_summary"] = {"status_counts": status_counts, "review_flag_counts": flag_counts, "publish_readiness": "Block" if status_counts.get("Block") else "Needs Review"}
        batch["status"] = batch["batch_qa_summary"]["publish_readiness"]
        write_json(batch_path, batch)
    print(f"Applied source resolutions to {len(updated)} page(s): {', '.join(updated)}")


if __name__ == "__main__":
    main()
