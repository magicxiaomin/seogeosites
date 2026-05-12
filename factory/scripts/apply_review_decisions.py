from pathlib import Path
import argparse
import json
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[2]
ALLOWED = {"pending", "approve_for_production_batch", "request_edits", "reject_or_defer"}
PUBLICATION_SAFE_DECISIONS = {"pending", "request_edits", "reject_or_defer"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else root / p


def normalize_pages(decision_doc):
    pages = decision_doc.get("pages", [])
    if not isinstance(pages, list):
        raise SystemExit("review decisions input must contain a pages array")
    by_id = {}
    errors = []
    for item in pages:
        oid = item.get("opportunity_id")
        decision = item.get("decision", "pending")
        if not oid:
            errors.append("page decision is missing opportunity_id")
            continue
        if oid in by_id:
            errors.append(f"duplicate decision for {oid}")
        if decision not in ALLOWED:
            errors.append(f"{oid}: invalid decision {decision!r}; allowed: {sorted(ALLOWED)}")
        by_id[oid] = item
    if errors:
        raise SystemExit("\n".join(errors))
    return by_id


def render_md(applied):
    lines = [
        "# Review decision application",
        "",
        "This artifact records editorial review decisions for a staging batch. It does not publish content and does not enable production publishing.",
        "",
        f"- Run: `{applied['run']}`",
        f"- Production publish allowed: `{applied['production_publish_allowed']}`",
        f"- Publish-readiness: `{applied['publish_readiness']}`",
        f"- Explicit publish batch approval present: `{applied['explicit_publish_batch_approval_present']}`",
        "",
        "## Decision summary",
        "",
    ]
    for key, count in applied["decision_counts"].items():
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Pages", ""])
    for page in applied["pages"]:
        lines.extend([
            f"### {page['slug']}",
            "",
            f"- Opportunity ID: `{page['opportunity_id']}`",
            f"- Topic: {page['topic']}",
            f"- Decision: `{page['decision']}`",
            f"- Production review state: `{page['production_review_state']}`",
            f"- Candidate for explicit publish batch: `{page['candidate_for_explicit_publish_batch']}`",
            f"- Reviewer notes: {page.get('reviewer_notes') or 'none'}",
            "- Required edits:",
        ])
        edits = page.get("required_edits") or []
        if edits:
            lines.extend(f"  - {edit}" for edit in edits)
        else:
            lines.append("  - none recorded")
        lines.append("")
    lines.extend(["## Remaining production gates", ""])
    for item in applied["remaining_production_gates"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Apply human review decisions to a staging batch without enabling production publishing.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    parser.add_argument("--decisions", default="factory/runs/pilot-001/inputs/review_decisions.json")
    args = parser.parse_args()
    run = resolve(args.run)
    decisions_path = resolve(args.decisions)
    out = run / "outputs"
    batch = load_json(out / "batch_publish_report.json")
    decision_doc = load_json(decisions_path) if decisions_path.exists() else {"pages": []}
    decision_by_id = normalize_pages(decision_doc)

    page_records = []
    counts = {key: 0 for key in sorted(ALLOWED)}
    missing_decisions = []
    for page in batch.get("generated_pages", []):
        oid = page["opportunity_id"]
        decision = decision_by_id.get(oid, {"decision": "pending"})
        decision_name = decision.get("decision", "pending")
        counts[decision_name] += 1
        if oid not in decision_by_id:
            missing_decisions.append(oid)
        candidate = decision_name == "approve_for_production_batch"
        if decision_name == "approve_for_production_batch":
            state = "candidate_for_publish_batch_pending_explicit_batch_approval"
        elif decision_name == "request_edits":
            state = "needs_editorial_changes"
        elif decision_name == "reject_or_defer":
            state = "deferred_or_rejected"
        else:
            state = "pending_review"
        page_records.append({
            "opportunity_id": oid,
            "topic": page.get("topic"),
            "slug": page.get("slug"),
            "decision": decision_name,
            "production_review_state": state,
            "candidate_for_explicit_publish_batch": candidate,
            "reviewer_notes": decision.get("reviewer_notes", ""),
            "required_edits": decision.get("required_edits", []),
            "publish_batch_notes": decision.get("publish_batch_notes", ""),
        })

    explicit_batch_approval = bool(decision_doc.get("explicit_publish_batch_approval"))
    remaining_gates = [
        "publish_batch_approval",
        "final_brand_domain_decision",
        "trust_pages_finalized",
        "production_robots_indexing_plan",
        "analytics_search_console_hooks_if_credentials_exist",
    ]
    if missing_decisions:
        remaining_gates.insert(0, "all_pages_have_recorded_human_review_decisions")
    if not explicit_batch_approval:
        remaining_gates.insert(0, "explicit_publish_batch_approval")

    applied = {
        "run": str(run.relative_to(root)),
        "decision_source": str(decisions_path.relative_to(root)) if decisions_path.exists() else None,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "simulation_only": True,
        "production_publish_allowed": False,
        "current_publish_allowed_field": batch.get("publish_allowed"),
        "publish_readiness": "Needs Review",
        "explicit_publish_batch_approval_present": explicit_batch_approval,
        "missing_page_decisions": missing_decisions,
        "decision_counts": counts,
        "pages": page_records,
        "remaining_production_gates": remaining_gates,
    }
    (out / "review_decision_application.json").write_text(json.dumps(applied, indent=2), encoding="utf-8")
    (out / "review_decision_application.md").write_text(render_md(applied), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "production_publish_allowed": False,
        "publish_readiness": "Needs Review",
        "decision_counts": counts,
        "missing_page_decisions": missing_decisions,
    }, indent=2))


if __name__ == "__main__":
    main()
