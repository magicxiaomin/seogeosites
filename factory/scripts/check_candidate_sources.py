from pathlib import Path
import argparse
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_url(url, timeout=12):
    req = Request(url, headers={"User-Agent": "SEO-GEO-Factory-SourceChecker/0.1"})
    try:
        with urlopen(req, timeout=timeout) as r:
            return {"http_status": r.status, "reachable": 200 <= r.status < 400, "error": None}
    except HTTPError as e:
        return {"http_status": e.code, "reachable": False, "error": str(e)}
    except URLError as e:
        return {"http_status": None, "reachable": False, "error": str(e.reason)}
    except Exception as e:
        return {"http_status": None, "reachable": False, "error": repr(e)}


def summarize(candidate_sources):
    total = len(candidate_sources)
    concrete = sum(1 for s in candidate_sources if str(s.get("url", "")).startswith(("http://", "https://")))
    reachable = sum(1 for s in candidate_sources if s.get("reachable") is True)
    accepted = sum(1 for s in candidate_sources if s.get("status") in {"checked", "accepted"})
    rejected = sum(1 for s in candidate_sources if s.get("status") == "rejected")
    return {
        "total_sources": total,
        "concrete_urls": concrete,
        "reachable_urls": reachable,
        "accepted_or_checked": accepted,
        "rejected": rejected,
        "all_sources_publish_ready": total >= 2 and accepted >= 2,
    }


def main():
    parser = argparse.ArgumentParser(description="HTTP-check candidate source URLs in a factory run.")
    parser.add_argument("--run", required=True)
    parser.add_argument("--accept-reachable", action="store_true", help="Mark reachable candidate_url sources as checked. Does not set overall QA to Pass.")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    pages_dir = run / "outputs" / "pages"
    checked = 0
    for page_dir in sorted(pages_dir.glob("*")):
        sv_path = page_dir / "source_verification.json"
        qa_path = page_dir / "qa_report.json"
        if not sv_path.exists():
            continue
        sv = load_json(sv_path)
        sources = sv.get("candidate_sources", [])
        for src in sources:
            url = src.get("url")
            if not str(url).startswith(("http://", "https://")):
                continue
            result = check_url(url)
            src.update(result)
            src["checked_at"] = datetime.now(timezone.utc).isoformat()
            if src.get("status") == "candidate_url":
                if result["reachable"] and args.accept_reachable:
                    src["status"] = "checked"
                    src["final_status"] = "checked_reachable_candidate"
                elif result["reachable"]:
                    src["final_status"] = "reachable_needs_acceptance"
                else:
                    src["final_status"] = "unreachable_or_error"
            checked += 1
        sv["summary"].update(summarize(sources))
        ready = sv["summary"].get("all_sources_publish_ready", False)
        sv.setdefault("review_flags", {})["missing_concrete_source_urls"] = not ready
        write_json(sv_path, sv)
        if qa_path.exists():
            qa = load_json(qa_path)
            qa.setdefault("review_flags", {})["missing_concrete_source_urls"] = not ready
            qa["checks"]["evidence_source_integrity"] = "Pass" if ready else "Needs Review: source URLs need verification or acceptance"
            req = [x for x in qa.get("required_before_publish", []) if "source" not in x.lower() and "concrete official URLs" not in x]
            if not ready:
                req.append("Accept at least 2 checked concrete source URLs")
            qa["required_before_publish"] = req
            qa["status"] = "Block" if qa.get("blockers") else "Needs Review"
            write_json(qa_path, qa)
    first = sorted(pages_dir.glob("*"))[0]
    for name in ["source_verification.json", "qa_report.json"]:
        src = first / name
        if src.exists():
            write_json(run / "outputs" / name, load_json(src))
    batch_path = run / "outputs" / "batch_publish_report.json"
    if batch_path.exists():
        batch = load_json(batch_path)
        flag_counts, status_counts = {}, {}
        for rec in batch.get("generated_pages", []):
            page_qa_path = pages_dir / rec["opportunity_id"] / "qa_report.json"
            if page_qa_path.exists():
                qa = load_json(page_qa_path)
                rec["qa_status"] = qa["status"]
                rec["review_flags"] = qa["review_flags"]
                rec["required_before_publish"] = qa["required_before_publish"]
            status_counts[rec["qa_status"]] = status_counts.get(rec["qa_status"], 0) + 1
            for flag, value in rec["review_flags"].items():
                if value:
                    flag_counts[flag] = flag_counts.get(flag, 0) + 1
        batch["batch_qa_summary"] = {"status_counts": status_counts, "review_flag_counts": flag_counts, "publish_readiness": "Block" if status_counts.get("Block") else "Needs Review"}
        batch["status"] = batch["batch_qa_summary"]["publish_readiness"]
        batch["publish_allowed"] = False
        write_json(batch_path, batch)
    print(f"Checked {checked} candidate source URL(s) in {run.relative_to(root)}")


if __name__ == "__main__":
    main()
