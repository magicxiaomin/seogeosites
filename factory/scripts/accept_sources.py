from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def refresh_batch(run):
    pages_dir = run / "outputs" / "pages"
    batch_path = run / "outputs" / "batch_publish_report.json"
    if not batch_path.exists():
        return
    batch = load_json(batch_path)
    flag_counts, status_counts = {}, {}
    for rec in batch.get("generated_pages", []):
        page_qa = pages_dir / rec["opportunity_id"] / "qa_report.json"
        if page_qa.exists():
            qa = load_json(page_qa)
            rec["qa_status"] = qa["status"]
            rec["review_flags"] = qa["review_flags"]
            rec["required_before_publish"] = qa["required_before_publish"]
        status_counts[rec["qa_status"]] = status_counts.get(rec["qa_status"], 0) + 1
        for flag, value in rec["review_flags"].items():
            if value:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
    batch["batch_qa_summary"] = {
        "status_counts": status_counts,
        "review_flag_counts": flag_counts,
        "publish_readiness": "Block" if status_counts.get("Block") else "Needs Review",
    }
    batch["status"] = batch["batch_qa_summary"]["publish_readiness"]
    batch["publish_allowed"] = False
    write_json(batch_path, batch)


def main():
    parser = argparse.ArgumentParser(description="Accept checked source URLs for a page without auto-publishing.")
    parser.add_argument("--run", required=True)
    parser.add_argument("--opportunity-id", required=True)
    parser.add_argument("--url", action="append", required=True, help="Candidate URL to mark accepted. Repeatable.")
    parser.add_argument("--reason", default="Accepted for source coverage after review.")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    page_dir = run / "outputs" / "pages" / args.opportunity_id
    sv_path = page_dir / "source_verification.json"
    qa_path = page_dir / "qa_report.json"
    sv = load_json(sv_path)
    urls = set(args.url)
    accepted_count = 0
    for source in sv.get("candidate_sources", []):
        if source.get("url") in urls:
            if source.get("reachable") is not True:
                source["status"] = "rejected"
                source["final_status"] = "rejected_not_reachable"
                source["acceptance_note"] = "Cannot accept unreachable URL."
            else:
                source["status"] = "accepted"
                source["final_status"] = "accepted_reachable_source"
                source["acceptance_note"] = args.reason
                accepted_count += 1
    accepted = sum(1 for s in sv.get("candidate_sources", []) if s.get("status") in {"checked", "accepted"})
    concrete = sum(1 for s in sv.get("candidate_sources", []) if str(s.get("url", "")).startswith(("http://", "https://")))
    reachable = sum(1 for s in sv.get("candidate_sources", []) if s.get("reachable") is True)
    sv["summary"].update({
        "concrete_urls": concrete,
        "reachable_urls": reachable,
        "accepted_or_checked": accepted,
        "all_sources_publish_ready": accepted >= 2,
    })
    ready = sv["summary"]["all_sources_publish_ready"]
    sv["review_flags"]["missing_concrete_source_urls"] = not ready
    write_json(sv_path, sv)
    qa = load_json(qa_path)
    qa["review_flags"]["missing_concrete_source_urls"] = not ready
    qa["checks"]["evidence_source_integrity"] = "Pass" if ready else "Needs Review: source URLs need verification or acceptance"
    req = [x for x in qa.get("required_before_publish", []) if "source" not in x.lower() and "concrete official URLs" not in x]
    if not ready:
        req.append("Accept at least 2 checked concrete source URLs")
    qa["required_before_publish"] = req
    qa["status"] = "Block" if qa.get("blockers") else "Needs Review"
    write_json(qa_path, qa)
    first = sorted((run / "outputs" / "pages").glob("*"))[0]
    for name in ["source_verification.json", "qa_report.json"]:
        write_json(run / "outputs" / name, load_json(first / name))
    refresh_batch(run)
    print(f"Accepted {accepted_count} source URL(s) for {args.opportunity_id}; publish still requires human review.")


if __name__ == "__main__":
    main()
