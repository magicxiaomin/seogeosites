from pathlib import Path
import argparse
import json
import shutil
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description="Create a new SEO/GEO factory run directory.")
    parser.add_argument("--name", help="Run name. Defaults to UTC timestamp.")
    parser.add_argument("--from-sample", action="store_true", help="Seed the new run with the sample opportunity pool.")
    args = parser.parse_args()

    run_name = args.name or datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    run_dir = root / "factory" / "runs" / run_name
    if run_dir.exists():
        raise SystemExit(f"Run already exists: {run_dir}")

    (run_dir / "inputs").mkdir(parents=True)
    (run_dir / "outputs").mkdir()

    manifest = {
        "run_name": run_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "created",
        "publish_readiness": "not_evaluated",
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if args.from_sample:
        sample = root / "factory" / "runs" / "sample" / "inputs" / "opportunity_pool.json"
        if not sample.exists():
            raise SystemExit("Sample opportunity pool does not exist. Run npm run factory:sample first.")
        shutil.copy(sample, run_dir / "inputs" / "opportunity_pool.json")

    print(run_dir.relative_to(root))


if __name__ == "__main__":
    main()
