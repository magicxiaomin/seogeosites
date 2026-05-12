from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]

REQUIRED_OUTPUTS = [
    "site_blueprint.json",
    "site_blueprint.md",
    "internal_link_map.json",
    "measurement_plan.json",
    "measurement_plan.md",
]
REQUIRED_TEMPLATES = [
    "opportunity_discovery_template.json",
    "opportunity_scoring_template.json",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Validate strategy/cluster artifacts for the staging MVP.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    errors = []
    for name in REQUIRED_OUTPUTS:
        if not (run / "outputs" / name).exists():
            errors.append(f"missing output artifact: {name}")
    for name in REQUIRED_TEMPLATES:
        if not (root / "factory/templates" / name).exists():
            errors.append(f"missing template artifact: {name}")
    blueprint = load_json(run / "outputs/site_blueprint.json") if (run / "outputs/site_blueprint.json").exists() else {}
    if blueprint.get("production_publish_allowed") is not False:
        errors.append("site_blueprint must keep production_publish_allowed=false")
    if len(blueprint.get("required_trust_pages", [])) < 5:
        errors.append("site_blueprint must list required trust pages")
    link_map = load_json(run / "outputs/internal_link_map.json") if (run / "outputs/internal_link_map.json").exists() else {}
    batch = load_json(run / "outputs/batch_publish_report.json")
    expected_supporting = len(batch.get("generated_pages", []))
    hub_links = [x for x in link_map.get("links", []) if x.get("from") == link_map.get("hub")]
    if len(hub_links) < expected_supporting:
        errors.append("internal link map must link hub to every generated page")
    hub_page = root / "content/sites/productivity-ai-pilot/pages/ai-workflow-templates-for-business-teams.md"
    if not hub_page.exists():
        errors.append("missing staging hub page")
    else:
        text = hub_page.read_text(encoding="utf-8")
        for page in batch.get("generated_pages", []):
            if page["slug"] not in text:
                errors.append(f"hub page missing supporting page slug: {page['slug']}")
    report = {"ok": not errors, "errors": errors, "run": str(run.relative_to(root))}
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit("Strategy artifact validation failed")


if __name__ == "__main__":
    main()
