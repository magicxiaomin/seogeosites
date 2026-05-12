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
else:
    strategy = json.loads((run / "outputs/strategy_classification.json").read_text())
    result["classified_opportunities"] = len(strategy)

print(json.dumps(result, indent=2))
