#!/usr/bin/env python3
"""Add practical, reviewable template sections to pilot staging pages."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content/sites/productivity-ai-pilot/pages"

PAGE_SECTIONS = {
    "ai-workflow-template-for-meeting-notes-and-action-items": {
        "direct": "Use this workflow to turn a meeting transcript or rough notes into a decision log, owner-based action-item list, and follow-up message. Keep raw transcripts private, verify names and decisions with the meeting owner, and publish only the cleaned summary.",
        "input": ["Meeting agenda or topic", "Transcript, recording notes, or live notes", "Participant list and owner names", "Decision criteria, due dates, and open questions"],
        "steps": ["Remove unrelated small talk and any sensitive material that should not leave the source system.", "Ask the AI tool to extract decisions, risks, blockers, and action items separately.", "Group action items by owner and add due dates only when they are explicit in the source notes.", "Send the draft to the meeting owner for correction before sharing it with attendees."],
        "prompt": "You are helping prepare meeting notes. From the source notes below, extract: decisions, action items with owner and due date, open questions, and risks. If an owner or due date is not explicit, write 'not specified' instead of guessing. Keep the tone neutral and do not add facts that are not in the notes.",
        "output": ["One-paragraph meeting summary", "Decision log", "Action-item table with owner, due date, and confidence", "Follow-up email or chat message"],
    },
    "ai-workflow-template-for-customer-support-triage": {
        "direct": "Use this workflow to classify support messages by issue type, urgency, account impact, and next action. It should assist support agents, not replace human judgment for refunds, security issues, escalations, or sensitive customer data.",
        "input": ["Customer message", "Product area or plan tier", "Known incident status", "Relevant help-center article or internal runbook"],
        "steps": ["Redact personal data that is not required for classification.", "Classify the ticket into issue type, urgency, sentiment, and escalation need.", "Suggest the next response path with links to official help or internal runbook material.", "Require an agent to review the classification before sending any customer-facing reply."],
        "prompt": "Classify this support ticket for triage. Return issue type, urgency, sentiment, likely product area, escalation reason if any, and the next agent action. Do not promise refunds, policy exceptions, legal conclusions, or account-specific outcomes.",
        "output": ["Triage label set", "Escalation recommendation", "Draft internal note", "Suggested but human-reviewed customer reply outline"],
    },
    "ai-workflow-template-for-weekly-business-reporting": {
        "direct": "Use this workflow to turn weekly metrics and team notes into a concise business update with wins, risks, metric changes, and next priorities. The AI should explain source numbers but should not invent causes for metric movement.",
        "input": ["Weekly KPI table", "Prior-week comparison", "Team updates", "Known launches, incidents, or campaigns"],
        "steps": ["Paste or upload only metrics that are approved for the report audience.", "Ask the AI to summarize changes and flag metrics that need owner explanation.", "Separate observed metric movement from hypotheses about why it happened.", "Have metric owners verify final numbers before distribution."],
        "prompt": "Create a weekly business report from the provided metrics and notes. Separate facts, interpretation, risks, and open questions. Do not infer causality unless it is stated in the notes. Highlight missing data that a human should verify.",
        "output": ["Executive summary", "Metric movement table", "Risks and blockers", "Next-week priorities and owner questions"],
    },
    "ai-workflow-template-for-content-repurposing": {
        "direct": "Use this workflow to transform owned or licensed source material into channel-specific drafts while preserving the original meaning, attribution needs, and review status. Do not use it to rewrite competitor content or bypass copyright restrictions.",
        "input": ["Owned article, webinar transcript, white paper, or newsletter", "Target channels", "Brand voice rules", "Attribution or licensing requirements"],
        "steps": ["Confirm the source material is owned, licensed, or otherwise approved for reuse.", "Extract the core claims, examples, and citations before drafting new formats.", "Generate channel-specific versions that add summaries, hooks, or formatting rather than copying paragraphs.", "Run copyright, factual, and brand review before scheduling."],
        "prompt": "Repurpose the approved source material into the requested formats. Preserve the original meaning, flag claims that need citation, avoid copying long passages verbatim, and list any attribution or rights questions a reviewer must answer.",
        "output": ["LinkedIn post draft", "Newsletter blurb", "Short video outline", "Citation and rights-review checklist"],
    },
    "ai-workflow-template-for-sales-follow-up-notes": {
        "direct": "Use this workflow to convert sales-call notes into a CRM-ready summary, next-step plan, and follow-up email. Keep it factual, disclose uncertainty, and avoid promising outcomes or making unsupported ROI claims.",
        "input": ["Call notes or approved transcript excerpt", "Account and opportunity context", "Buyer questions and objections", "Approved product messaging"],
        "steps": ["Remove confidential or irrelevant personal details before processing.", "Extract buyer goals, pain points, decision process, objections, and next steps.", "Draft a follow-up message that references only confirmed facts and approved claims.", "Have the account owner review before sending or updating CRM fields."],
        "prompt": "Summarize this sales conversation for CRM and follow-up. Capture buyer goals, stakeholders, objections, next steps, and open questions. Use only information in the notes. Do not invent budget, authority, timing, ROI, or product commitments.",
        "output": ["CRM summary", "Next-step checklist", "Follow-up email draft", "Reviewer notes for claims or disclosure concerns"],
    },
}


def block(slug: str, data: dict) -> str:
    bullets = lambda items: "\n".join(f"- {item}" for item in items)
    return f"""## Practical template

### Inputs to collect

{bullets(data['input'])}

### Step-by-step workflow

{chr(10).join(f'{i}. {step}' for i, step in enumerate(data['steps'], 1))}

### Reusable AI prompt block

```text
{data['prompt']}
```

### Expected outputs

{bullets(data['output'])}

### Human QA checks

- The final answer distinguishes source-backed facts from editorial recommendations.
- Any privacy, copyright, monetization, or disclosure issue remains flagged for production review.
- The reviewer can trace factual or tool-capability claims to the accepted sources below.
"""


def replace_between(text: str, start_heading: str, end_heading: str, replacement: str) -> str:
    start = text.find(start_heading)
    end = text.find(end_heading)
    if start == -1 or end == -1 or end <= start:
        return text
    return text[:start].rstrip() + "\n\n" + replacement.rstrip() + "\n\n" + text[end:].lstrip()


def main() -> None:
    updated = []
    for slug, data in PAGE_SECTIONS.items():
        path = CONTENT_DIR / f"{slug}.md"
        text = path.read_text(encoding="utf-8")
        text = replace_between(text, "## Direct answer", "## What this is", f"## Direct answer\n\n{data['direct']}")
        text = replace_between(text, "## Recommended workflow", "## Evidence and source notes", block(slug, data))
        path.write_text(text, encoding="utf-8")
        updated.append(str(path.relative_to(ROOT)))
    print("Updated practical template sections:")
    for item in updated:
        print(f"- {item}")


if __name__ == "__main__":
    main()
