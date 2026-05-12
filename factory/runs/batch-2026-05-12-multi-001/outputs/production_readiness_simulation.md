# Production readiness simulation

Status: simulation only — production publishing remains disabled.

- Production publish allowed: `False`
- Current publish_allowed field: `False`
- Can enter human publish review queue: `False`

## Missing before production publish

- content_quality_pass
- strategy_cluster_measurement_artifacts
- explicit_production_blocker_list
- human_editorial_decisions_recorded
- publish_batch_approval
- final_brand_domain_decision
- trust_pages_finalized
- production_robots_indexing_plan
- analytics_search_console_hooks_if_credentials_exist

## Page-level review gaps

### ai-workflow-template-for-onboarding-new-employees

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, privacy_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Privacy/data-handling review

### ai-workflow-template-for-invoice-approval-routing

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, privacy_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Privacy/data-handling review

### ai-workflow-template-for-product-feedback-triage

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, privacy_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Privacy/data-handling review

### ai-workflow-template-for-recruiting-interview-scorecards

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, privacy_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Privacy/data-handling review

### ai-workflow-template-for-sales-call-summaries

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, privacy_review_required, monetization_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Privacy/data-handling review
  - Monetization/disclosure review

### ai-workflow-template-for-knowledge-base-article-updates

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, copyright_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Copyright/IP review

### ai-workflow-template-for-project-status-reporting

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs

### ai-workflow-template-for-incident-postmortem-drafts

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs

### ai-workflow-template-for-webinar-content-repurposing

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, copyright_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Copyright/IP review

### ai-workflow-template-for-procurement-vendor-comparison

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs

### ai-workflow-template-for-quarterly-business-review-preparation

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs

### ai-workflow-template-for-customer-research-interview-synthesis

- Ready for publish batch after human review: `False`
- Active review flags: `missing_concrete_source_urls, privacy_review_required`
- Required before publish:
  - Human review before production publish
  - Replace source-plan placeholders with concrete official URLs
  - Privacy/data-handling review
