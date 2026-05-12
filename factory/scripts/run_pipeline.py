from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def classify(o):
    risks = " ".join(o.get("risk_flags", [])).lower()
    topic = o.get("topic", "").lower()
    seo = 4 if any(term in topic for term in ["workflow", "template", "guide"]) else 3
    geo = 5 if any(term in topic for term in ["workflow", "guide", "how to"]) else 3
    risk = 1 if any(term in risks for term in ["legal", "medical", "financial", "high ymyl"]) else (3 if any(term in risks for term in ["thin", "affiliate bias"]) else 5)
    if risk <= 2:
        cls, rec = "Reject", "no-go: risk veto"
    elif seo >= 4 and geo >= 4:
        cls, rec = "Balanced SEO+GEO", "go: MVP pilot candidate"
    elif geo > seo:
        cls, rec = "GEO-led", "requires explicit human approval"
    else:
        cls, rec = "Defer", "defer until stronger evidence/fit"
    return {
        "opportunity_id": o["id"],
        "seo_score": seo,
        "geo_score": geo,
        "risk_fit_score": risk,
        "classification": cls,
        "recommendation": rec,
        "required_evidence_level": "medium" if risk >= 4 else "high",
        "human_review_triggers": [] if cls == "Balanced SEO+GEO" else ["risk/strategy review"],
    }


def main():
    parser = argparse.ArgumentParser(description="Run the strategy classification stage for a factory run.")
    parser.add_argument("--run", required=True, help="Run directory, e.g. factory/runs/my-run")
    args = parser.parse_args()

    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    pool_path = run_dir / "inputs" / "opportunity_pool.json"
    if not pool_path.exists():
        raise SystemExit(f"Missing opportunity pool: {pool_path}")

    opportunities = json.loads(pool_path.read_text(encoding="utf-8"))
    strategy = [classify(o) for o in opportunities]
    (run_dir / "outputs").mkdir(exist_ok=True)
    (run_dir / "outputs" / "strategy_classification.json").write_text(json.dumps(strategy, indent=2), encoding="utf-8")
    print(f"Classified {len(strategy)} opportunities for {run_dir.relative_to(root)}")


if __name__ == "__main__":
    main()
