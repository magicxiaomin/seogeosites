from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
run = root / "factory/runs/sample"
(run / "inputs").mkdir(parents=True, exist_ok=True)
(run / "outputs").mkdir(parents=True, exist_ok=True)
(root / "content/sites/productivity-ai-pilot/pages").mkdir(parents=True, exist_ok=True)

opps = [
    {
        "id": "opp-001",
        "topic": "AI meeting notes workflow for small remote teams",
        "search_intent": "informational/commercial investigation",
        "geo_scenario": "direct answer + workflow extraction",
        "risk_flags": ["low YMYL", "tool claims need source support"],
        "recommended_cluster": "AI Meeting Workflows",
    },
    {
        "id": "opp-002",
        "topic": "AI legal advice for employee termination",
        "search_intent": "legal advice",
        "geo_scenario": "answer engine citation potential",
        "risk_flags": ["high YMYL/legal", "jurisdiction-specific"],
        "recommended_cluster": "AI HR Workflows",
    },
    {
        "id": "opp-003",
        "topic": "Best AI coupon generators for ecommerce stores",
        "search_intent": "commercial",
        "geo_scenario": "list extraction",
        "risk_flags": ["affiliate bias risk", "thin roundup risk"],
        "recommended_cluster": "AI Ecommerce Tools",
    },
]
(run / "inputs/opportunity_pool.json").write_text(json.dumps(opps, indent=2), encoding="utf-8")


def classify(o):
    risks = " ".join(o["risk_flags"]).lower()
    topic = o["topic"].lower()
    seo = 4 if "meeting" in topic else 3
    geo = 5 if "meeting" in topic else 3
    risk = 1 if "legal" in risks or "high ymyl" in risks else (3 if "thin" in risks else 5)
    if risk <= 2:
        cls, rec = "Reject", "no-go: risk veto"
    elif seo >= 4 and geo >= 4:
        cls, rec = "Balanced SEO+GEO", "go: MVP pilot candidate"
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


strategy = [classify(o) for o in opps]
(run / "outputs/strategy_classification.json").write_text(json.dumps(strategy, indent=2), encoding="utf-8")
selected = opps[0]

evidence = {
    "opportunity_id": selected["id"],
    "source_plan": [
        "Zoom official support/docs",
        "Google Meet official help docs",
        "Notion/Google Docs docs",
        "Vendor feature/pricing pages only for factual claims",
        "Community questions as intent signals only",
    ],
    "entity_map": [
        "remote teams",
        "meeting transcripts",
        "AI summarization",
        "Zoom",
        "Google Meet",
        "Notion",
        "action items",
        "decision log",
    ],
    "claim_policy": "Make workflow claims only when grounded in official docs or labeled as editorial guidance.",
    "forbidden_claims": [
        "guaranteed productivity gains",
        "unverified tool feature claims",
        "legal/compliance promises",
    ],
    "evidence_requirements": [
        "cite official docs for platform capabilities",
        "include dated criteria",
        "separate factual claims from recommendations",
    ],
    "update_requirements": "Review quarterly or when major meeting-tool features/pricing change.",
    "human_review_triggers": ["new tool claims without official source", "privacy/security claims"],
}
(run / "outputs/evidence_plan.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
source_verification = {
    "opportunity_id": selected["id"],
    "source_items": [
        {
            "source": source,
            "is_concrete_url": str(source).startswith(("http://", "https://")),
            "verification_status": "placeholder_requires_replacement",
            "required_before_pass": True,
        }
        for source in evidence["source_plan"]
    ],
    "summary": {
        "total_sources": len(evidence["source_plan"]),
        "concrete_urls": 0,
        "placeholders": len(evidence["source_plan"]),
        "all_sources_publish_ready": False,
    },
    "review_flags": {
        "missing_concrete_source_urls": True,
        "privacy_review_required": True,
        "copyright_review_required": False,
        "monetization_review_required": False,
        "high_risk_topic": False,
    },
}
(run / "outputs/source_verification.json").write_text(json.dumps(source_verification, indent=2), encoding="utf-8")

placement = {
    "opportunity_id": selected["id"],
    "recommendation": "new_cluster_in_existing_site",
    "target_site": "productivity-ai-pilot",
    "target_section": "AI Meeting Workflows",
    "target_page_type": "pillar_page",
    "fit_scores": {
        "audience_fit": 5,
        "topical_fit": 5,
        "entity_fit": 5,
        "intent_fit": 4,
        "internal_link_fit": 4,
        "trust_fit": 4,
        "risk_fit": 5,
        "monetization_fit": 4,
        "language_region_fit": 5,
        "scale_potential": 3,
    },
    "reasoning": {
        "summary": "Natural extension of the AI productivity pilot site.",
        "why_not_new_site": "No distinct audience, risk class, or brand posture requiring a standalone site.",
        "why_not_existing_page_update": "No existing page in this repo yet.",
    },
    "human_review_required": False,
}
(run / "outputs/site_placement_decision.json").write_text(json.dumps(placement, indent=2), encoding="utf-8")

brief = {
    "cluster_brief": {
        "cluster_name": "AI Meeting Workflows",
        "pillar_page": "/ai-meeting-notes-workflow/",
        "supporting_pages": [
            "/ai-meeting-notes-action-items/",
            "/ai-meeting-notes-decision-log/",
            "/zoom-meeting-summary-workflow/",
        ],
        "internal_link_plan": ["homepage -> pillar", "pillar -> supporting pages", "supporting pages -> pillar"],
        "geo_structure_requirements": [
            "direct answer block",
            "definition box",
            "step-by-step workflow",
            "FAQ",
            "claim/evidence table",
        ],
        "schema_plan": ["Article", "FAQPage", "BreadcrumbList"],
    },
    "page_brief": {
        "page_title": "AI Meeting Notes Workflow for Small Remote Teams",
        "slug": "ai-meeting-notes-workflow",
        "search_intent": "Learn how to set up a practical AI meeting notes workflow",
        "direct_answer_block": "A reliable AI meeting notes workflow captures the transcript, summarizes decisions and action items, routes notes to a shared workspace, and includes a human review step for important meetings.",
        "outline": [
            "What the workflow is",
            "Recommended workflow",
            "Evidence and source notes",
            "Privacy and trust checklist",
            "FAQ",
        ],
        "faq_questions": [
            "What should AI meeting notes include?",
            "Do AI meeting notes need human review?",
            "Where should action items go?",
        ],
        "source_notes": evidence["source_plan"],
        "update_notes": [evidence["update_requirements"]],
    },
}
(run / "outputs/content_brief.json").write_text(json.dumps(brief, indent=2), encoding="utf-8")

md = f'''---
title: "{brief['page_brief']['page_title']}"
slug: "{brief['page_brief']['slug']}"
site: "productivity-ai-pilot"
status: "staging-draft"
geo_classification: "Balanced SEO+GEO"
last_reviewed: "2026-05-12"
---

# {brief['page_brief']['page_title']}

## Direct answer

{brief['page_brief']['direct_answer_block']}

## What this workflow is

An AI meeting notes workflow is a repeatable process for turning a live meeting into a reviewed knowledge asset: transcript, summary, decisions, action items, owners, and follow-up location.

## Recommended workflow

1. Capture the meeting transcript using an approved meeting platform or note-taking tool.
2. Generate a first-pass summary focused on decisions, blockers, and action items.
3. Separate factual notes from interpretation or recommendations.
4. Route action items to the team's task system and decisions to a shared decision log.
5. Review important or sensitive meetings before sharing broadly.
6. Update the team's template when recurring errors appear.

## Evidence and source notes

This staging draft should be checked against official platform documentation before publication. Community questions can inform reader intent, but should not be used as factual evidence for tool capabilities.

## Privacy and trust checklist

- Confirm whether the meeting can be transcribed.
- Avoid sending sensitive meetings to unapproved tools.
- Label AI-generated summaries until reviewed.
- Keep a record of who reviewed high-impact notes.

## FAQ

### What should AI meeting notes include?

They should include a short summary, decisions, action items with owners, unresolved questions, and links to relevant source material.

### Do AI meeting notes need human review?

For routine low-risk meetings, light review may be enough. For customer, legal, finance, hiring, or strategy meetings, human review should be required before the notes are treated as authoritative.

### Where should action items go?

Action items should move into the team's normal task system rather than staying only in a meeting summary.
'''
(root / "content/sites/productivity-ai-pilot/pages/ai-meeting-notes-workflow.md").write_text(md, encoding="utf-8")

qa = {
    "page": "content/sites/productivity-ai-pilot/pages/ai-meeting-notes-workflow.md",
    "status": "Needs Review",
    "checks": {
        "seo_quality": "Pass",
        "content_usefulness": "Pass",
        "evidence_source_integrity": "Needs Review: official URLs not verified in sample run",
        "geo_readiness": "Pass",
        "anti_spam_scaled_abuse": "Pass",
        "technical_publishing": "Pass",
    },
    "blockers": [],
    "required_before_publish": [
        "Replace source-plan placeholders with concrete official URLs",
        "Human review privacy/security wording before production",
    ],
}
(run / "outputs/qa_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
print("Sample SEO/GEO pipeline generated.")
