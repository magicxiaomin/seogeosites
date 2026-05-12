from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
RUN = root / "factory/runs/pilot-001"
CONTENT_DIR = root / "content/sites/productivity-ai-pilot/pages"

FLAG_NOTES = {
    "privacy_review_required": [
        "Privacy note: do not paste sensitive customer data, private transcripts, credentials, or confidential business information into an AI tool unless the organization has approved that tool and its data-handling settings.",
        "Use redaction, data minimization, and access controls before testing this workflow with real tickets or CRM records.",
    ],
    "copyright_review_required": [
        "Copyright/IP note: use this workflow to transform owned or licensed material; do not copy third-party articles, competitor pages, or protected examples into a repurposing template without permission or a separate legal/editorial review.",
        "Keep examples original and attribute source material when attribution is required.",
    ],
    "monetization_review_required": [
        "Disclosure note: if tool recommendations, affiliate links, sponsorships, or vendor preferences are added later, disclose the relationship clearly before publication.",
        "Do not present sales outcomes or conversion improvements as guaranteed results.",
    ],
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_lines(source_verification):
    lines = []
    for source in source_verification.get("candidate_sources", []):
        if source.get("status") != "accepted" or source.get("reachable") is not True:
            continue
        title = source.get("title") or source.get("url")
        claims = ", ".join(source.get("supports_claims", [])) or "source-backed factual context"
        lines.append(f"- {title}: {source.get('url')} — supports: {claims}.")
    return lines


def flag_lines(flags):
    lines = []
    for flag, enabled in flags.items():
        if enabled:
            lines.extend(FLAG_NOTES.get(flag, []))
    return lines


def replace_section(body, heading, new_section):
    marker = f"## {heading}"
    start = body.find(marker)
    if start == -1:
        return body.rstrip() + "\n\n" + new_section.rstrip() + "\n"
    next_start = body.find("\n## ", start + len(marker))
    if next_start == -1:
        return body[:start].rstrip() + "\n\n" + new_section.rstrip() + "\n"
    return body[:start].rstrip() + "\n\n" + new_section.rstrip() + "\n" + body[next_start:]


def main():
    batch = load_json(RUN / "outputs/batch_publish_report.json")
    updated = []
    for page in batch.get("generated_pages", []):
        slug = page["slug"]
        md_path = CONTENT_DIR / f"{slug}.md"
        sv = load_json(RUN / "outputs/pages" / page["opportunity_id"] / "source_verification.json")
        text = md_path.read_text(encoding="utf-8")
        source_notes = source_lines(sv)
        risk_notes = flag_lines(page.get("review_flags", {}))
        evidence_section = [
            "## Evidence and source notes",
            "",
            "This staging page now includes accepted, reachable source URLs for factual/tool-context claims. Sources support context and capabilities; they do not turn editorial recommendations into guaranteed outcomes.",
            "",
            "### Accepted sources",
            "",
            *(source_notes or ["- No accepted source URLs are recorded yet."]),
            "",
            "### Editorial guardrails",
            "",
            "- Keep factual product/tool claims tied to accepted sources.",
            "- Mark recommendations as editorial workflow guidance, not source-backed facts unless the source directly supports them.",
            "- Keep this page in staging preview until production publish gates pass.",
        ]
        if risk_notes:
            evidence_section.extend(["", "### Risk-specific notes", ""])
            evidence_section.extend(f"- {note}" for note in risk_notes)
        body = replace_section(text, "Evidence and source notes", "\n".join(evidence_section))
        body = body.replace("- Human review triggers are documented.", "- Staging approval is automated; production publish remains controlled by publish gates.")
        body = body.replace("A human should review it when source URLs are missing, privacy/security claims are present, or the topic changes risk class.", "The system should keep it in staging when source URLs are missing, privacy/security flags are unresolved for production, or the topic changes risk class.")
        md_path.write_text(body, encoding="utf-8")
        updated.append(str(md_path.relative_to(root)))
    print(json.dumps({"updated_pages": updated}, indent=2))


if __name__ == "__main__":
    main()
