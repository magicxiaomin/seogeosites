from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]


def load_json(path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def risk_result(flags):
    joined = " ".join(flags).lower()
    if any(term in joined for term in ["medical", "legal advice", "investment", "high risk", "ymyl"]):
        return "defer_or_reject_until_expert_review"
    if flags:
        return "allow_staging_needs_review"
    return "allow_staging_low_risk"


def infer_query_patterns(topic):
    lower = topic.lower()
    patterns = [lower]
    if lower.startswith("ai workflow template for "):
        task = lower.replace("ai workflow template for ", "")
        patterns.extend([
            f"{task} ai workflow template",
            f"how to use ai for {task}",
            f"{task} workflow checklist",
        ])
    else:
        patterns.extend([f"{lower} template", f"{lower} checklist"])
    return patterns


def strategy_for(opp, classification, placement, evidence, source_verification, qa_page):
    topic = opp["topic"]
    flags = opp.get("risk_flags", [])
    cluster = opp.get("recommended_cluster", "")
    entities = opp.get("entities", [])
    accepted_sources = [
        {
            "title": s.get("title") or s.get("url"),
            "url": s.get("url"),
            "status": s.get("status"),
            "reachable": s.get("reachable"),
            "http_status": s.get("http_status"),
            "supports_claims": s.get("supports_claims", []),
        }
        for s in source_verification.get("candidate_sources", [])
        if s.get("status") == "accepted"
    ]
    seo_score = classification.get("seo_score")
    geo_score = classification.get("geo_score")
    risk_fit_score = classification.get("risk_fit_score")
    return {
        "opportunity_id": opp["id"],
        "topic": topic,
        "status": "staging_strategy_explanation_not_publish_approval",
        "why_create_this_page": [
            f"The topic maps to a concrete {opp.get('search_intent', 'informational')} intent rather than a broad AI trend article.",
            f"It belongs inside the '{cluster}' cluster, so it can compound topical coverage with related workflow-template pages.",
            "The page can be useful as a reusable implementation asset: inputs, workflow steps, prompt block, expected outputs, human QA checks, and source notes.",
        ],
        "topic_signal_type": "staging_strategy_hypothesis_long_tail_not_external_keyword_volume_verified",
        "query_patterns_to_validate": infer_query_patterns(topic),
        "search_intent": {
            "type": opp.get("search_intent"),
            "user_need": f"Find a practical, reviewable template for {topic.replace('AI workflow template for ', '')}.",
        },
        "seo_rationale": {
            "score": seo_score,
            "reasoning": [
                "Long-tail workflow/template query with clear task intent.",
                "Can be internally linked from the AI workflow templates hub and adjacent operational pages.",
                "Search value still needs validation with real query data before production prioritization.",
            ],
        },
        "geo_rationale": {
            "score": geo_score,
            "reasoning": [
                "Structured answer format is extractable by AI answer engines: direct answer, definition, steps, FAQ, and source notes.",
                f"Explicit entities improve summarizability: {', '.join(entities) if entities else 'entities pending' }.",
                "Evidence/source notes make the page more cite-worthy than generic AI productivity commentary.",
            ],
        },
        "risk_assessment": {
            "risk_fit_score": risk_fit_score,
            "result": risk_result(flags),
            "risk_flags": flags,
            "veto_result": "passed_for_staging_only" if risk_result(flags).startswith("allow") else "not_passed",
            "production_review_required": True,
        },
        "site_placement": {
            "decision": placement.get("recommendation"),
            "target_site": placement.get("target_site"),
            "target_section": placement.get("target_section"),
            "target_page_type": placement.get("target_page_type"),
            "why_not_new_site": placement.get("reasoning", {}).get("why_not_new_site"),
            "why_not_existing_page_update": placement.get("reasoning", {}).get("why_not_existing_page_update"),
        },
        "evidence_plan": {
            "required_evidence_level": classification.get("required_evidence_level"),
            "source_plan": evidence.get("source_plan", []),
            "accepted_staging_sources": accepted_sources,
            "claim_policy": evidence.get("claim_policy"),
            "forbidden_claims": evidence.get("forbidden_claims", []),
        },
        "publish_status": {
            "staging": "approved_for_preview" if qa_page.get("staging_approved") else "pending",
            "production": qa_page.get("qa_status") or qa_page.get("status") or "Needs Review",
            "required_before_publish": qa_page.get("required_before_publish", []),
            "production_publish_allowed": False,
        },
        "what_would_make_this_stronger": [
            "Validate actual search demand with Search Console, keyword tools, SERP sampling, or community-question evidence.",
            "Record competitor/answer-engine gaps rather than using only a strategy hypothesis.",
            "Add reviewer-approved examples and policies for the specific workflow before production publishing.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Build human-readable opportunity strategy review artifacts for a factory run.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    args = parser.parse_args()
    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    out = run / "outputs"
    opportunities = load_json(run / "inputs" / "opportunity_pool.json", [])
    classifications = {x["opportunity_id"]: x for x in load_json(out / "strategy_classification.json", [])}
    batch = load_json(out / "batch_publish_report.json", {"generated_pages": []})
    batch_pages = {x["opportunity_id"]: x for x in batch.get("generated_pages", [])}
    reviews = []
    for opp in opportunities:
        oid = opp["id"]
        page_dir = out / "pages" / oid
        review = strategy_for(
            opp,
            classifications.get(oid, {}),
            load_json(page_dir / "site_placement_decision.json", {}),
            load_json(page_dir / "evidence_plan.json", {}),
            load_json(page_dir / "source_verification.json", {"candidate_sources": []}),
            batch_pages.get(oid, load_json(page_dir / "qa_report.json", {})),
        )
        reviews.append(review)
    artifact = {
        "run": str(run.relative_to(root)),
        "status": "strategy_review_for_staging_batch_not_publish_approval",
        "production_publish_allowed": False,
        "note": "This explains why each staging page exists. Topic demand is a hypothesis unless external signal fields are later populated.",
        "batch_role": "pipeline_validation_batch_not_real_traffic_opportunity_pool",
        "upstream_strategy_requirement": "Before future content production, run signal-led opportunity discovery and a strategy meeting pack using demand, capture likelihood, GEO fit, evidence availability, and risk veto.",
        "cluster_strategy": {
            "hub": "ai-workflow-templates-for-business-teams",
            "thesis": "This cluster is a low/medium-risk pipeline-validation fixture for exercising the factory. It is not yet the selected traffic-led strategy.",
            "selection_model": "risk veto + SEO/GEO classification + evidence availability + existing-site placement fit",
            "current_limitation": "This batch uses strategy-hypothesis long-tail topics; it does not yet include verified keyword volume, trend-source data, SERP observations, competitor gaps, or AI-answer-gap sampling.",
        },
        "opportunities": reviews,
    }
    write_json(out / "opportunity_strategy_review.json", artifact)

    lines = [
        "# Opportunity strategy review — staging batch",
        "",
        "Status: `strategy_review_for_staging_batch_not_publish_approval`  ",
        "Production publish allowed: `false`",
        "",
        "This artifact answers: why make each page, what intent it targets, how SEO/GEO/risk were judged, why it sits in the current site/cluster, and what still needs human review.",
        "",
        "## Batch role correction",
        "",
        "This is a `pipeline_validation_batch_not_real_traffic_opportunity_pool`. It proves the factory can process a cluster, but future production candidates should come from a signal-led strategy meeting pack first.",
        "",
        "## Cluster thesis",
        "",
        f"Hub: `{artifact['cluster_strategy']['hub']}`",
        "",
        artifact["cluster_strategy"]["thesis"],
        "",
        f"Selection model: {artifact['cluster_strategy']['selection_model']}",
        "",
        f"Current limitation: {artifact['cluster_strategy']['current_limitation']}",
        "",
    ]
    for r in reviews:
        lines.extend([
            f"## {r['topic']}",
            "",
            f"Opportunity ID: `{r['opportunity_id']}`  ",
            f"Classification: `{classifications.get(r['opportunity_id'], {}).get('classification', 'unknown')}`  ",
            f"SEO score: `{r['seo_rationale']['score']}` · GEO score: `{r['geo_rationale']['score']}` · Risk fit: `{r['risk_assessment']['risk_fit_score']}`  ",
            f"Production status: `{r['publish_status']['production']}`",
            "",
            "### Why create this page",
            *[f"- {x}" for x in r["why_create_this_page"]],
            "",
            "### Search intent and query patterns to validate",
            f"- Intent: {r['search_intent']['type']}",
            f"- User need: {r['search_intent']['user_need']}",
            *[f"- `{x}`" for x in r["query_patterns_to_validate"]],
            "",
            "### SEO rationale",
            *[f"- {x}" for x in r["seo_rationale"]["reasoning"]],
            "",
            "### GEO rationale",
            *[f"- {x}" for x in r["geo_rationale"]["reasoning"]],
            "",
            "### Risk and veto result",
            f"- Result: `{r['risk_assessment']['result']}`",
            f"- Veto: `{r['risk_assessment']['veto_result']}`",
            *[f"- Risk flag: {x}" for x in (r['risk_assessment']['risk_flags'] or ['none recorded'])],
            "",
            "### Site placement",
            f"- Decision: `{r['site_placement']['decision']}`",
            f"- Target site: `{r['site_placement']['target_site']}`",
            f"- Target section: `{r['site_placement']['target_section']}`",
            f"- Why not a new site: {r['site_placement']['why_not_new_site']}",
            f"- Why not an existing-page update: {r['site_placement']['why_not_existing_page_update']}",
            "",
            "### Evidence plan",
            *[f"- Required source path: {x}" for x in r['evidence_plan']['source_plan']],
            *[f"- Accepted staging source: [{s['title']}]({s['url']})" for s in r['evidence_plan']['accepted_staging_sources']],
            "",
            "### Required before production publish",
            *[f"- {x}" for x in (r['publish_status']['required_before_publish'] or ['Human review before production publish'])],
            "",
            "### What would make this stronger",
            *[f"- {x}" for x in r["what_would_make_this_stronger"]],
            "",
        ])
    write_md(out / "opportunity_strategy_review.md", "\n".join(lines))
    print(json.dumps({"created": [str((out / 'opportunity_strategy_review.json').relative_to(root)), str((out / 'opportunity_strategy_review.md').relative_to(root))], "opportunities": len(reviews), "production_publish_allowed": False}, indent=2))


if __name__ == "__main__":
    main()
