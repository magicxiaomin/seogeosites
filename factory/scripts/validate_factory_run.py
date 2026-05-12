from pathlib import Path
import json
import sys

run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("factory/runs/sample")
required = [
    "inputs/opportunity_pool.json",
    "outputs/strategy_classification.json",
    "outputs/evidence_plan.json",
    "outputs/site_placement_decision.json",
    "outputs/content_brief.json",
    "outputs/qa_report.json",
]
missing = [x for x in required if not (run / x).exists()]
if missing:
    raise SystemExit("Missing files: " + ", ".join(missing))
qa = json.loads((run / "outputs/qa_report.json").read_text())
if qa["status"] not in ["Pass", "Needs Review", "Block"]:
    raise SystemExit("Invalid QA status")
print(json.dumps({"run": str(run), "missing_files": missing, "qa_status": qa["status"], "ok": True}, indent=2))
