"""
SoonTrend V2 — Maximum SEO Sitemap System

Generates:
  1. docs/sitemap.xml          — main sitemap index
  2. docs/sitemap-articles.xml — all article URLs
  3. docs/sitemap-static.xml   — homepage, topics, about, contact
  4. docs/robots.txt           — optimised for Googlebot
  5. Auto-pings Google + Bing  — every single update

Sitemap rebuilds on EVERY run = Google always knows about new content.
NewsArticles = daily changefreq (crawled faster by Google).
"""
import glob, json, os, sys, urllib.request, urllib.parse
from datetime import date, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import SITE_URL, PUBLISHED_FILE


# ── Helpers ───────────────────────────────────────────────────────────────────
def _now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _url(loc, lastmod, changefreq, priority, news_title=None, news_date=None):
    """Build a <url> block. Adds Google News tags for news articles."""
    lines = [
        f"  <url>",
        f"    <loc>{loc}</loc>",
        f"    <lastmod>{lastmod}</lastmod>",
        f"    <changefreq>{changefreq}</changefreq>",
        f"    <priority>{priority}</priority>",
    ]
    if news_title and news_date:
        lines += [
            f"    <news:news>",
            f"      <news:publication>",
            f"        <news:name>SoonTrend</news:name>",
            f"        <news:language>en</news:language>",
            f"      </news:publication>",
            f"      <news:publication_date>{news_date}</news:publication_date>",
            f"      <news:title>{news_title}</news:title>",
            f"    </news:news>",
        ]
    lines.append("  </url>")
    return "\n".join(lines)


def _sitemap_wrap(urls: list, extra_ns: str = "") -> str:
    ns = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    if extra_ns:
        ns += f"\n        {extra_ns}"
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset {ns}>\n'
            + "\n".join(urls) +
            '\n</urlset>')


def _ping_search_engines(sitemap_url: str):
    """Notify Google and Bing about the updated sitemap."""
    engines = [
        f"https://www.google.com/ping?sitemap={urllib.parse.quote(sitemap_url, safe='')}",
        f"https://www.bing.com/ping?sitemap={urllib.parse.quote(sitemap_url, safe='')}",
    ]
    for ping_url in engines:
        try:
            req = urllib.request.Request(ping_url,
                headers={"User-Agent": "SoonTrend/2.0 Sitemap Notifier"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                engine = "Google" if "google" in ping_url else "Bing"
                print(f"    ✅ Pinged {engine}: HTTP {resp.status}")
        except Exception as e:
            engine = "Google" if "google" in ping_url else "Bing"
            print(f"    ⚠️  Could not ping {engine}: {e}")


def rebuild_sitemap():
    """
    Full sitemap rebuild. Called after EVERY content generation run.
    Automatically notifies Google and Bing of new content.
    """
    # Load published article metadata
    pub_info = {}
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE) as f:
            for e in json.load(f):
                pub_info[e["slug"]] = {
                    "date":    e.get("date", str(date.today())),
                    "ctype":   e.get("content_type", "article"),
                    "title":   e.get("title", ""),
                    "cat":     e.get("category", ""),
                }

    pages = sorted(glob.glob("docs/articles/*/index.html"))
    today = str(date.today())
    now   = _now()
    os.makedirs("docs", exist_ok=True)

    # ── 1. Static pages sitemap ───────────────────────────────────────────────
    static_pages = [
        ("/",          "1.0", "daily"),
        ("/topics/",   "0.9", "daily"),
        ("/about/",    "0.6", "monthly"),
        ("/contact/",  "0.5", "monthly"),
        ("/privacy/",  "0.3", "monthly"),
        ("/terms/",    "0.3", "monthly"),
    ]
    static_urls = [
        _url(f"{SITE_URL}{path}", today, freq, pri)
        for path, pri, freq in static_pages
    ]
    with open("docs/sitemap-static.xml", "w") as f:
        f.write(_sitemap_wrap(static_urls))

    # ── 2. Articles sitemap (with Google News tags for news articles) ─────────
    article_urls = []
    for page in pages:
        slug  = page.replace("\\", "/").split("/")[2]
        info  = pub_info.get(slug, {})
        lm    = info.get("date", today)
        ctype = info.get("ctype", "article")
        title = info.get("title", "")

        # News articles: daily crawl, priority 0.9, Google News tags
        if ctype == "news":
            article_urls.append(_url(
                f"{SITE_URL}/articles/{slug}/",
                lm, "daily", "0.9",
                news_title=title,
                news_date=f"{lm}T00:00:00Z"
            ))
        else:
            article_urls.append(_url(
                f"{SITE_URL}/articles/{slug}/",
                lm, "weekly", "0.8"
            ))

    news_ns = 'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"'
    with open("docs/sitemap-articles.xml", "w") as f:
        f.write(_sitemap_wrap(article_urls, extra_ns=news_ns))

    # ── 3. Sitemap index (master file pointing to both sitemaps) ─────────────
    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <sitemap>\n'
        f'    <loc>{SITE_URL}/sitemap-static.xml</loc>\n'
        f'    <lastmod>{today}</lastmod>\n'
        f'  </sitemap>\n'
        f'  <sitemap>\n'
        f'    <loc>{SITE_URL}/sitemap-articles.xml</loc>\n'
        f'    <lastmod>{today}</lastmod>\n'
        f'  </sitemap>\n'
        f'</sitemapindex>'
    )
    with open("docs/sitemap.xml", "w") as f:
        f.write(sitemap_index)

    # ── 4. Robots.txt — maximised for Googlebot ───────────────────────────────
    robots = f"""User-agent: *
Allow: /

# Priority crawl paths
Allow: /articles/
Allow: /topics/
Allow: /about/

# Block non-content paths
Disallow: /assets/
Disallow: /*.json$

# Sitemaps
Sitemap: {SITE_URL}/sitemap.xml
Sitemap: {SITE_URL}/sitemap-articles.xml
Sitemap: {SITE_URL}/sitemap-static.xml

# Crawl delay for bots other than Googlebot
User-agent: *
Crawl-delay: 1
"""
    with open("docs/robots.txt", "w") as f:
        f.write(robots)

    # ── 5. Ping Google + Bing automatically ───────────────────────────────────
    print(f"  🗺️  Sitemap: {len(pages)} articles, {len(static_pages)} static pages")
    print(f"  📡 Pinging search engines...")
    _ping_search_engines(f"{SITE_URL}/sitemap.xml")
    _ping_search_engines(f"{SITE_URL}/sitemap-articles.xml")
