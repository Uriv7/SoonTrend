"""
main.py — SoonTrend Master Orchestrator
Pipeline: Trends → AI (Gemini→Groq) → HTML → Sitemap → GitHub → Cloudflare
"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__))

from backend.generator.trends    import get_trending_topics
from backend.generator.content   import generate_article
from backend.generator.builder   import (build_article_page, build_homepage,
                                          build_topics_page, build_static_pages)
from backend.generator.sitemap   import rebuild_sitemap
from backend.generator.publisher import mark_published, git_commit_and_push
from config.settings             import MAX_PAGES_PER_RUN, API_SLEEP_SECONDS


def run():
    print("\n" + "═"*56)
    print("  🚀  SoonTrend — Daily Auto-Publisher")
    print("═"*56 + "\n")

    # ── 1. Fetch trending topics ───────────────────────────────────────────
    print("📡  [1/5] Fetching trends from 30 countries...")
    candidates = get_trending_topics(max_total=MAX_PAGES_PER_RUN * 3)
    if not candidates:
        print("  ℹ️  No new topics today. Exiting."); return

    # ── 2. Generate articles + build pages ────────────────────────────────
    print(f"\n✍️   [2/5] Generating up to {MAX_PAGES_PER_RUN} articles...")
    published_topics = []

    for item in candidates[:MAX_PAGES_PER_RUN]:
        topic = item["topic"]
        print(f"\n  📝  {topic}")
        try:
            article = generate_article(topic)   # No country in content
            build_article_page(article)          # No country on page
            mark_published(article)
            published_topics.append(topic)
            time.sleep(API_SLEEP_SECONDS)
        except Exception as e:
            print(f"  ❌  Skipped '{topic}': {e}")
            continue

    if not published_topics:
        print("\n  ⚠️  No articles generated this run."); return

    # ── 3. Rebuild homepage ────────────────────────────────────────────────
    print(f"\n🏠  [3/5] Rebuilding homepage...")
    build_homepage()

    # ── 4. Rebuild topics + static pages ──────────────────────────────────
    print(f"\n📚  [4/5] Rebuilding topics index + static pages...")
    build_topics_page()
    build_static_pages()

    # ── 5. Sitemap + push → triggers Cloudflare deploy ────────────────────
    print(f"\n🗺️   [5/5] Sitemap → GitHub push → Cloudflare deploy...")
    rebuild_sitemap()
    git_commit_and_push(published_topics)

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "═"*56)
    print(f"  ✅  Done! {len(published_topics)} article(s) published today:")
    for t in published_topics:
        print(f"       → {t}")
    print("═"*56 + "\n")


if __name__ == "__main__":
    run()
