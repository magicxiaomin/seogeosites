from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]

REVIEW_GUIDANCE = {
    "privacy_review_required": [
        "Confirm the draft does not ask readers to paste sensitive personal, customer, or confidential business data into AI tools without safeguards.",
        "Add or verify data-minimization guidance for notes, CRM records, support tickets, and transcripts.",
        "Confirm any tool-specific privacy or data-retention claims are supported by accepted official sources.",
    ],
    "copyright_review_required": [
        "Confirm the workflow discourages copying third-party content verbatim or bypassing licenses.",
        "Add or verify guidance for attribution, permission, fair-use uncertainty, and original editorial transformation.",
        "Confirm examples/templates are original and not rewritten competitor material.",
    ],
    "monetization_review_required": [
        "Confirm no affiliate, sponsorship, or vendor preference is implied without disclosure.",
        "Add disclosure placeholders if tool recommendations or monetized links may be added later.",
        "Confirm recommendations are framed as editorial guidance, not guaranteed commercial outcomes.",
    ],
    "high_risk_topic": [
        "Escalate before further drafting; do not publish without explicit approval and qualified review.",
    ],
    "missing_concrete_source_urls": [
        "Replace placeholder source notes with accepted concrete URLs from official or primary sources.",
    ],
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def active_flags(page):
    return [name for name, enabled in page.get("review_flags", {}).items() if enabled]


def main():
    parser = argparse.ArgumentParser(description="Generate human review checklists from a batch publish report.")
    parser.add_argument("--run", default="factory/runs/pilot-001")
    parser.add_argument("--out", help="Markdown output path. Defaults to <run>/outputs/review_checklists.md")
    args = parser.parse_args()

    run = Path(args.run)
    if not run.is_absolute():
        run = root / run
    out = Path(args.out) if args.out else run / "outputs" / "review_checklists.md"
    if not out.is_absolute():
        out = root / out

    batch = load_json(run / "outputs" / "batch_publish_report.json")
    lines = [
        "# Human Review Checklists",
        "",
        f"Run: `{batch.get('run', args.run)}`",
        f"Batch readiness: **{batch.get('status', 'unknown')}**",
        f"Publish allowed: `{batch.get('publish_allowed')}`",
        "",
        "> This file is a staging review artifact. It does not approve production publishing.",
        "",
        "## Batch-level gates",
        "",
        "- [ ] Confirm every page has at least two accepted, reachable sources for factual/product claims.",
        "- [ ] Confirm direct-answer blocks are accurate and do not overclaim.",
        "- [ ] Confirm no page copies competitor text, protected examples, or proprietary templates.",
        "- [ ] Confirm privacy, copyright/IP, and monetization disclosures are resolved where flagged.",
        "- [ ] Confirm final production publish batch is explicitly approved by a human reviewer.",
        "",
    ]

    for page in batch.get("generated_pages", []):
        flags = active_flags(page)
        lines.extend([
            f"## {page.get('topic', page.get('opportunity_id', 'Untitled page'))}",
            "",
            f"- Opportunity ID: `{page.get('opportunity_id')}`",
            f"- Draft: `{page.get('draft_path')}`",
            f"- QA status: **{page.get('qa_status', 'unknown')}**",
            f"- Active flags: {', '.join(flags) if flags else 'none'}",
            "",
            "### Required before publish",
            "",
        ])
        for item in page.get("required_before_publish", []):
            lines.append(f"- [ ] {item}")
        if not page.get("required_before_publish"):
            lines.append("- [ ] Human review before production publish")
        lines.extend(["", "### Flag-specific checks", ""])
        if flags:
            for flag in flags:
                lines.append(f"**{flag}**")
                for item in REVIEW_GUIDANCE.get(flag, ["Resolve this review flag before publish."]):
                    lines.append(f"- [ ] {item}")
                lines.append("")
        else:
            lines.append("- [ ] Confirm no additional privacy, copyright/IP, monetization, or YMYL flags were introduced during editing.")
            lines.append("")
        lines.extend([
            "### Editorial sign-off",
            "",
            "- [ ] Source-backed factual claims verified against accepted sources.",
            "- [ ] Examples/templates are useful, original, and non-deceptive.",
            "- [ ] Page remains staging-only until batch approval.",
            "",
        ])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated review checklists: {out.relative_to(root)}")


if __name__ == "__main__":
    main()
