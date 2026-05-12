from pathlib import Path
import html
import json
import re

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


def md_to_html(md):
    lines = []
    for line in md.splitlines():
        if line.startswith("# "):
            lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif re.match(r"^\d+\. ", line):
            lines.append(f'<p class="step">{html.escape(line)}</p>')
        elif line.startswith("- "):
            lines.append(f'<p class="bullet">• {html.escape(line[2:])}</p>')
        elif line.strip():
            lines.append(f"<p>{html.escape(line)}</p>")
    return "\n".join(lines)


pages = []
for p in (root / "content/sites").glob("*/pages/*.md"):
    meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    title = meta.get("title", p.stem)
    slug = meta.get("slug", p.stem)
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "dateModified": meta.get("last_reviewed", ""),
    }
    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="Staging SEO/GEO knowledge asset: {html.escape(title)}">
<script type="application/ld+json">{json.dumps(article)}</script>
<style>body{{font-family:system-ui,sans-serif;max-width:820px;margin:40px auto;line-height:1.65;padding:0 20px}} .banner{{background:#fff7ed;border:1px solid #fed7aa;padding:12px;border-radius:10px}} h1{{line-height:1.15}} .step,.bullet{{margin-left:1rem}}</style>
</head><body><div class="banner">Staging draft — not approved for production publishing.</div>
{md_to_html(body)}
</body></html>'''
    (public / f"{slug}.html").write_text(doc, encoding="utf-8")
    pages.append((title, f"{slug}.html"))

index = "<h1>SEO/GEO Sites Staging</h1><ul>" + "".join(
    f'<li><a href="{href}">{html.escape(title)}</a></li>' for title, href in pages
) + "</ul>"
(public / "index.html").write_text(
    f'<!doctype html><html><head><meta charset="utf-8"><title>SEO/GEO Sites Staging</title></head><body>{index}</body></html>',
    encoding="utf-8",
)
print(f"Built {len(pages)} page(s) into {public}")
