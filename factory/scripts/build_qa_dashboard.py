from pathlib import Path
import argparse
import html
import json

root = Path(__file__).resolve().parents[2]
public = root / "public"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


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
    rows = []
    for page in batch["generated_pages"]:
        oid = page["opportunity_id"]
        sv_path = run / "outputs" / "pages" / oid / "source_verification.json"
        sv = load_json(sv_path) if sv_path.exists() else {"summary": {}, "candidate_sources": []}
        flags = ", ".join(k for k, v in page["review_flags"].items() if v) or "none"
        sources = "<br>".join(
            f"<a href='{html.escape(s.get('url',''))}'>{html.escape(s.get('title') or s.get('url',''))}</a> — {html.escape(s.get('status',''))} / {html.escape(s.get('final_status','not_checked'))} / HTTP {html.escape(str(s.get('http_status','n/a')))}"
            for s in sv.get("candidate_sources", [])
        ) or "No candidate sources yet"
        rows.append(f"""
<tr>
  <td>{html.escape(page['topic'])}</td>
  <td><strong>{html.escape(page['qa_status'])}</strong></td>
  <td>{html.escape(flags)}</td>
  <td>{html.escape(str(sv.get('summary', {})))}</td>
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
</style>
</head>
<body>
<div class="banner">Staging QA dashboard — not a publish approval screen. Production publish remains blocked until human review.</div>
<h1>SEO/GEO Factory QA Dashboard</h1>
<p>Run: <code>{html.escape(str(run.relative_to(root)))}</code></p>
<p class="status">Batch readiness: {html.escape(batch.get('status','unknown'))} · publish_allowed: {html.escape(str(batch.get('publish_allowed')))}</p>
<h2>Batch summary</h2>
<pre>{html.escape(json.dumps(summary, indent=2))}</pre>
<h2>Pages</h2>
<table><thead><tr><th>Page</th><th>QA</th><th>Review flags</th><th>Source summary</th><th>Candidate sources</th><th>Draft</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table>
</body></html>"""
    out.write_text(doc, encoding="utf-8")
    print(f"Built QA dashboard: {out.relative_to(root)}")


if __name__ == "__main__":
    main()
