"""SoonTrend V2 — Builder. Handles Article + NewsArticle content types."""
import json, os, sys
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from jinja2 import Environment, FileSystemLoader
from config.settings import (
    SITE_URL, SITE_NAME, ARTICLES_DIR, PUBLISHED_FILE,
    GOOGLE_ADS_CLIENT, GOOGLE_ADS_SLOT_TOP, GOOGLE_ADS_SLOT_MID,
    GOOGLE_ADS_SLOT_BOTTOM, GOOGLE_ADS_SLOT_STICKY, GOOGLE_ANALYTICS_ID
)

TMPL_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'templates')
env = Environment(loader=FileSystemLoader(TMPL_DIR), autoescape=True)
env.globals['enumerate'] = enumerate


def _load_published() -> list:
    if not os.path.exists(PUBLISHED_FILE):
        return []
    with open(PUBLISHED_FILE) as f:
        return json.load(f)


def _shared():
    return {
        "site_url":        SITE_URL,
        "site_name":       SITE_NAME,
        "ads_client":      GOOGLE_ADS_CLIENT,
        "ads_slot_top":    GOOGLE_ADS_SLOT_TOP,
        "ads_slot_mid":    GOOGLE_ADS_SLOT_MID,
        "ads_slot_bottom": GOOGLE_ADS_SLOT_BOTTOM,
        "ads_slot_sticky": GOOGLE_ADS_SLOT_STICKY,
        "ga_id":           GOOGLE_ANALYTICS_ID,
        "today":           str(date.today()),
    }


def _related(slug, tags, cat, all_arts, n=6):
    tag_set = set(t.lower() for t in tags)
    scored  = []
    for a in all_arts:
        if a["slug"] == slug:
            continue
        score = sum(2 for t in a.get("tags",[]) if t.lower() in tag_set)
        if a.get("category") == cat:
            score += 1
        if score > 0:
            scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:n]]


def _sidebar(slug, all_arts, n=8):
    return sorted(
        [a for a in all_arts if a["slug"] != slug],
        key=lambda x: x.get("date",""), reverse=True
    )[:n]


def build_article_page(article: dict) -> str:
    all_arts = _load_published()
    ctx = _shared()
    ctx.update({
        "data":               article,
        "published_date":     str(date.today()),
        "published_datetime": f"{date.today()}T00:00:00Z",
        "related_articles":   _related(article["slug"], article.get("tags",[]),
                                        article.get("category",""), all_arts),
        "sidebar_latest":     _sidebar(article["slug"], all_arts),
    })
    html = env.get_template("article.html").render(**ctx)
    out  = os.path.join(ARTICLES_DIR, article["slug"])
    os.makedirs(out, exist_ok=True)
    ctype = article.get("content_type","article")
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    icon = "⚡" if ctype == "news" else "📄"
    print(f"  {icon} /articles/{article['slug']}/ [{ctype}]")
    return article["slug"]


def build_homepage():
    all_arts = sorted(_load_published(), key=lambda x: x.get("date",""), reverse=True)
    ctx = _shared()
    ctx.update({"articles": all_arts[:40], "total_count": len(all_arts)})
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html","w",encoding="utf-8") as f:
        f.write(env.get_template("index.html").render(**ctx))
    news_count = sum(1 for a in all_arts if a.get("content_type") == "news")
    print(f"  🏠 Homepage ({len(all_arts)} articles, {news_count} news)")


def build_topics_page():
    all_arts = sorted(_load_published(), key=lambda x: x.get("date",""), reverse=True)
    by_cat: dict = {}
    for a in all_arts:
        by_cat.setdefault(a.get("category","Other"), []).append(a)
    ctx = _shared()
    ctx.update({"by_category": by_cat, "total": len(all_arts),
                "cat_count": len(by_cat), "year": str(date.today())[:4]})
    os.makedirs("docs/topics", exist_ok=True)
    with open("docs/topics/index.html","w",encoding="utf-8") as f:
        f.write(env.get_template("topics.html").render(**ctx))
    print(f"  📚 Topics ({len(by_cat)} categories)")


def build_static_pages():
    ctx = _shared()
    for name in ("privacy","terms","about","contact"):
        os.makedirs(f"docs/{name}", exist_ok=True)
        with open(f"docs/{name}/index.html","w",encoding="utf-8") as f:
            f.write(env.get_template(f"{name}.html").render(**ctx))
    print("  📋 Static: privacy, terms, about, contact")
