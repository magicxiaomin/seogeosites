from pathlib import Path
import argparse
import html
import json

root = Path(__file__).resolve().parents[2]
public = root / "public"

FLAG_LABELS = {
    "missing_concrete_source_urls": "Sources needed",
    "privacy_review_required": "Privacy",
    "copyright_review_required": "Copyright/IP",
    "monetization_review_required": "Monetization",
    "high_risk_topic": "High risk",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def badge(label, kind="neutral"):
    return f"<span class='badge {html.escape(kind)}'>{html.escape(label)}</span>"


def active_flag_badges(flags):
    active = [name for name, enabled in flags.items() if enabled]
    if not active:
        return badge("No active flags", "pass")
    return " ".join(badge(FLAG_LABELS.get(name, name), "review") for name in active)


def status_badge(status):
    kind = {"Pass": "pass", "Needs Review": "review", "Block": "block"}.get(status, "neutral")
    return badge(status, kind)


def accepted_source_count(source_verification):
    return sum(
        1
        for source in source_verification.get("candidate_sources", [])
        if source.get("status") == "accepted"
        and source.get("reachable") is True
    )


def remaining_actions(page, source_verification):
    actions = list(page.get("required_before_publish", []))
    accepted = accepted_source_count(source_verification)
    if accepted < 2:
        actions.append(f"Accept at least {2 - accepted} more reachable source(s)")
    return actions or ["No remaining checklist actions recorded"]


def main():
    parser = argparse.ArgumentParser(description="Build a static QA dashboard for a factory run.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    parser.add_argument("--out", default="public/qa-dashboard.html")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    batch = load_json(run / "outputs" / "batch_publish_report.json")
    staging = load_json(run / "outputs" / "staging_approval.json") if (run / "outputs" / "staging_approval.json").exists() else {}
    checklist_rel = None
    checklist_path = run / "outputs" / "review_checklists.md"
    if checklist_path.exists():
        public_checklist = public / "review-checklists.md"
        public_checklist.write_text(checklist_path.read_text(encoding="utf-8"), encoding="utf-8")
        checklist_rel = public_checklist.relative_to(public)
    review_pack_rel = None
    review_pack_path = run / "outputs" / "editorial_review_pack.md"
    if review_pack_path.exists():
        public_review_pack = public / "editorial-review-pack.md"
        public_review_pack.write_text(review_pack_path.read_text(encoding="utf-8"), encoding="utf-8")
        review_pack_rel = public_review_pack.relative_to(public)
    quality = load_json(run / "outputs" / "content_quality_report.json") if (run / "outputs" / "content_quality_report.json").exists() else {}
    review_decision_rel = None
    review_decision_path = run / "outputs" / "review_decision_application.md"
    if review_decision_path.exists():
        public_review_decision = public / "review-decision-application.md"
        public_review_decision.write_text(review_decision_path.read_text(encoding="utf-8"), encoding="utf-8")
        review_decision_rel = public_review_decision.relative_to(public)
    review_decision_input_rel = None
    review_decision_input_path = run / "inputs" / "review_decisions.json"
    if review_decision_input_path.exists():
        public_review_decision_input = public / "review-decisions-input.json"
        public_review_decision_input.write_text(review_decision_input_path.read_text(encoding="utf-8"), encoding="utf-8")
        review_decision_input_rel = public_review_decision_input.relative_to(public)
    simulation_rel = None
    simulation_path = run / "outputs" / "production_readiness_simulation.md"
    if simulation_path.exists():
        public_simulation = public / "production-readiness-simulation.md"
        public_simulation.write_text(simulation_path.read_text(encoding="utf-8"), encoding="utf-8")
        simulation_rel = public_simulation.relative_to(public)
    rows = []
    for page in batch["generated_pages"]:
        oid = page["opportunity_id"]
        sv_path = run / "outputs" / "pages" / oid / "source_verification.json"
        sv = load_json(sv_path) if sv_path.exists() else {"summary": {}, "candidate_sources": []}
        sources = "<br>".join(
            f"<a href='{html.escape(s.get('url',''))}'>{html.escape(s.get('title') or s.get('url',''))}</a> — {html.escape(s.get('status',''))} / {html.escape(s.get('final_status','not_checked'))} / HTTP {html.escape(str(s.get('http_status','n/a')))}"
            for s in sv.get("candidate_sources", [])
        ) or "No candidate sources yet"
        actions = "".join(f"<li>{html.escape(action)}</li>" for action in remaining_actions(page, sv))
        rows.append(f"""
<tr>
  <td>{html.escape(page['topic'])}<br><small><code>{html.escape(oid)}</code></small></td>
  <td>{status_badge(page['qa_status'])}<br>{badge('Staging approved', 'pass') if page.get('staging_approved') else badge('Staging pending', 'review')}</td>
  <td>{active_flag_badges(page['review_flags'])}</td>
  <td><strong>{accepted_source_count(sv)}</strong> accepted<br><small>{html.escape(str(sv.get('summary', {})))}</small></td>
  <td><ul class='actions'>{actions}</ul></td>
  <td>{sources}</td>
  <td><code>{html.escape(page['draft_path'])}</code></td>
</tr>""")
    summary = batch.get("batch_qa_summary", {})
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO/GEO Factory QA Dashboard</title>
<style>
body{{font-family:system-ui,sans-serif;margin:32px;line-height:1.5;color:#172033}}
.banner{{background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:14px;margin-bottom:18px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee9;padding:10px;vertical-align:top}}th{{background:#eef2ff;text-align:left}}
code{{white-space:normal}} .status{{font-size:20px;font-weight:700}}
.badge{{display:inline-block;border-radius:999px;padding:3px 9px;margin:2px;font-size:12px;font-weight:700;border:1px solid #cbd5e1}}
.badge.pass{{background:#ecfdf5;color:#065f46;border-color:#a7f3d0}} .badge.review{{background:#fff7ed;color:#9a3412;border-color:#fed7aa}} .badge.block{{background:#fef2f2;color:#991b1b;border-color:#fecaca}} .badge.neutral{{background:#f8fafc;color:#334155}}
.actions{{margin:0;padding-left:18px}}
</style>
</head>
<body>
<div class="banner">Staging QA dashboard — not a publish approval screen. Production publish remains blocked until human review.</div>
<h1>SEO/GEO Factory QA Dashboard</h1>
<p>Run: <code>{html.escape(str(run.relative_to(root)))}</code></p>
<p class="status">Staging: {badge('Approved', 'pass') if staging.get('staging_approved') else badge('Pending', 'review')} · Batch publish-readiness: {status_badge(batch.get('status','unknown'))} · Content quality: {badge('Pass', 'pass') if quality.get('ok') else badge('Not checked', 'review')} · production publish_allowed: <code>{html.escape(str(batch.get('publish_allowed')))}</code></p>
<p>{'<a href="' + html.escape(str(checklist_rel)) + '">Human review checklists</a>' if checklist_rel else 'Human review checklists have not been generated yet.'} · {'<a href="' + html.escape(str(review_pack_rel)) + '">Editorial review pack</a>' if review_pack_rel else 'Editorial review pack has not been generated yet.'} · {'<a href="' + html.escape(str(review_decision_input_rel)) + '">Review decisions input</a>' if review_decision_input_rel else 'Review decisions input has not been created yet.'} · {'<a href="' + html.escape(str(review_decision_rel)) + '">Review decision application</a>' if review_decision_rel else 'Review decisions have not been applied yet.'} · {'<a href="' + html.escape(str(simulation_rel)) + '">Production readiness simulation</a>' if simulation_rel else 'Production readiness simulation has not been generated yet.'}</p>
<h2>Batch summary</h2>
<pre>{html.escape(json.dumps(summary, indent=2))}</pre>
<h2>Pages</h2>
<table><thead><tr><th>Page</th><th>QA</th><th>Review flags</th><th>Sources</th><th>Remaining actions</th><th>Candidate sources</th><th>Draft</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table>
</body></html>"""
    out.write_text(doc, encoding="utf-8")
    print(f"Built QA dashboard: {out.relative_to(root)}")


if __name__ == "__main__":
    main()
