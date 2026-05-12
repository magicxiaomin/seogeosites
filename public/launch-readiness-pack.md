# Launch readiness pack

This is a production-preparation artifact only. It does not approve publishing and does not change `publish_allowed`.

- Run: `factory/runs/pilot-001`
- Production publish allowed: `False`
- Publish-readiness: `Needs Review`
- Candidate pages after review decisions: `0`

## Trust pages required before production

### About and Editorial Standards

- Slug: `about-and-editorial-standards`
- Status: `draft_required_before_production`
- Purpose: Explain who the site is for, what the editorial promise is, and how AI-assisted content is reviewed before publication.
- Required sections:
  - Audience and scope
  - Editorial promise
  - AI assistance disclosure
  - Human review policy
  - Correction and update path

### Source and Update Policy

- Slug: `source-and-update-policy`
- Status: `draft_required_before_production`
- Purpose: Define acceptable source types, claim support expectations, source-review cadence, and update triggers.
- Required sections:
  - Accepted source hierarchy
  - Claim evidence rules
  - Freshness and review dates
  - Correction workflow
  - Unsupported-claim policy

### Contact and Corrections

- Slug: `contact-and-corrections`
- Status: `draft_required_before_production`
- Purpose: Give readers a way to report errors, request clarifications, or raise source concerns.
- Required sections:
  - Contact route
  - Correction request format
  - Response expectations
  - Escalation for sensitive issues

### Privacy and Disclosures

- Slug: `privacy-and-disclosures`
- Status: `draft_required_before_production`
- Purpose: State data handling, affiliate/sponsorship disclosures if any, analytics posture, and privacy contact path.
- Required sections:
  - Data collection posture
  - Analytics disclosure
  - Affiliate/sponsorship disclosure
  - Privacy contact
  - Policy update date

## Production robots/indexing plan

- Current staging robots: `User-agent: *\nDisallow: /`
- Current staging meta: `noindex,nofollow`
- Production robots change: Allow intended public URLs only after publish-batch approval; keep review/admin/artifact paths blocked.
- Production meta change: Remove noindex only from explicitly approved production pages; keep non-approved staging/review artifacts noindex.
- Production sitemap rule: Generate sitemap only for production-approved URLs and exclude review artifacts.

### Never-index paths

- `/qa-dashboard.html`
- `/editorial-review-pack.md`
- `/review-decisions-input.json`
- `/review-decision-application.md`
- `/production-readiness-simulation.md`
- `/review-checklists.md`

## Analytics and measurement hooks

### Pre-publish setup

- Confirm brand/domain and final URL structure.
- Prepare Search Console property after domain decision.
- Decide analytics tool and privacy disclosure wording.
- Keep staging preview unindexed and exclude it from production metrics.

### Post-publish metrics

- Indexing status by URL
- Impressions/clicks/CTR by query group
- Internal-link crawl coverage
- Engagement proxy by page type if analytics credentials exist
- Sampled AI-answer coverage observations
- Source freshness and update backlog

## Remaining blockers

- no_pages_approved_for_publish_batch
- explicit_publish_batch_approval
- final_brand_domain_decision
- trust_pages_finalized
- production_robots_indexing_plan_approved
- analytics_search_console_hooks_if_credentials_exist
