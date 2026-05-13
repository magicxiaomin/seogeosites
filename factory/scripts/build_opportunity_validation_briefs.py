from pathlib import Path
import argparse
import json
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def md_link(item):
    return f"[{item.get('title') or item.get('url')}]({item.get('url')})"


def extract_domains(results):
    domains = []
    for r in results:
        url = r.get("url", "")
        if "://" in url:
            domain = url.split("://", 1)[1].split("/", 1)[0].replace("www.", "")
            if domain not in domains:
                domains.append(domain)
    return domains[:12]


def source_map(candidate):
    official = candidate.get("evidence_source_feasibility", {}).get("official_sources", [])
    return [
        {
            "title": s.get("title"),
            "url": s.get("url"),
            "role": infer_source_role(s.get("title", "") + " " + s.get("url", "")),
            "reachability": {
                "reachable": s.get("reachable"),
                "http_status": s.get("http_status"),
                "note": s.get("source_access_note", ""),
            },
            "production_use_policy": "candidate_official_source_needs_editorial_acceptance_before_publish",
        }
        for s in official
    ]


def infer_source_role(text):
    t = text.lower()
    if "help" in t or "support" in t:
        return "product documentation / help center source"
    if "blog" in t or "announcement" in t or "introducing" in t:
        return "official announcement / product status source"
    if "search central" in t or "developers" in t:
        return "search documentation / implementation guidance source"
    if "edge" in t or "comet" in t or "chatgpt" in t or "perplexity" in t:
        return "official product source"
    return "official or primary source"


def serp_gap_table(candidate):
    rows = []
    for obs in candidate.get("serp_observations", []):
        results = obs.get("results", [])
        competitor = [r for r in results if any(w in (r.get("title", "").lower()) for w in ["best", "vs", "review", "guide", "compared", "comparison"])]
        official = [r for r in results if any(d in r.get("url", "") for d in ["openai.com", "chatgpt.com", "perplexity.ai", "google.com", "microsoft.com", "github.com"])]
        rows.append({
            "query": obs.get("query"),
            "sample_source": obs.get("source"),
            "http_status": obs.get("http_status"),
            "observed_result_count": len(results),
            "dominant_result_domains": extract_domains(results),
            "official_or_primary_count": len(official),
            "comparison_or_review_count": len(competitor),
            "content_gap": infer_gap(obs.get("query", ""), official, competitor),
            "capture_note": "Use official-source-grounded explainers and decision tables; do not rewrite competitor roundups.",
        })
    return rows


def infer_gap(query, official, competitor):
    q = query.lower()
    if "vs" in q or "search" in q:
        return "SERP has explainers and product pages, but needs a current, source-backed comparison that separates product facts, evaluator criteria, and update notes."
    if "privacy" in q or "browser" in q or "agent" in q:
        return "SERP has lists/reviews and official product pages, but fewer neutral workflow, privacy, and safety checklists with explicit claim sourcing."
    return "SERP has mixed official, review, and glossary results; opportunity is a concise decision asset with evidence table and freshness policy."


def recommended_pages(candidate):
    cid = candidate.get("candidate_id")
    if "browsers" in cid:
        return [
            {"page": "What is an AI browser?", "intent": "definition + buyer/research orientation", "role": "pillar/supporting explainer", "production_gate": "verify official product set and current names"},
            {"page": "AI browser vs AI search engine", "intent": "comparison/decision", "role": "high-GEO comparison asset", "production_gate": "source-backed definitions and examples"},
            {"page": "Best AI browsers for research workflows", "intent": "evaluation", "role": "reviewable comparison page", "production_gate": "hands-on or clearly disclosed non-hands-on evaluation policy"},
            {"page": "AI browser privacy and safety checklist", "intent": "risk checklist", "role": "trust-building supporting page", "production_gate": "privacy/security claims reviewed"},
            {"page": "Perplexity Comet guide", "intent": "product-specific guide", "role": "supporting page", "production_gate": "official docs and product access confirmed"},
        ]
    return [
        {"page": "What is an AI search engine?", "intent": "definition + landscape", "role": "pillar explainer", "production_gate": "official-source examples only"},
        {"page": "Perplexity AI vs ChatGPT Search vs Google AI Mode", "intent": "comparison/decision", "role": "high-GEO comparison asset", "production_gate": "feature parity/current status verified"},
        {"page": "Answer engine optimization guide", "intent": "implementation", "role": "hub/supporting guide", "production_gate": "avoid unsupported ranking/citation promises"},
        {"page": "How AI answer engines cite sources", "intent": "evidence/source trust", "role": "source-trust page", "production_gate": "cite official docs or research; no black-box claims"},
        {"page": "SEO vs GEO vs AEO", "intent": "terminology comparison", "role": "glossary/comparison page", "production_gate": "define terms as industry usage, not universal standards"},
    ]


def build_brief(candidate):
    pages = recommended_pages(candidate)
    classification = "Balanced SEO+GEO" if candidate.get("validation_scores", {}).get("geo_likelihood") == "high" else "SEO-led"
    return {
        "candidate_id": candidate.get("candidate_id"),
        "topic": candidate.get("topic"),
        "status": "opportunity_validation_brief_not_content_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "production_publish_allowed": False,
        "classification": classification,
        "recommended_action": "approve_for_content_briefing_after_human_opportunity_pool_confirmation",
        "why_this_opportunity": [
            "It has visible public SERP evidence from the previous signal-led validation run.",
            "It sits at the intersection of traditional search intent and AI-answer-engine explainability, making it suitable for Balanced SEO+GEO testing.",
            "Official/primary sources are available enough to build evidence-backed briefs, but production claims still need editorial source acceptance.",
        ],
        "traffic_intents": ["definition", "comparison", "best/tools evaluation", "implementation checklist", "privacy/safety or trust caveat"],
        "serp_gap_table": serp_gap_table(candidate),
        "competitor_weakness_hypotheses": [
            "Roundups often optimize for affiliate-style rankings rather than source-backed definitions and update policy.",
            "Product-specific coverage can blur official status, review opinion, and speculative capability claims.",
            "Many explainers lack extractable tables, concise direct-answer blocks, source notes, and dated freshness logic for AI answer engines.",
        ],
        "official_source_map": source_map(candidate),
        "ai_answer_gap_sampling_checklist": candidate.get("ai_answer_gap_sampling", []),
        "recommended_cluster_shape": {
            "placement_decision": "new_cluster_in_existing_pilot_site",
            "cluster_or_hub": candidate.get("topic"),
            "why_not_new_site": "The opportunity fits the existing SEO/GEO factory pilot audience and does not require a separate brand, risk class, monetization model, or language/region.",
            "why_not_immediate_draft": "The current artifact is an opportunity validation brief; content briefs and drafts should follow only after opportunity-pool confirmation and source acceptance.",
            "first_candidate_pages_if_approved": pages,
        },
        "defer_or_reject_criteria": [
            "No confirmed search demand or community/competitor signal beyond noisy public mentions.",
            "Official sources cannot substantiate product status, feature claims, or safety/privacy statements.",
            "SERP is dominated by high-authority pages with no clear angle for a more useful, evidence-backed asset.",
            "The page would depend on copying competitor tests, unsupported claims, or rapidly stale speculation.",
        ],
        "next_workflow_step": "human_confirm_opportunity_pool_then_generate_content_briefs_and_source_acceptance_queue",
        "publish_readiness": "Needs Review",
    }


def brief_to_md(brief):
    lines = [
        f"# Opportunity Validation Brief — {brief['topic']}",
        "",
        f"Status: `{brief['status']}`  ",
        f"Classification: `{brief['classification']}`  ",
        f"Production publish allowed: `{str(brief['production_publish_allowed']).lower()}`  ",
        f"Publish-readiness: `{brief['publish_readiness']}`",
        "",
        "## 1. Why this opportunity",
    ]
    lines += [f"- {x}" for x in brief["why_this_opportunity"]]
    lines += ["", "## 2. Traffic intent targets"]
    lines += [f"- `{x}`" for x in brief["traffic_intents"]]
    lines += ["", "## 3. SERP gap table"]
    lines += ["| Query | Results | Official/primary | Comparison/review | Gap |", "|---|---:|---:|---:|---|"]
    for row in brief["serp_gap_table"]:
        lines.append(f"| {row['query']} | {row['observed_result_count']} | {row['official_or_primary_count']} | {row['comparison_or_review_count']} | {row['content_gap']} |")
    lines += ["", "## 4. Competitor/content weaknesses to verify"]
    lines += [f"- {x}" for x in brief["competitor_weakness_hypotheses"]]
    lines += ["", "## 5. Official source map"]
    for s in brief["official_source_map"]:
        http = s["reachability"].get("http_status", "n/a")
        reachable = s["reachability"].get("reachable")
        lines.append(f"- [{s['title']}]({s['url']}) — {s['role']}; reachable: `{reachable}`, HTTP: `{http}`; policy: `{s['production_use_policy']}`")
    lines += ["", "## 6. AI answer gap sampling checklist"]
    for g in brief["ai_answer_gap_sampling_checklist"]:
        lines.append(f"- {g.get('prompt')} — `{g.get('sampling_status')}`")
    lines += ["", "## 7. Recommended cluster/page shape"]
    cs = brief["recommended_cluster_shape"]
    lines += [
        f"- Placement decision: `{cs['placement_decision']}`",
        f"- Cluster/hub: `{cs['cluster_or_hub']}`",
        f"- Why not new site: {cs['why_not_new_site']}",
        f"- Why not immediate draft: {cs['why_not_immediate_draft']}",
        "",
        "### First candidate pages if approved",
    ]
    for p in cs["first_candidate_pages_if_approved"]:
        lines.append(f"- **{p['page']}** — intent: `{p['intent']}`; role: `{p['role']}`; gate: {p['production_gate']}")
    lines += ["", "## 8. Defer/reject criteria"]
    lines += [f"- {x}" for x in brief["defer_or_reject_criteria"]]
    lines += ["", "## 9. Next workflow step", f"`{brief['next_workflow_step']}`"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="factory/strategy/meetings/2026-05-12-opportunity-validation-v1/validated_opportunity_pool.json")
    parser.add_argument("--out-dir", default="factory/strategy/meetings/2026-05-12-opportunity-brief-pack-v1")
    parser.add_argument("--public-dir", default="public")
    args = parser.parse_args()
    data = load_json(root / args.input)
    out = root / args.out_dir
    public = root / args.public_dir
    out.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    briefs = [build_brief(c) for c in data.get("candidates", [])]
    pack = {
        "status": "opportunity_validation_brief_pack_not_content_or_publish_approval",
        "production_publish_allowed": False,
        "publish_readiness": "Needs Review",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_validation_input": args.input,
        "briefs": briefs,
        "recommended_batch_decision": "confirm_or_edit_opportunity_pool_before_content_briefs",
    }
    write_json(out / "opportunity_validation_brief_pack.json", pack)
    write_json(public / "batch-2026-05-12-opportunity_validation_brief_pack.json", pack)

    index_lines = [
        "# Opportunity Validation Brief Pack — v1",
        "",
        "Status: `opportunity_validation_brief_pack_not_content_or_publish_approval`  ",
        "Production publish allowed: `false`  ",
        "Publish-readiness: `Needs Review`",
        "",
        "This pack translates the validated opportunity pool into decision-ready briefs. It is not content approval and does not authorize production publishing.",
        "",
        "## Briefs",
    ]
    for b in briefs:
        slug = b["candidate_id"].replace("validated-", "")
        md = brief_to_md(b)
        write_json(out / f"{slug}-validation_brief.json", b)
        write_json(public / f"batch-2026-05-12-{slug}-validation_brief.json", b)
        (out / f"{slug}-validation_brief.md").write_text(md, encoding="utf-8")
        (public / f"batch-2026-05-12-{slug}-validation_brief.md").write_text(md, encoding="utf-8")
        index_lines.append(f"- [{b['topic']}](batch-2026-05-12-{slug}-validation_brief.md) — `{b['classification']}` / `{b['publish_readiness']}`")
    index_lines += ["", "## Recommended decision", "`confirm_or_edit_opportunity_pool_before_content_briefs`"]
    (out / "opportunity_validation_brief_pack.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    (public / "batch-2026-05-12-opportunity_validation_brief_pack.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(json.dumps({"created": str(out.relative_to(root)), "briefs": len(briefs)}, indent=2))


if __name__ == "__main__":
    main()
