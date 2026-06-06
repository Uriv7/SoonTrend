"""
SoonTrend V2 — Master Orchestrator
3× daily via GitHub Actions.
Each run: 4 deep SEO Articles + 4 Breaking NewsArticles = 8 pages
Total: 24 pages/day, 720/month
"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__))

from backend.generator.trends    import get_trending_topics
from backend.generator.content   import generate_article, generate_news_article
from backend.generator.builder   import (build_article_page, build_homepage,
                                          build_topics_page, build_static_pages)
from backend.generator.sitemap   import rebuild_sitemap
from backend.generator.publisher import mark_published, git_commit_and_push
from config.settings             import ARTICLES_PER_RUN, NEWS_ARTICLES_PER_RUN, API_SLEEP_SECONDS


def run():
    print("\n" + "═"*60)
    print("  🚀  SoonTrend V2 — Daily Auto-Publisher")
    print(f"  📋  Plan: {ARTICLES_PER_RUN} Articles + {NEWS_ARTICLES_PER_RUN} NewsArticles")
    print("═"*60 + "\n")

    # ── 1. Fetch all topics ─────────────────────────────────────────────────
    print("📡  [1/5] Fetching topics from all sources...")
    topics = get_trending_topics(max_total=(ARTICLES_PER_RUN + NEWS_ARTICLES_PER_RUN) * 3)

    evergreen_pool = topics.get("evergreen", [])
    breaking_pool  = topics.get("breaking",  [])

    if not evergreen_pool and not breaking_pool:
        print("  ℹ️  No new topics found. Exiting."); return

    # ── 2. Generate articles ────────────────────────────────────────────────
    print(f"\n✍️   [2/5] Generating articles...")
    published_topics = []

    # 4 Deep SEO Articles
    print(f"\n  📘 Generating {ARTICLES_PER_RUN} SEO Articles...")
    for item in evergreen_pool[:ARTICLES_PER_RUN]:
        topic = item["topic"]
        print(f"\n    📝 [Article] {topic}")
        try:
            article = generate_article(topic)
            article["content_type"] = "article"
            build_article_page(article)
            mark_published(article)
            published_topics.append(f"[Article] {topic}")
            time.sleep(API_SLEEP_SECONDS)
        except Exception as e:
            print(f"    ❌ Skipped: {e}")
            continue

    # 4 Breaking NewsArticles
    print(f"\n  📰 Generating {NEWS_ARTICLES_PER_RUN} NewsArticles...")
    for item in breaking_pool[:NEWS_ARTICLES_PER_RUN]:
        topic = item["topic"]
        print(f"\n    ⚡ [News] {topic}")
        try:
            article = generate_news_article(topic)
            article["content_type"] = "news"
            build_article_page(article)
            mark_published(article)
            published_topics.append(f"[News] {topic}")
            time.sleep(API_SLEEP_SECONDS)
        except Exception as e:
            print(f"    ❌ Skipped: {e}")
            continue

    if not published_topics:
        print("\n  ⚠️  No articles generated this run."); return

    # ── 3. Rebuild homepage ─────────────────────────────────────────────────
    print(f"\n🏠  [3/5] Rebuilding homepage...")
    build_homepage()

    # ── 4. Rebuild topics + static pages ───────────────────────────────────
    print(f"\n📚  [4/5] Rebuilding topics + static pages...")
    build_topics_page()
    build_static_pages()

    # ── 5. Sitemap + push → Cloudflare ─────────────────────────────────────
    print(f"\n🗺️   [5/5] Sitemap → GitHub push → Cloudflare deploy...")
    rebuild_sitemap()
    git_commit_and_push(published_topics)

    print("\n" + "═"*60)
    print(f"  ✅  Published {len(published_topics)} pages this run:")
    for t in published_topics:
        print(f"       → {t}")
    print("═"*60 + "\n")


if __name__ == "__main__":
    run()
