# Validated opportunity pool — v1

Status: `validated_opportunity_pool_not_content_or_publish_approval`  
Production publish allowed: `false`

This validates the two signal-led recommendations before any content production. It samples SERP shape, checks official-source feasibility, and prepares AI-answer-gap prompts.

## AI browsers and agent browsers

Recommended action: `create_validation_brief_not_content_yet`

### Scores
- traffic_likelihood: `medium_from_public_signal_scan_needs_keyword_tool`
- capture_likelihood: `medium_high`
- geo_likelihood: `high`
- evidence_confidence: `high`
- risk_veto: `pass`

### SERP shape
- Type counts: `{"other": 25, "competitor_content": 8, "official_or_primary": 4, "news_or_review": 3}`

Top observed results:
- [More at Wikipedia](https://en.wikipedia.org/wiki/AI_browser) — `other` via `AI browser`
- [8 Best Agentic AI Browsers in 2026](https://usefulai.com/tools/ai-browsers) — `competitor_content` via `AI browser`
- [Comet Browser: a Personal AI Assistant](https://www.perplexity.ai/comet) — `official_or_primary` via `AI browser`
- [The Best AI Web Browsers We've Tested for 2026 | PCMag](https://www.pcmag.com/picks/the-best-ai-web-browsers) — `news_or_review` via `AI browser`
- [11 Best AI Browsers in 2026 (Tested & Compared) - testgrid.io](https://testgrid.io/blog/ai-browsers/) — `competitor_content` via `AI browser`
- [The 5 best AI browsers in 2026 - Zapier](https://zapier.com/blog/best-ai-browser/) — `competitor_content` via `AI browser`
- [I Tested the Four Biggest AI Browsers, and Here's What I Found](https://lifehacker.com/tech/i-compared-the-biggest-ai-browsers) — `other` via `AI browser`
- [6 Best AI Browsers (2026 Tested) - Stop Drowning in Browser Tabs](https://kripeshadwani.com/best-ai-browsers/) — `competitor_content` via `AI browser`

### Official source feasibility
- [Perplexity Comet official page](https://www.perplexity.ai/comet) — reachable: `True`, HTTP: `403`
- [OpenAI ChatGPT official site](https://chatgpt.com/) — reachable: `True`, HTTP: `403`
- [Google Search AI Mode announcement](https://blog.google/products/search/ai-mode-search/) — reachable: `True`, HTTP: `200`
- [Microsoft Edge Copilot feature page](https://www.microsoft.com/en-us/edge/features/copilot) — reachable: `True`, HTTP: `200`

### AI answer gap prompts to sample
- What is an AI browser?
- AI browser vs AI search engine
- ChatGPT Atlas vs Perplexity Comet
- Best AI browsers for research
- What privacy risks do AI browsers create?

### Notes
- SERP data is from DuckDuckGo HTML sampling and should be supplemented with Google/Bing/keyword-tool data.
- AI answer gap prompts are prepared but not represented as measured model outputs unless sampled by an approved API/manual reviewer.

## AI search and answer engines

Recommended action: `create_validation_brief_not_content_yet`

### Scores
- traffic_likelihood: `medium_from_public_signal_scan_needs_keyword_tool`
- capture_likelihood: `medium`
- geo_likelihood: `high`
- evidence_confidence: `high`
- risk_veto: `pass`

### SERP shape
- Type counts: `{"other": 6, "official_or_primary": 3, "competitor_content": 5, "news_or_review": 2}`

Top observed results:
- [Perplexity AI](https://en.wikipedia.org/wiki/Perplexity_AI) — `other` via `Perplexity AI`
- [Perplexity AI](https://www.perplexity.ai/) — `official_or_primary` via `Perplexity AI`
- [What Is Perplexity? Here's Everything You Need to Know About This AI ...](https://www.cnet.com/tech/services-and-software/what-is-perplexity-heres-everything-you-need-to-know-about-this-ai-chatbot/) — `competitor_content` via `Perplexity AI`
- [Perplexity AI App](https://www.perplexityai.app/) — `other` via `Perplexity AI`
- [Perplexity - Download and install on Windows | Microsoft Store](https://apps.microsoft.com/detail/xp8jnqfbqh6pvf) — `official_or_primary` via `Perplexity AI`
- [Want Perplexity Pro for free? 4 ways to get a year of access ... - ZDNET](https://www.zdnet.com/article/want-perplexity-pro-for-free-4-ways-to-get-a-year-of-access-for-0-a-200-value/) — `news_or_review` via `Perplexity AI`
- [My In-Depth Perplexity AI Review: Is Pro Worth It in 2026? - G2](https://learn.g2.com/perplexity-ai-review) — `competitor_content` via `Perplexity AI`
- [Perplexity AI: Exploring AI-powered search beyond Google](https://searchengineland.com/perplexity-ai-exploring-ai-powered-search-beyond-google-439879) — `other` via `Perplexity AI`

### Official source feasibility
- [Perplexity official site](https://www.perplexity.ai/) — reachable: `True`, HTTP: `403`
- [OpenAI ChatGPT search help](https://help.openai.com/en/articles/9237897-chatgpt-search) — reachable: `True`, HTTP: `403`
- [Google AI Mode help](https://support.google.com/websearch/answer/14901683) — reachable: `True`, HTTP: `200`
- [Google Search Central](https://developers.google.com/search) — reachable: `True`, HTTP: `200`

### AI answer gap prompts to sample
- What is an AI search engine?
- Perplexity AI vs ChatGPT Search
- Google AI Mode vs ChatGPT Search
- What is answer engine optimization?
- How should a website optimize for AI answer engines?

### Notes
- SERP data is from DuckDuckGo HTML sampling and should be supplemented with Google/Bing/keyword-tool data.
- AI answer gap prompts are prepared but not represented as measured model outputs unless sampled by an approved API/manual reviewer.
