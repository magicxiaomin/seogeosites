from pathlib import Path
import argparse
import json

parser = argparse.ArgumentParser(description="Validate SEO/GEO factory run artifacts.")
parser.add_argument("run", nargs="?", default="factory/runs/sample")
parser.add_argument(
    "--stage",
    choices=["strategy", "full"],
    default="full",
    help="Validate only strategy-stage artifacts or the full sample pipeline.",
)
args = parser.parse_args()

run = Path(args.run)
required = [
    "inputs/opportunity_pool.json",
    "outputs/strategy_classification.json",
]
if args.stage == "full":
    required.extend(
        [
            "outputs/evidence_plan.json",
            "outputs/source_verification.json",
            "outputs/site_placement_decision.json",
            "outputs/content_brief.json",
            "outputs/qa_report.json",
        ]
    )

missing = [x for x in required if not (run / x).exists()]
if missing:
    raise SystemExit("Missing files: " + ", ".join(missing))

result = {"run": str(run), "stage": args.stage, "missing_files": missing, "ok": True}
if args.stage == "full":
    qa = json.loads((run / "outputs/qa_report.json").read_text())
    if qa["status"] not in ["Pass", "Needs Review", "Block"]:
        raise SystemExit("Invalid QA status")
    result["qa_status"] = qa["status"]

    batch_path = run / "outputs/batch_publish_report.json"
    if batch_path.exists():
        batch = json.loads(batch_path.read_text())
        pages = batch.get("generated_pages", [])
        if not pages:
            raise SystemExit("Batch publish report has no generated_pages")
        invalid_statuses = [p.get("opportunity_id") for p in pages if p.get("qa_status") not in ["Pass", "Needs Review", "Block"]]
        if invalid_statuses:
            raise SystemExit("Invalid page QA status for: " + ", ".join(invalid_statuses))
        missing_page_outputs = []
        for page in pages:
            oid = page.get("opportunity_id")
            for name in ["evidence_plan.json", "source_verification.json", "site_placement_decision.json", "content_brief.json", "qa_report.json"]:
                if not (run / "outputs" / "pages" / oid / name).exists():
                    missing_page_outputs.append(f"{oid}/{name}")
        if missing_page_outputs:
            raise SystemExit("Missing per-page outputs: " + ", ".join(missing_page_outputs))
        if batch.get("publish_allowed") is True and batch.get("status") != "Pass":
            raise SystemExit("publish_allowed cannot be true unless batch status is Pass")
        result["batch_status"] = batch.get("status")
        result["generated_pages"] = len(pages)
        result["publish_allowed"] = batch.get("publish_allowed")
else:
    strategy = json.loads((run / "outputs/strategy_classification.json").read_text())
    result["classified_opportunities"] = len(strategy)

print(json.dumps(result, indent=2))
