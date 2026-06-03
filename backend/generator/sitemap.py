"""
backend/generator/sitemap.py
Rebuilds docs/sitemap.xml and docs/robots.txt from all published articles.
"""
import glob, json, os, sys
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import SITE_URL, SITEMAP_FILE, PUBLISHED_FILE


def rebuild_sitemap():
    # Build slug→date lookup
    pub_dates = {}
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE) as f:
            for e in json.load(f):
                pub_dates[e["slug"]] = e.get("date", str(date.today()))

    pages = sorted(glob.glob("docs/articles/*/index.html"))
    today = str(date.today())
    urls  = []

    # Static pages
    statics = [
        ("/",         "1.0", "daily"),
        ("/topics/",  "0.9", "daily"),
        ("/privacy/", "0.5", "monthly"),
        ("/terms/",   "0.5", "monthly"),
    ]
    for path, pri, freq in statics:
        urls.append(f"  <url><loc>{SITE_URL}{path}</loc>"
                    f"<lastmod>{today}</lastmod>"
                    f"<changefreq>{freq}</changefreq>"
                    f"<priority>{pri}</priority></url>")

    # Article pages
    for page in pages:
        # Normalise path separator for Windows/Linux
        parts = page.replace("\\", "/").split("/")
        slug  = parts[2]          # docs/articles/SLUG/index.html
        lm    = pub_dates.get(slug, today)
        urls.append(f"  <url><loc>{SITE_URL}/articles/{slug}/</loc>"
                    f"<lastmod>{lm}</lastmod>"
                    f"<changefreq>monthly</changefreq>"
                    f"<priority>0.8</priority></url>")

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) +
           "\n</urlset>")

    os.makedirs("docs", exist_ok=True)
    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(xml)

    with open("docs/robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    print(f"  🗺️  Sitemap: {len(pages)} articles + {len(statics)} static pages")
