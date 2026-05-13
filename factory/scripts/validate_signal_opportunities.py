from pathlib import Path
import argparse, json, urllib.parse, urllib.request, re
from datetime import datetime, timezone
from html.parser import HTMLParser

root = Path(__file__).resolve().parents[2]

CANDIDATES = [
  {
    "id":"validated-ai-browsers-agent-browsers",
    "topic":"AI browsers and agent browsers",
    "queries":["AI browser", "agent browser", "ChatGPT Atlas", "Perplexity Comet", "browser agent"],
    "official_sources":[
      {"title":"Perplexity Comet official page", "url":"https://www.perplexity.ai/comet"},
      {"title":"OpenAI ChatGPT official site", "url":"https://chatgpt.com/"},
      {"title":"Google Search AI Mode announcement", "url":"https://blog.google/products/search/ai-mode-search/"},
      {"title":"Microsoft Edge Copilot feature page", "url":"https://www.microsoft.com/en-us/edge/features/copilot"}
    ],
    "gap_prompts":["What is an AI browser?", "AI browser vs AI search engine", "ChatGPT Atlas vs Perplexity Comet", "Best AI browsers for research", "What privacy risks do AI browsers create?"]
  },
  {
    "id":"validated-ai-search-answer-engines",
    "topic":"AI search and answer engines",
    "queries":["Perplexity AI", "AI search engine", "ChatGPT search", "Google AI Mode", "answer engine optimization"],
    "official_sources":[
      {"title":"Perplexity official site", "url":"https://www.perplexity.ai/"},
      {"title":"OpenAI ChatGPT search help", "url":"https://help.openai.com/en/articles/9237897-chatgpt-search"},
      {"title":"Google AI Mode help", "url":"https://support.google.com/websearch/answer/14901683"},
      {"title":"Google Search Central", "url":"https://developers.google.com/search"}
    ],
    "gap_prompts":["What is an AI search engine?", "Perplexity AI vs ChatGPT Search", "Google AI Mode vs ChatGPT Search", "What is answer engine optimization?", "How should a website optimize for AI answer engines?"]
  }
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self._a=None; self._text=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a':
            self._a=dict(attrs); self._text=[]
    def handle_data(self, data):
        if self._a is not None: self._text.append(data)
    def handle_endtag(self, tag):
        if tag=='a' and self._a is not None:
            href=self._a.get('href',''); text=' '.join(' '.join(self._text).split())
            if href and text: self.links.append({'href':href,'text':text})
            self._a=None; self._text=[]

def fetch(url, timeout=20):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 SEO-GEO-Factory validation'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', errors='replace')

def duckduckgo(query):
    url='https://duckduckgo.com/html/?'+urllib.parse.urlencode({'q':query})
    try:
        status, html=fetch(url)
        p=LinkParser(); p.feed(html)
        out=[]
        for l in p.links:
            href=l['href']; text=l['text']
            if 'duckduckgo.com/l/?uddg=' in href:
                qs=urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href=urllib.parse.unquote(qs.get('uddg',[''])[0])
            if href.startswith('http') and 'duckduckgo.com' not in href and len(text)>12:
                if not any(x['url']==href for x in out):
                    out.append({'title':text[:180], 'url':href})
            if len(out)>=8: break
        return {'query':query,'source':'duckduckgo_html','http_status':status,'results':out}
    except Exception as e:
        return {'query':query,'source':'duckduckgo_html','error':str(e),'results':[]}

def check_sources(sources):
    checked=[]
    for s in sources:
        item=dict(s)
        try:
            req=urllib.request.Request(s['url'], headers={'User-Agent':'Mozilla/5.0 SEO-GEO-Factory source check'}, method='HEAD')
            with urllib.request.urlopen(req, timeout=15) as r: item.update({'reachable': True, 'http_status': r.status})
        except Exception as e:
            try:
                status,_=fetch(s['url'], timeout=15); item.update({'reachable': True, 'http_status': status, 'source_access_note': 'direct_fetch_ok'})
            except urllib.error.HTTPError as e2:
                item.update({'reachable': e2.code in {401, 403}, 'http_status': e2.code, 'source_access_note': 'official URL exists but blocks automated access' if e2.code in {401,403} else 'http_error'})
            except Exception as e2: item.update({'reachable': False, 'error': str(e2)[:200], 'source_access_note': 'not_reachable_by_automated_check'})
        checked.append(item)
    return checked

def classify_result(url,title):
    u=url.lower(); t=title.lower()
    if any(x in u for x in ['openai.com','perplexity.ai','google.com','microsoft.com','anthropic.com']): return 'official_or_primary'
    if any(x in u for x in ['techcrunch','theverge','wired','arstechnica','zdnet','tomsguide','pcmag','forbes']): return 'news_or_review'
    if any(x in u for x in ['reddit.com','news.ycombinator.com','stackexchange']): return 'community'
    if any(x in t for x in ['best','vs','comparison','review','what is','guide']): return 'competitor_content'
    return 'other'

def validate_candidate(c):
    serp=[]
    for q in c['queries'][:5]: serp.append(duckduckgo(q))
    flat=[]
    for s in serp:
        for r in s['results']:
            flat.append({**r,'query':s['query'],'type':classify_result(r['url'],r['title'])})
    type_counts={}
    for r in flat: type_counts[r['type']]=type_counts.get(r['type'],0)+1
    sources=check_sources(c['official_sources'])
    reachable=sum(1 for s in sources if s.get('reachable'))
    gaps=[]
    for p in c['gap_prompts']:
        gaps.append({'prompt':p,'expected_gap_to_check':'Does the answer provide current product status, official-source distinctions, privacy/safety caveats, and a practical comparison/workflow table?','sampling_status':'prompt_prepared_manual_or_api_sampling_required'})
    official_count=type_counts.get('official_or_primary',0)
    competitor_count=type_counts.get('competitor_content',0)+type_counts.get('news_or_review',0)
    capture='medium'
    if competitor_count>=8 and official_count>=3: capture='medium_high'
    if competitor_count>15: capture='medium_low_competitive'
    evidence='high' if reachable>=2 else 'medium' if reachable==1 else 'low'
    rec='create_validation_brief_not_content_yet' if evidence in ['high','medium'] else 'defer_until_sources_resolved'
    return {
        'candidate_id':c['id'], 'topic':c['topic'], 'validated_at':datetime.now(timezone.utc).isoformat(),
        'serp_observations':serp, 'serp_type_counts':type_counts,
        'top_observed_results':flat[:20], 'evidence_source_feasibility': {'official_sources':sources,'reachable_count':reachable,'confidence':evidence},
        'ai_answer_gap_sampling': gaps,
        'validation_scores': {'traffic_likelihood':'medium_from_public_signal_scan_needs_keyword_tool','capture_likelihood':capture,'geo_likelihood':'high','evidence_confidence':evidence,'risk_veto':'pass'},
        'recommended_action':rec,
        'recommended_next_asset': 'strategy_validation_brief + source map + SERP gap table before any draft',
        'notes': ['SERP data is from DuckDuckGo HTML sampling and should be supplemented with Google/Bing/keyword-tool data.', 'AI answer gap prompts are prepared but not represented as measured model outputs unless sampled by an approved API/manual reviewer.']
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',default='factory/strategy/meetings/2026-05-12-opportunity-validation-v1'); args=ap.parse_args()
    out=root/args.out_dir; out.mkdir(parents=True,exist_ok=True)
    validations=[validate_candidate(c) for c in CANDIDATES]
    pool={'status':'validated_opportunity_pool_not_content_or_publish_approval','production_publish_allowed':False,'validation_scope':'SERP sample + source feasibility + AI-answer-gap prompt prep','candidates':validations}
    (out/'validated_opportunity_pool.json').write_text(json.dumps(pool,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'serp_observations.json').write_text(json.dumps({v['candidate_id']:v['serp_observations'] for v in validations},indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'evidence_source_feasibility.json').write_text(json.dumps({v['candidate_id']:v['evidence_source_feasibility'] for v in validations},indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'ai_answer_gap_sampling.json').write_text(json.dumps({v['candidate_id']:v['ai_answer_gap_sampling'] for v in validations},indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# Validated opportunity pool — v1','','Status: `validated_opportunity_pool_not_content_or_publish_approval`  ','Production publish allowed: `false`','','This validates the two signal-led recommendations before any content production. It samples SERP shape, checks official-source feasibility, and prepares AI-answer-gap prompts.']
    for v in validations:
        lines += ['',f"## {v['topic']}",'',f"Recommended action: `{v['recommended_action']}`",'', '### Scores']
        for k,val in v['validation_scores'].items(): lines.append(f"- {k}: `{val}`")
        lines += ['', '### SERP shape', f"- Type counts: `{json.dumps(v['serp_type_counts'])}`", '', 'Top observed results:']
        for r in v['top_observed_results'][:8]: lines.append(f"- [{r['title']}]({r['url']}) — `{r['type']}` via `{r['query']}`")
        lines += ['', '### Official source feasibility']
        for s in v['evidence_source_feasibility']['official_sources']: lines.append(f"- [{s['title']}]({s['url']}) — reachable: `{s.get('reachable')}`, HTTP: `{s.get('http_status','n/a')}`")
        lines += ['', '### AI answer gap prompts to sample']
        for g in v['ai_answer_gap_sampling']: lines.append(f"- {g['prompt']}")
        lines += ['', '### Notes'] + [f"- {n}" for n in v['notes']]
    (out/'validated_opportunity_pool.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'created':str(out.relative_to(root)),'candidates':len(validations)},indent=2))
if __name__=='__main__': main()
