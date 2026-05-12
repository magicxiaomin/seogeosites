from pathlib import Path
import argparse
import json
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Auto-approve a factory batch for staging/preview only.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()

    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    batch_path = run / "outputs" / "batch_publish_report.json"
    batch = load_json(batch_path)
    now = datetime.now(timezone.utc).isoformat()

    for page in batch.get("generated_pages", []):
        page["staging_approved"] = True
        page["staging_approved_at"] = now
        page["staging_approval_mode"] = "automated"
        page["staging_approval_scope"] = "preview_only_not_production_publish"

    batch["staging_approved"] = True
    batch["staging_approved_at"] = now
    batch["staging_approval_mode"] = "automated"
    batch["staging_approval_scope"] = "preview_only_not_production_publish"
    batch["production_publish_allowed"] = bool(batch.get("publish_allowed"))
    batch["reason"] = "Staging preview is automatically approved; production publish remains governed by publish_allowed and publish-gate validation."
    write_json(batch_path, batch)

    approval = {
        "run": str(run.relative_to(root)),
        "staging_approved": True,
        "staging_approved_at": now,
        "approval_mode": "automated",
        "scope": "preview_only_not_production_publish",
        "production_publish_allowed": bool(batch.get("publish_allowed")),
        "pages": [
            {
                "opportunity_id": p.get("opportunity_id"),
                "slug": p.get("slug"),
                "qa_status": p.get("qa_status"),
                "staging_approved": p.get("staging_approved"),
            }
            for p in batch.get("generated_pages", [])
        ],
    }
    out = run / "outputs" / "staging_approval.json"
    write_json(out, approval)
    print(f"Staging approved for preview: {out.relative_to(root)}")


if __name__ == "__main__":
    main()
