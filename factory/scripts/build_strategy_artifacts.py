from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
run = root / "factory/runs/pilot-001"
out = run / "outputs"
content_dir = root / "content/sites/productivity-ai-pilot/pages"

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def write_md(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")

batch = json.loads((out / "batch_publish_report.json").read_text(encoding="utf-8"))
pages = batch["generated_pages"]

blueprint = {
    "site_id": "productivity-ai-pilot",
    "status": "staging_blueprint_not_production_publish",
    "production_publish_allowed": False,
    "working_brand_posture": "Practical AI workflow templates for operations, support, sales, content, and reporting teams.",
    "primary_audience": ["operators", "founders", "team leads", "support/sales/content managers"],
    "editorial_promise": "Evidence-backed, privacy-aware, implementation-ready AI workflow guides with clear source notes and review gates.",
    "topical_scope": ["AI workflow templates", "team productivity automation", "safe prompt/process design", "source-backed tool-context guides"],
    "out_of_scope": ["medical/legal/financial advice", "guaranteed ROI claims", "competitor rewrites", "private-data automation without review", "mass programmatic publishing"],
    "required_trust_pages": ["homepage", "about/trust", "editorial policy", "source and update policy", "contact", "privacy/disclosure note if monetized"],
    "initial_cluster": {
        "hub_slug": "ai-workflow-templates-for-business-teams",
        "supporting_pages": [{"topic": p["topic"], "slug": p["slug"], "status": p["qa_status"]} for p in pages]
    },
    "production_blockers": ["final brand/domain decision", "human editorial review", "publish-batch approval", "trust pages not finalized", "analytics/search-console hooks not configured"],
}
write_json(out / "site_blueprint.json", blueprint)
write_md(out / "site_blueprint.md", f"""
# Site blueprint — staging only

Status: `staging_blueprint_not_production_publish`  
Production publish allowed: `false`

## Working brand/entity posture

{blueprint['working_brand_posture']}

## Primary audience

{chr(10).join('- ' + x for x in blueprint['primary_audience'])}

## Editorial promise

{blueprint['editorial_promise']}

## Topical scope

{chr(10).join('- ' + x for x in blueprint['topical_scope'])}

## Out of scope

{chr(10).join('- ' + x for x in blueprint['out_of_scope'])}

## Required trust pages before production

{chr(10).join('- ' + x for x in blueprint['required_trust_pages'])}

## Initial cluster

Hub slug: `{blueprint['initial_cluster']['hub_slug']}`

{chr(10).join('- ' + p['topic'] + ' — `' + p['slug'] + '`' for p in blueprint['initial_cluster']['supporting_pages'])}

## Production blockers

{chr(10).join('- ' + x for x in blueprint['production_blockers'])}
""")

opportunity_template = {
    "candidate_id": "opp-YYYYMMDD-001",
    "seed_theme": "",
    "working_topic": "",
    "search_intent": "informational | commercial-investigation | comparison | template-download | troubleshooting",
    "geo_scenario": "direct-answer | tool-selection | workflow-design | troubleshooting | checklist",
    "signals": {
        "keyword_or_question_sources": [],
        "serp_observations": [],
        "competitor_structures_observed": [],
        "community_questions": [],
        "official_sources_available": [],
        "sampled_ai_answer_gaps": []
    },
    "risk_flags": {
        "privacy_review_required": False,
        "copyright_review_required": False,
        "monetization_review_required": False,
        "high_risk_topic": False
    },
    "classification_inputs": {"seo_score_1_to_5": None, "geo_score_1_to_5": None, "risk_score_1_to_5": None, "evidence_availability_1_to_5": None},
    "recommended_cluster": "",
    "placement_recommendation": "existing_page_update | new_supporting_page | new_cluster_in_existing_site | defer | reject"
}
write_json(root / "factory/templates/opportunity_discovery_template.json", opportunity_template)

scoring_template = {
    "risk_veto": {"reject_if": ["unsupported YMYL advice", "copyright/IP-heavy rewriting", "blind scraping dependency", "scaled-content-abuse pattern", "no credible source path"]},
    "classifications": ["SEO-led", "GEO-led", "Balanced SEO+GEO", "Defer", "Reject"],
    "balanced_seo_geo_default": {"seo_min": 4, "geo_min": 4, "risk_max": 3, "evidence_min": 3},
    "required_output_fields": ["classification", "go_no_go", "evidence_level", "human_review_triggers", "site_placement_recommendation"]
}
write_json(root / "factory/templates/opportunity_scoring_template.json", scoring_template)

internal_link_map = {
    "hub": "ai-workflow-templates-for-business-teams",
    "rules": ["hub links to every supporting page", "supporting pages link back to hub", "supporting pages cross-link only when intent overlap is natural"],
    "links": [{"from": "ai-workflow-templates-for-business-teams", "to": p["slug"], "anchor": p["topic"]} for p in pages] + [{"from": p["slug"], "to": "ai-workflow-templates-for-business-teams", "anchor": "AI workflow templates for business teams"} for p in pages]
}
write_json(out / "internal_link_map.json", internal_link_map)

hub_md = """---
title: "AI Workflow Templates for Business Teams"
slug: "ai-workflow-templates-for-business-teams"
site: "productivity-ai-pilot"
status: "staging-draft"
geo_classification: "Balanced SEO+GEO"
last_reviewed: "2026-05-12"
---

# AI Workflow Templates for Business Teams

## Direct answer

This staging hub organizes practical AI workflow templates for common business-team tasks. Each supporting page should provide a reusable prompt block, step-by-step workflow, accepted source notes, and production review flags before any public publishing.

## How to use this hub

1. Pick the workflow that matches the team task.
2. Review inputs and data-handling constraints before using AI tools.
3. Use the prompt block as a starting point, not as unreviewed automation.
4. Check accepted sources and editorial guardrails on each supporting page.
5. Keep production publishing blocked until human review approves the batch.

## Supporting workflow templates

"""
for p in pages:
    hub_md += f"- [{p['topic']}](/{p['slug']}.html) — status: {p['qa_status']}.\n"
hub_md += """

## Editorial guardrails

- Keep sensitive data out of AI prompts unless the tool and data-handling model are approved.
- Treat workflow advice as editorial guidance unless directly supported by accepted sources.
- Do not present tool outputs, sales results, or productivity gains as guaranteed outcomes.
- Do not use this hub for production publishing until the explicit publish batch is approved.

## Publish-readiness

Staging preview is approved for review. Production publish remains blocked.
"""
write_md(content_dir / "ai-workflow-templates-for-business-teams.md", hub_md)

measurement = {
    "status": "template_only_no_production_data_yet",
    "pre_publish_checks": ["content quality pass", "source coverage pass", "human review decision recorded", "robots/indexing settings reviewed for production"],
    "post_publish_metrics": ["indexing status", "impressions", "clicks", "rank movement", "engagement proxy", "AI answer coverage sample", "source freshness", "template QA failure rate"],
    "feedback_decisions": ["continue", "modify", "pause", "scale", "stop"],
    "sampled_geo_prompts": [
        "What is a safe AI workflow for turning meeting notes into action items?",
        "How should a support team use AI to triage tickets without exposing private data?",
        "What should be included in an AI weekly business reporting workflow?"
    ]
}
write_json(out / "measurement_plan.json", measurement)
write_md(out / "measurement_plan.md", """
# Measurement and feedback plan

Status: `template_only_no_production_data_yet`

## Pre-publish checks

- Content quality pass
- Source coverage pass
- Human review decision recorded
- Production robots/indexing settings reviewed

## Post-publish metrics

- Indexing status
- Impressions/clicks/rank movement
- Engagement proxy
- AI answer coverage sample
- Source freshness
- Template QA failure rate

## Feedback decisions

- continue
- modify
- pause
- scale
- stop

## Sample GEO prompts

- What is a safe AI workflow for turning meeting notes into action items?
- How should a support team use AI to triage tickets without exposing private data?
- What should be included in an AI weekly business reporting workflow?
""")

print(json.dumps({"created": ["site_blueprint", "opportunity_templates", "internal_link_map", "hub_page", "measurement_plan"], "production_publish_allowed": False}, indent=2))
