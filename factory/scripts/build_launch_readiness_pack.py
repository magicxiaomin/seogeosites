from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]

TRUST_PAGES = [
    {
        "slug": "about-and-editorial-standards",
        "title": "About and Editorial Standards",
        "purpose": "Explain who the site is for, what the editorial promise is, and how AI-assisted content is reviewed before publication.",
        "required_sections": ["Audience and scope", "Editorial promise", "AI assistance disclosure", "Human review policy", "Correction and update path"],
        "status": "draft_required_before_production",
    },
    {
        "slug": "source-and-update-policy",
        "title": "Source and Update Policy",
        "purpose": "Define acceptable source types, claim support expectations, source-review cadence, and update triggers.",
        "required_sections": ["Accepted source hierarchy", "Claim evidence rules", "Freshness and review dates", "Correction workflow", "Unsupported-claim policy"],
        "status": "draft_required_before_production",
    },
    {
        "slug": "contact-and-corrections",
        "title": "Contact and Corrections",
        "purpose": "Give readers a way to report errors, request clarifications, or raise source concerns.",
        "required_sections": ["Contact route", "Correction request format", "Response expectations", "Escalation for sensitive issues"],
        "status": "draft_required_before_production",
    },
    {
        "slug": "privacy-and-disclosures",
        "title": "Privacy and Disclosures",
        "purpose": "State data handling, affiliate/sponsorship disclosures if any, analytics posture, and privacy contact path.",
        "required_sections": ["Data collection posture", "Analytics disclosure", "Affiliate/sponsorship disclosure", "Privacy contact", "Policy update date"],
        "status": "draft_required_before_production",
    },
]

ROBOTS_PLAN = {
    "current_staging": {
        "robots_txt": "User-agent: *\\nDisallow: /",
        "html_meta": "noindex,nofollow",
        "status": "active_for_preview_only",
    },
    "production_required_change": {
        "robots_txt": "Allow intended public URLs only after publish-batch approval; keep review/admin/artifact paths blocked.",
        "html_meta": "Remove noindex only from explicitly approved production pages; keep non-approved staging/review artifacts noindex.",
        "sitemap": "Generate sitemap only for production-approved URLs and exclude review artifacts.",
    },
    "never_index_paths": [
        "/qa-dashboard.html",
        "/editorial-review-pack.md",
        "/review-decisions-input.json",
        "/review-decision-application.md",
        "/production-readiness-simulation.md",
        "/review-checklists.md",
    ],
}

ANALYTICS_PLAN = {
    "pre_publish": [
        "Confirm brand/domain and final URL structure.",
        "Prepare Search Console property after domain decision.",
        "Decide analytics tool and privacy disclosure wording.",
        "Keep staging preview unindexed and exclude it from production metrics.",
    ],
    "post_publish_metrics": [
        "Indexing status by URL",
        "Impressions/clicks/CTR by query group",
        "Internal-link crawl coverage",
        "Engagement proxy by page type if analytics credentials exist",
        "Sampled AI-answer coverage observations",
        "Source freshness and update backlog",
    ],
    "credentials_required": ["Search Console", "Analytics provider if used"],
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_md(pack):
    lines = [
        "# Launch readiness pack",
        "",
        "This is a production-preparation artifact only. It does not approve publishing and does not change `publish_allowed`.",
        "",
        f"- Run: `{pack['run']}`",
        f"- Production publish allowed: `{pack['production_publish_allowed']}`",
        f"- Publish-readiness: `{pack['publish_readiness']}`",
        f"- Candidate pages after review decisions: `{pack['candidate_page_count']}`",
        "",
        "## Trust pages required before production",
        "",
    ]
    for page in pack["trust_pages"]:
        lines.extend([
            f"### {page['title']}",
            "",
            f"- Slug: `{page['slug']}`",
            f"- Status: `{page['status']}`",
            f"- Purpose: {page['purpose']}",
            "- Required sections:",
        ])
        lines.extend(f"  - {section}" for section in page["required_sections"])
        lines.append("")
    lines.extend(["## Production robots/indexing plan", ""])
    lines.extend([
        f"- Current staging robots: `{pack['robots_indexing_plan']['current_staging']['robots_txt']}`",
        f"- Current staging meta: `{pack['robots_indexing_plan']['current_staging']['html_meta']}`",
        f"- Production robots change: {pack['robots_indexing_plan']['production_required_change']['robots_txt']}",
        f"- Production meta change: {pack['robots_indexing_plan']['production_required_change']['html_meta']}",
        f"- Production sitemap rule: {pack['robots_indexing_plan']['production_required_change']['sitemap']}",
        "",
        "### Never-index paths",
        "",
    ])
    lines.extend(f"- `{path}`" for path in pack["robots_indexing_plan"]["never_index_paths"])
    lines.extend(["", "## Analytics and measurement hooks", "", "### Pre-publish setup", ""])
    lines.extend(f"- {item}" for item in pack["analytics_plan"]["pre_publish"])
    lines.extend(["", "### Post-publish metrics", ""])
    lines.extend(f"- {item}" for item in pack["analytics_plan"]["post_publish_metrics"])
    lines.extend(["", "## Remaining blockers", ""])
    lines.extend(f"- {item}" for item in pack["remaining_blockers"])
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Build a launch readiness pack without enabling production publishing.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    out = run / "outputs"
    batch = load_json(out / "batch_publish_report.json")
    decisions_path = out / "review_decision_application.json"
    decisions = load_json(decisions_path) if decisions_path.exists() else {"pages": []}
    candidate_pages = [p for p in decisions.get("pages", []) if p.get("candidate_for_explicit_publish_batch")]
    blockers = [
        "explicit_publish_batch_approval",
        "final_brand_domain_decision",
        "trust_pages_finalized",
        "production_robots_indexing_plan_approved",
        "analytics_search_console_hooks_if_credentials_exist",
    ]
    if not candidate_pages:
        blockers.insert(0, "no_pages_approved_for_publish_batch")
    pack = {
        "run": str(run.relative_to(root)),
        "production_publish_allowed": False,
        "current_publish_allowed_field": batch.get("publish_allowed"),
        "publish_readiness": "Needs Review",
        "candidate_page_count": len(candidate_pages),
        "candidate_pages": candidate_pages,
        "trust_pages": TRUST_PAGES,
        "robots_indexing_plan": ROBOTS_PLAN,
        "analytics_plan": ANALYTICS_PLAN,
        "remaining_blockers": blockers,
    }
    (out / "launch_readiness_pack.json").write_text(json.dumps(pack, indent=2), encoding="utf-8")
    (out / "launch_readiness_pack.md").write_text(render_md(pack), encoding="utf-8")
    print(json.dumps({"ok": True, "production_publish_allowed": False, "candidate_page_count": len(candidate_pages), "remaining_blockers": blockers}, indent=2))


if __name__ == "__main__":
    main()
