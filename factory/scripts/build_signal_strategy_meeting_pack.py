from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def level(score):
    if score >= 13:
        return "high"
    if score >= 9:
        return "medium"
    return "low"


def credible_signal_count(candidate):
    return sum(
        1
        for signal in candidate.get("observed_signals", [])
        if signal.get("strength") in {"medium", "strong"}
    )


def classify(candidate):
    risk = candidate.get("risk", {})
    if risk.get("veto") in {"reject", "defer"}:
        return risk.get("veto")
    demand = candidate.get("demand_signal", {}).get("score", 0)
    capture = candidate.get("capture_likelihood", {}).get("score", 0)
    geo = candidate.get("geo_likelihood", {}).get("score", 0)
    evidence = candidate.get("evidence_availability", {}).get("score", 0)
    total = demand + capture + geo + evidence
    credible = credible_signal_count(candidate)
    # Do not recommend a production opportunity pool from weak/noisy public mentions alone.
    # A candidate needs at least one credible observed signal plus good demand/capture/GEO/evidence scores.
    if demand >= 4 and capture >= 3 and geo >= 3 and evidence >= 3 and credible >= 1:
        return "recommend_for_opportunity_pool"
    if total >= 10 or credible >= 1:
        return "watch_or_research_more"
    return "defer"


def score_candidate(candidate):
    demand = candidate.get("demand_signal", {}).get("score", 0)
    capture = candidate.get("capture_likelihood", {}).get("score", 0)
    geo = candidate.get("geo_likelihood", {}).get("score", 0)
    evidence = candidate.get("evidence_availability", {}).get("score", 0)
    strategic = candidate.get("strategic_fit", {}).get("score", 0)
    total = demand + capture + geo + evidence + strategic
    return {"total": total, "tier": level(total), "recommendation": classify(candidate)}


def default_input():
    return {
        "run_type": "signal_led_strategy_meeting",
        "status": "template_plus_staging_examples_not_external_signal_verified",
        "target_site": "productivity-ai-pilot",
        "target_region_language": "en-US initially unless changed by human",
        "strategy_goal": "Find traffic-capturable SEO/GEO opportunities from signals before creating content clusters or pages.",
        "signal_sources_to_use_next": [
            "Google Trends / keyword tool exports",
            "Search Console once production site exists",
            "SERP sampling and People Also Ask",
            "competitor URL/content-structure observations",
            "community questions from Reddit, forums, YouTube, X, Hacker News, Product Hunt, app stores",
            "AI answer gap sampling from ChatGPT/Perplexity/Gemini prompts",
            "official product docs, changelogs, standards, and public datasets"
        ],
        "candidates": [
            {
                "candidate_id": "sig-2026-05-12-001",
                "working_topic": "AI workflow template for onboarding new employees",
                "signal_status": "staging_example_from_pipeline_validation_not_real_keyword_volume_verified",
                "observed_signals": [
                    {"source": "pipeline validation batch", "evidence": "Selected as low/medium-risk workflow-template hypothesis", "strength": "weak"}
                ],
                "query_patterns": ["ai workflow template for onboarding new employees", "onboarding new employees ai workflow template", "new employee onboarding workflow checklist"],
                "intent": "template and implementation guide",
                "demand_signal": {"score": 2, "rationale": "Plausible long-tail demand, but no external trend/volume data has been attached yet."},
                "capture_likelihood": {"score": 3, "rationale": "Specific long-tail intent is more capturable than a broad AI/HR head term."},
                "geo_likelihood": {"score": 4, "rationale": "Workflow/checklist/template content is extractable for AI answers."},
                "evidence_availability": {"score": 3, "rationale": "Official HR/workspace sources exist; production examples still need reviewer input."},
                "strategic_fit": {"score": 3, "rationale": "Fits a productivity/AI workflow pilot cluster."},
                "risk": {"veto": "pass", "flags": ["employee data privacy review required"]},
                "recommended_action": "watch_or_research_more_before_publish_pool",
                "why_now": "Useful only as a workflow-template hypothesis until real signal evidence is attached.",
                "why_us": "Could win by providing privacy-aware implementation assets, but needs demand validation.",
                "next_research_tasks": ["Validate query demand", "Sample SERP difficulty", "Check AI answer gaps", "Collect official HRIS/workspace docs"]
            },
            {
                "candidate_id": "sig-2026-05-12-002",
                "working_topic": "AI workflow template for invoice approval routing",
                "signal_status": "staging_example_from_pipeline_validation_not_real_keyword_volume_verified",
                "observed_signals": [
                    {"source": "pipeline validation batch", "evidence": "Selected as finance-ops workflow-template hypothesis", "strength": "weak"}
                ],
                "query_patterns": ["ai workflow template for invoice approval routing", "invoice approval routing workflow template", "accounts payable ai workflow checklist"],
                "intent": "workflow template",
                "demand_signal": {"score": 2, "rationale": "Plausible long-tail operational need, but no real volume/trend evidence attached yet."},
                "capture_likelihood": {"score": 3, "rationale": "Specific operational workflow may be capturable if SERP lacks practical templates."},
                "geo_likelihood": {"score": 4, "rationale": "Decision rules and checklist format are suitable for AI answer extraction."},
                "evidence_availability": {"score": 3, "rationale": "Official invoice/AP platform docs exist; avoid financial advice."},
                "strategic_fit": {"score": 3, "rationale": "Fits business operations workflow cluster if demand is confirmed."},
                "risk": {"veto": "pass", "flags": ["vendor data privacy", "avoid financial advice"]},
                "recommended_action": "watch_or_research_more_before_publish_pool",
                "why_now": "Use as a validation example, not as a confirmed traffic target yet.",
                "why_us": "Could win with a clear routing/checklist asset if SERP is weak.",
                "next_research_tasks": ["Validate query demand", "Inspect SERP template quality", "Attach official AP/invoicing sources"]
            }
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Build a signal-led SEO/GEO strategy meeting pack before content production.")
    parser.add_argument("--input", default="factory/strategy/signal-led-opportunity-input.json")
    parser.add_argument("--out-dir", default="factory/strategy/meetings/2026-05-12-signal-led-mvp")
    args = parser.parse_args()
    in_path = root / args.input
    if not in_path.exists():
        write_json(in_path, default_input())
    data = load_json(in_path, default_input())
    out_dir = root / args.out_dir
    candidates = []
    for c in data.get("candidates", []):
        enriched = dict(c)
        enriched["strategy_score"] = score_candidate(c)
        candidates.append(enriched)
    ranked = sorted(candidates, key=lambda x: x["strategy_score"]["total"], reverse=True)
    artifact = {
        "status": "strategy_meeting_pack_not_content_production_approval",
        "production_publish_allowed": False,
        "purpose": data.get("strategy_goal"),
        "target_site": data.get("target_site"),
        "target_region_language": data.get("target_region_language"),
        "signal_sources_to_use_next": data.get("signal_sources_to_use_next", []),
        "decision_rule": "Only candidates with credible demand signals, capture likelihood, GEO fit, evidence path, and no risk veto should enter the opportunity pool. Public-signal scan candidates need at least one medium/strong observed signal; weak/noisy mentions stay in watch/research.",
        "ranked_candidates": ranked,
        "recommended_pool": [c for c in ranked if c["strategy_score"]["recommendation"] == "recommend_for_opportunity_pool"],
        "watch_or_research_more": [c for c in ranked if c["strategy_score"]["recommendation"] == "watch_or_research_more"],
        "defer_or_reject": [c for c in ranked if c["strategy_score"]["recommendation"] in {"defer", "reject"}],
    }
    write_json(out_dir / "strategy_meeting_pack.json", artifact)
    lines = [
        "# Signal-led SEO/GEO strategy meeting pack",
        "",
        "Status: `strategy_meeting_pack_not_content_production_approval`  ",
        "Production publish allowed: `false`",
        "",
        f"Purpose: {artifact['purpose']}",
        "",
        "## Important correction",
        "",
        "The factory should not start by inventing a content family. It should first gather traffic/market/AI-answer signals, score whether traffic is capturable, then approve an opportunity pool. Existing AI workflow-template pages are now treated as pipeline-validation examples unless real signal evidence is attached.",
        "",
        "## Signal sources to use next",
        "",
        *[f"- {x}" for x in artifact["signal_sources_to_use_next"]],
        "",
        "## Decision rule",
        "",
        artifact["decision_rule"],
        "",
        "## Ranked candidates",
        "",
    ]
    for c in ranked:
        s = c["strategy_score"]
        lines.extend([
            f"### {c['working_topic']}",
            "",
            f"Candidate ID: `{c['candidate_id']}`  ",
            f"Signal status: `{c.get('signal_status', 'unknown')}`  ",
            f"Score: `{s['total']}` · Tier: `{s['tier']}` · Recommendation: `{s['recommendation']}`",
            "",
            f"Intent: {c.get('intent')}",
            "",
            "Query patterns:",
            *[f"- `{q}`" for q in c.get("query_patterns", [])],
            "",
            "Observed signals:",
            *[f"- {sig.get('source')}: {sig.get('evidence')} ({sig.get('strength')})" for sig in c.get("observed_signals", [])],
            "",
            "Why now:",
            f"- {c.get('why_now')}",
            "",
            "Why us / capture path:",
            f"- {c.get('why_us')}",
            "",
            "Scoring rationale:",
            f"- Demand: {c.get('demand_signal', {}).get('score')} — {c.get('demand_signal', {}).get('rationale')}",
            f"- Capture: {c.get('capture_likelihood', {}).get('score')} — {c.get('capture_likelihood', {}).get('rationale')}",
            f"- GEO: {c.get('geo_likelihood', {}).get('score')} — {c.get('geo_likelihood', {}).get('rationale')}",
            f"- Evidence: {c.get('evidence_availability', {}).get('score')} — {c.get('evidence_availability', {}).get('rationale')}",
            f"- Strategic fit: {c.get('strategic_fit', {}).get('score')} — {c.get('strategic_fit', {}).get('rationale')}",
            "",
            "Risk/veto:",
            f"- Veto: `{c.get('risk', {}).get('veto')}`",
            *[f"- {x}" for x in c.get('risk', {}).get('flags', [])],
            "",
            "Next research tasks:",
            *[f"- {x}" for x in c.get("next_research_tasks", [])],
            "",
        ])
    write_md(out_dir / "strategy_meeting_pack.md", "\n".join(lines))
    print(json.dumps({"created": [str((out_dir / 'strategy_meeting_pack.json').relative_to(root)), str((out_dir / 'strategy_meeting_pack.md').relative_to(root))], "candidates": len(ranked), "recommended_pool": len(artifact['recommended_pool'])}, indent=2))


if __name__ == "__main__":
    main()
