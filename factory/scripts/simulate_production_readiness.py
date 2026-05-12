from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Simulate production readiness without enabling publish.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    out = run / "outputs"
    batch = load_json(out / "batch_publish_report.json")
    blueprint = load_json(out / "site_blueprint.json") if (out / "site_blueprint.json").exists() else {}
    quality = load_json(out / "content_quality_report.json") if (out / "content_quality_report.json").exists() else {}
    strategy_ok = (out / "internal_link_map.json").exists() and (out / "measurement_plan.json").exists()

    page_gaps = []
    for page in batch.get("generated_pages", []):
        required = list(page.get("required_before_publish", []))
        flags = [k for k, v in page.get("review_flags", {}).items() if v]
        page_gaps.append({
            "opportunity_id": page["opportunity_id"],
            "slug": page["slug"],
            "ready_for_publish_batch_after_human_review": bool(quality.get("ok")) and not page.get("blockers"),
            "required_before_publish": required,
            "active_review_flags": flags,
        })

    missing = []
    if not quality.get("ok"):
        missing.append("content_quality_pass")
    if not strategy_ok:
        missing.append("strategy_cluster_measurement_artifacts")
    if not blueprint.get("production_blockers"):
        missing.append("explicit_production_blocker_list")
    missing.extend([
        "human_editorial_decisions_recorded",
        "publish_batch_approval",
        "final_brand_domain_decision",
        "trust_pages_finalized",
        "production_robots_indexing_plan",
        "analytics_search_console_hooks_if_credentials_exist",
    ])

    simulation = {
        "run": str(run.relative_to(root)),
        "simulation_only": True,
        "production_publish_allowed": False,
        "current_publish_allowed_field": batch.get("publish_allowed"),
        "publish_readiness": batch.get("status"),
        "can_enter_human_publish_review_queue": bool(quality.get("ok")) and strategy_ok and batch.get("publish_allowed") is False,
        "would_enable_publish_after_this_simulation": False,
        "missing_before_production_publish": missing,
        "page_gaps": page_gaps,
    }
    (out / "production_readiness_simulation.json").write_text(json.dumps(simulation, indent=2), encoding="utf-8")
    md = [
        "# Production readiness simulation",
        "",
        "Status: simulation only — production publishing remains disabled.",
        "",
        f"- Production publish allowed: `{simulation['production_publish_allowed']}`",
        f"- Current publish_allowed field: `{simulation['current_publish_allowed_field']}`",
        f"- Can enter human publish review queue: `{simulation['can_enter_human_publish_review_queue']}`",
        "",
        "## Missing before production publish",
        "",
    ]
    md.extend(f"- {item}" for item in missing)
    md.extend(["", "## Page-level review gaps", ""])
    for page in page_gaps:
        md.extend([
            f"### {page['slug']}",
            "",
            f"- Ready for publish batch after human review: `{page['ready_for_publish_batch_after_human_review']}`",
            f"- Active review flags: `{', '.join(page['active_review_flags']) or 'none'}`",
            "- Required before publish:",
        ])
        md.extend(f"  - {item}" for item in page["required_before_publish"])
        md.append("")
    (out / "production_readiness_simulation.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "simulation_only": True, "production_publish_allowed": False, "can_enter_human_publish_review_queue": simulation["can_enter_human_publish_review_queue"]}, indent=2))


if __name__ == "__main__":
    main()
