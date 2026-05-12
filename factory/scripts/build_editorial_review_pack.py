from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_summary(sv):
    accepted = [s for s in sv.get("candidate_sources", []) if s.get("status") == "accepted" and s.get("reachable") is True]
    return {
        "accepted_reachable_count": len(accepted),
        "accepted_sources": [
            {
                "title": s.get("title"),
                "url": s.get("url"),
                "supports_claims": s.get("supports_claims", []),
                "http_status": s.get("http_status"),
            }
            for s in accepted
        ],
    }


def page_review_record(run, page):
    oid = page["opportunity_id"]
    sv = load_json(run / "outputs" / "pages" / oid / "source_verification.json")
    qa = load_json(run / "outputs" / "pages" / oid / "qa_report.json")
    return {
        "opportunity_id": oid,
        "topic": page["topic"],
        "slug": page["slug"],
        "draft_path": page["draft_path"],
        "preview_path": f"/{page['slug']}.html",
        "qa_status": page["qa_status"],
        "staging_approved": page.get("staging_approved", False),
        "production_publish_allowed": False,
        "review_flags": {k: v for k, v in page.get("review_flags", {}).items() if v},
        "source_summary": source_summary(sv),
        "qa_checks": qa.get("checks", {}),
        "required_before_publish": page.get("required_before_publish", []),
        "reviewer_decision_options": ["approve_for_production_batch", "request_edits", "reject_or_defer"],
        "reviewer_decision": "",
        "reviewer_notes": "",
    }


def render_md(pack):
    lines = [
        "# Editorial review pack",
        "",
        f"Run: `{pack['run']}`",
        "",
        "This pack is for human/editorial production review. It is not a production publish approval by itself.",
        "",
        "## Batch status",
        "",
        f"- Staging approved: `{pack['staging_approved']}`",
        f"- Production publish allowed: `{pack['production_publish_allowed']}`",
        f"- Publish-readiness: `{pack['publish_readiness']}`",
        f"- Pages: `{len(pack['pages'])}`",
        "",
        "## Reviewer decision legend",
        "",
        "- `approve_for_production_batch`: reviewer accepts this page for a later explicit publish batch.",
        "- `request_edits`: page can remain in staging, but changes are required before production review.",
        "- `reject_or_defer`: remove from the candidate publish batch or revisit strategy/evidence.",
        "",
    ]
    for page in pack["pages"]:
        lines.extend([
            f"## {page['topic']}",
            "",
            f"- Opportunity ID: `{page['opportunity_id']}`",
            f"- Preview path: `{page['preview_path']}`",
            f"- Draft path: `{page['draft_path']}`",
            f"- QA status: `{page['qa_status']}`",
            f"- Staging approved: `{page['staging_approved']}`",
            f"- Production publish allowed: `{page['production_publish_allowed']}`",
            f"- Active review flags: `{', '.join(page['review_flags'].keys()) or 'none'}`",
            f"- Accepted reachable sources: `{page['source_summary']['accepted_reachable_count']}`",
            "",
            "### Accepted sources",
            "",
        ])
        for source in page["source_summary"]["accepted_sources"]:
            claims = ", ".join(source.get("supports_claims") or []) or "source coverage"
            lines.append(f"- {source.get('title')}: {source.get('url')} — supports: {claims}; HTTP {source.get('http_status')}")
        lines.extend(["", "### Required before production publish", ""])
        for item in page["required_before_publish"]:
            lines.append(f"- {item}")
        lines.extend([
            "",
            "### Reviewer decision",
            "",
            "- Decision: `[approve_for_production_batch | request_edits | reject_or_defer]`",
            "- Reviewer notes:",
            "",
            "```text",
            "",
            "```",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Build editorial review pack for a staging batch.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    out_dir = run / "outputs"
    batch = load_json(out_dir / "batch_publish_report.json")
    staging_path = out_dir / "staging_approval.json"
    staging = load_json(staging_path) if staging_path.exists() else {}
    pages = [page_review_record(run, page) for page in batch.get("generated_pages", [])]
    pack = {
        "run": str(run.relative_to(root)),
        "staging_approved": staging.get("staging_approved", False),
        "approval_scope": staging.get("scope", "preview_only_not_production_publish"),
        "production_publish_allowed": batch.get("publish_allowed", False),
        "publish_readiness": batch.get("status"),
        "pages": pages,
    }
    (out_dir / "editorial_review_pack.json").write_text(json.dumps(pack, indent=2), encoding="utf-8")
    (out_dir / "editorial_review_pack.md").write_text(render_md(pack), encoding="utf-8")
    print(json.dumps({"review_pack": str((out_dir / 'editorial_review_pack.md').relative_to(root)), "pages": len(pages)}, indent=2))


if __name__ == "__main__":
    main()
