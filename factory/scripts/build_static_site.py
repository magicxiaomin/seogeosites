from pathlib import Path
import html
import json
import re
from datetime import date

root = Path(__file__).resolve().parents[2]
public = root / "public"
public.mkdir(exist_ok=True)


def parse_frontmatter(text):
    meta = {}
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        return meta, body.strip()
    return meta, text


def inline_md(text):
    escaped = html.escape(text)
    linked = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" rel="nofollow noopener">{html.escape(m.group(1))}</a>',
        escaped,
    )
    return re.sub(
        r"(?<!href=\")https?://[^\s<]+",
        lambda m: f'<a href="{html.escape(m.group(0), quote=True)}" rel="nofollow noopener">{html.escape(m.group(0))}</a>',
        linked,
    )


def md_to_html(md):
    lines = []
    in_code = False
    code_lines = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                lines.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("# "):
            lines.append(f"<h1>{inline_md(line[2:])}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{inline_md(line[3:])}</h2>")
        elif line.startswith("### "):
            lines.append(f"<h3>{inline_md(line[4:])}</h3>")
        elif re.match(r"^\d+\. ", line):
            lines.append(f'<p class="step">{inline_md(line)}</p>')
        elif line.startswith("- "):
            lines.append(f'<p class="bullet">• {inline_md(line[2:])}</p>')
        elif line.strip():
            lines.append(f"<p>{inline_md(line)}</p>")
    if in_code:
        lines.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(lines)


def extract_faq(body):
    faq = []
    marker = "## FAQ"
    start = body.find(marker)
    if start == -1:
        return faq
    section = body[start + len(marker):]
    for match in re.finditer(r"\n### ([^\n]+)\n\n(.+?)(?=\n### |\Z)", section, flags=re.S):
        answer = " ".join(x.strip() for x in match.group(2).splitlines() if x.strip())
        faq.append({"@type": "Question", "name": match.group(1).strip(), "acceptedAnswer": {"@type": "Answer", "text": answer}})
    return faq


pages = []
for p in sorted((root / "content/sites").glob("*/pages/*.md")):
    meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    title = meta.get("title", p.stem)
    slug = meta.get("slug", p.stem)
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "dateModified": meta.get("last_reviewed", ""),
        "isAccessibleForFree": True,
        "genre": "staging SEO/GEO knowledge asset",
    }
    faq = extract_faq(body)
    schema = [article]
    if faq:
        schema.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq})
    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="Staging SEO/GEO knowledge asset: {html.escape(title)}">
<meta name="robots" content="noindex,nofollow">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>body{{font-family:system-ui,sans-serif;max-width:860px;margin:40px auto;line-height:1.65;padding:0 20px;color:#172033}} .banner{{background:#fff7ed;border:1px solid #fed7aa;padding:12px;border-radius:10px}} h1{{line-height:1.15}} .step,.bullet{{margin-left:1rem}} pre{{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;padding:14px;border-radius:10px}} a{{color:#1d4ed8}}</style>
</head><body><div class="banner">Staging draft — not approved for production publishing. <a href="/qa-dashboard.html">QA dashboard</a></div>
{md_to_html(body)}
</body></html>'''
    (public / f"{slug}.html").write_text(doc, encoding="utf-8")
    is_sample = "ai-meeting-notes-workflow" in slug
    pages.append((title, f"{slug}.html", is_sample))

pilot_pages = [p for p in pages if not p[2]]
sample_pages = [p for p in pages if p[2]]
index = "<h1>SEO/GEO Sites Staging</h1>"
index += "<p><strong>Status:</strong> staging preview only; production publishing remains blocked until review.</p>"
index += '<p><a href="qa-dashboard.html">Open QA dashboard</a></p>'
index += "<h2>Pilot staging pages</h2><ul>" + "".join(
    f'<li><a href="{href}">{html.escape(title)}</a></li>' for title, href, _ in pilot_pages
) + "</ul>"
index += "<h2>Sample/demo pages</h2><p>These are pipeline examples, not final niche decisions.</p><ul>" + "".join(
    f'<li><a href="{href}">{html.escape(title)}</a></li>' for title, href, _ in sample_pages
) + "</ul>"
(public / "index.html").write_text(
    f'<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>SEO/GEO Sites Staging</title><style>body{{font-family:system-ui,sans-serif;max-width:860px;margin:40px auto;line-height:1.65;padding:0 20px}}</style></head><body>{index}</body></html>',
    encoding="utf-8",
)
(public / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
(public / "sitemap.xml").write_text(
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
    + "".join(f"  <url><loc>/{html.escape(href)}</loc><lastmod>{date.today()}</lastmod></url>\n" for _, href, _ in pages)
    + "</urlset>\n",
    encoding="utf-8",
)
print(f"Built {len(pages)} page(s) into {public}")
