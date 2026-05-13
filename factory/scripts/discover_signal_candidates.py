from pathlib import Path
import argparse
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[2]

SEEDS = [
    {
        "theme": "AI browsers and agent browsers",
        "queries": ["AI browser", "agent browser", "ChatGPT Atlas", "Perplexity Comet", "browser agent"],
        "default_intent": "comparison and product decision",
    },
    {
        "theme": "AI meeting recorders and meeting notes",
        "queries": ["AI meeting recorder", "AI meeting notes", "meeting transcription AI", "Granola AI", "Fathom AI"],
        "default_intent": "tool selection and workflow setup",
    },
    {
        "theme": "AI coding agents",
        "queries": ["AI coding agent", "Claude Code", "Codex CLI", "OpenAI Codex", "agentic coding"],
        "default_intent": "tool comparison and implementation workflow",
    },
    {
        "theme": "AI search and answer engines",
        "queries": ["Perplexity AI", "AI search engine", "ChatGPT search", "Google AI Mode", "answer engine optimization"],
        "default_intent": "explainers, comparisons, and strategy guides",
    },
]


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "SEO-GEO-Factory/0.1 signal research"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def hn_search(query):
    url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode({"query": query, "tags": "story", "hitsPerPage": 5})
    try:
        data = fetch_json(url)
    except Exception as e:
        return [{"source": "hn_algolia", "query": query, "error": str(e), "items": []}]
    items = []
    for h in data.get("hits", []):
        title = h.get("title") or h.get("story_title") or ""
        if not title:
            continue
        items.append({
            "title": title,
            "url": h.get("url") or ("https://news.ycombinator.com/item?id=" + str(h.get("objectID"))),
            "points": h.get("points") or 0,
            "comments": h.get("num_comments") or 0,
            "created_at": h.get("created_at"),
        })
    return [{"source": "hn_algolia", "query": query, "items": items}]


def wikipedia_pageview_signal(query):
    # Best-effort entity demand proxy. Not every query maps to a page.
    title = query.replace(" ", "_")
    today = datetime.now(timezone.utc)
    # Use a broad recent-ish fixed window to avoid date arithmetic dependencies; API tolerates missing future? no.
    # Use previous full month-ish hardcoded by current environment date.
    start, end = "2025041200", "2025051100"
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(title, safe='')}/daily/{start}/{end}"
    try:
        data = fetch_json(url)
        views = sum(i.get("views", 0) for i in data.get("items", []))
        return {"source": "wikipedia_pageviews", "query": query, "page_title": title, "views_recent_window": views}
    except Exception as e:
        return {"source": "wikipedia_pageviews", "query": query, "error": str(e), "views_recent_window": None}


def make_candidate(seed, observations):
    hn_items = []
    errors = []
    wiki_views = 0
    wiki_seen = False
    for obs in observations:
        if obs.get("source") == "hn_algolia":
            if obs.get("error"):
                errors.append(obs)
            hn_items.extend(obs.get("items", []))
        if obs.get("source") == "wikipedia_pageviews" and obs.get("views_recent_window") is not None:
            wiki_seen = True
            wiki_views += obs.get("views_recent_window") or 0
    hn_points = sum(i.get("points", 0) for i in hn_items)
    hn_comments = sum(i.get("comments", 0) for i in hn_items)
    demand_score = 1
    if hn_items or wiki_views > 5000:
        demand_score = 3
    if hn_points > 200 or hn_comments > 100 or wiki_views > 50000:
        demand_score = 4
    if hn_points > 1000 or hn_comments > 500 or wiki_views > 250000:
        demand_score = 5
    theme = seed["theme"]
    is_y = any(x in theme.lower() for x in ["health", "legal", "finance"])
    risk = {"veto": "defer" if is_y else "pass", "flags": [] if not is_y else ["potential YMYL"]}
    # Practical heuristic: comparisons/workflows in fast-changing AI tooling often have GEO value and evidence via official docs.
    capture = 3 if demand_score >= 3 else 2
    geo = 4
    evidence = 3
    strategic = 4 if any(x in theme.lower() for x in ["browser", "meeting", "coding", "search"]) else 3
    signals = []
    for obs in observations:
        if obs.get("source") == "hn_algolia":
            for item in obs.get("items", [])[:3]:
                signals.append({
                    "source": "Hacker News search",
                    "evidence": f"{obs['query']}: {item['title']} ({item.get('points',0)} points, {item.get('comments',0)} comments)",
                    "url": item.get("url"),
                    "strength": "medium" if item.get("points", 0) > 50 or item.get("comments", 0) > 25 else "weak",
                })
        elif obs.get("source") == "wikipedia_pageviews" and obs.get("views_recent_window"):
            signals.append({
                "source": "Wikipedia pageviews proxy",
                "evidence": f"{obs['query']} had {obs['views_recent_window']} recent-window pageviews on matching Wikipedia page title",
                "strength": "medium" if obs["views_recent_window"] > 5000 else "weak",
            })
    if not signals:
        signals.append({"source": "automated public-signal scan", "evidence": "No strong public signal found in this pass; keep as research/watch, not production candidate.", "strength": "weak"})
    slug = re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-")
    return {
        "candidate_id": f"sig-real-{slug[:36]}",
        "working_topic": theme,
        "signal_status": "public_signal_scan_v1_partial_not_keyword_tool_verified",
        "observed_signals": signals[:8],
        "query_patterns": seed["queries"],
        "intent": seed["default_intent"],
        "demand_signal": {"score": demand_score, "rationale": f"Observed {len(hn_items)} HN items, {hn_points} points, {hn_comments} comments, wiki_views={wiki_views if wiki_seen else 'n/a'}."},
        "capture_likelihood": {"score": capture, "rationale": "Specific comparison/workflow long-tail pages are more capturable than broad AI head terms; needs SERP difficulty sampling next."},
        "geo_likelihood": {"score": geo, "rationale": "Comparison, workflow, and decision-support content can be structured for AI answer extraction."},
        "evidence_availability": {"score": evidence, "rationale": "Likely official docs/product pages/changelogs exist; source resolution still required before content production."},
        "strategic_fit": {"score": strategic, "rationale": "Fits a traffic-led AI tools/AI workflows pilot direction if human approves the opportunity pool."},
        "risk": risk,
        "recommended_action": "score_in_strategy_meeting_pack",
        "why_now": "Fast-moving AI tooling/search behavior creates recurring comparison and workflow questions; public-signal strength determines priority.",
        "why_us": "Win by producing source-backed, update-aware comparison/workflow assets rather than generic news recaps.",
        "next_research_tasks": ["Validate keyword/search volume", "Sample SERP difficulty and result freshness", "Sample AI answer gaps", "Resolve official sources", "Decide cluster vs single-page placement"],
    }


def main():
    parser = argparse.ArgumentParser(description="Discover signal-led SEO/GEO opportunity candidates from lightweight public sources.")
    parser.add_argument("--out", default="factory/strategy/signal-led-opportunity-input.json")
    args = parser.parse_args()
    all_candidates = []
    raw = []
    for seed in SEEDS:
        observations = []
        for q in seed["queries"][:3]:
            observations.extend(hn_search(q))
            observations.append(wikipedia_pageview_signal(q))
        raw.append({"seed": seed, "observations": observations})
        all_candidates.append(make_candidate(seed, observations))
    artifact = {
        "run_type": "signal_led_strategy_meeting",
        "status": "public_signal_scan_v1_partial",
        "target_site": "productivity-ai-pilot",
        "target_region_language": "en-US initially unless changed by human",
        "strategy_goal": "Find traffic-capturable SEO/GEO opportunities from public signals before creating content clusters or pages.",
        "signal_sources_to_use_next": [
            "Keyword tool exports / Google Trends for demand validation",
            "SERP sampling and People Also Ask for capture likelihood",
            "Competitor URL/content-structure observations",
            "Community questions from Reddit, forums, YouTube, X, Hacker News, Product Hunt, app stores",
            "AI answer gap sampling from ChatGPT/Perplexity/Gemini prompts",
            "Official product docs, changelogs, standards, and public datasets"
        ],
        "candidates": all_candidates,
        "raw_observations": raw,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"created": str(out.relative_to(root)), "candidates": len(all_candidates)}, indent=2))


if __name__ == "__main__":
    main()
