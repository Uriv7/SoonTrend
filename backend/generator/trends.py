"""
backend/generator/trends.py
Fetches trending topics using Google Trends RSS feeds (always free, no API needed).
Falls back to a curated evergreen topic list if RSS also fails.
Country codes only used internally — never shown on published pages.
"""
import json, os, sys, time, random, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import PUBLISHED_FILE

try:
    import requests
except ImportError:
    import urllib.request as requests


# ── Country RSS feeds (Google Trends daily trending RSS) ─────────────────────
TREND_FEEDS = {
    "US": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
    "IN": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
    "GB": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=GB",
    "AU": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=AU",
    "CA": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=CA",
    "DE": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=DE",
    "FR": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=FR",
    "JP": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=JP",
    "KR": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
    "SG": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=SG",
    "NL": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=NL",
    "SE": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=SE",
    "NO": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=NO",
    "DK": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=DK",
    "FI": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=FI",
    "CH": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=CH",
    "AT": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=AT",
    "BE": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=BE",
    "IE": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IE",
    "NZ": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=NZ",
    "IT": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IT",
    "ES": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=ES",
    "PL": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=PL",
    "CZ": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=CZ",
    "AE": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=AE",
    "SA": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=SA",
    "QA": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=QA",
    "IL": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IL",
    "HK": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=HK",
    "IS": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IS",
}

# ── Evergreen fallback topics (used if ALL RSS feeds fail) ───────────────────
FALLBACK_TOPICS = [
    "Artificial Intelligence", "Climate Change", "Quantum Computing",
    "Electric Vehicles", "Cryptocurrency", "Space Exploration",
    "Mental Health Awareness", "Renewable Energy", "Cybersecurity",
    "Remote Work", "Machine Learning", "Blockchain Technology",
    "Gene Editing", "Autonomous Vehicles", "Social Media Trends",
    "Inflation and Economy", "5G Technology", "NFTs and Digital Art",
    "Sustainable Living", "Virtual Reality", "ChatGPT",
    "Weight Loss Drugs", "Cancer Research", "Antibiotic Resistance",
    "Nuclear Fusion", "Carbon Capture", "Microplastics",
    "Deepfake Technology", "Brain-Computer Interface", "Longevity Science",
]


def _load_published_topics() -> set:
    if not os.path.exists(PUBLISHED_FILE):
        return set()
    with open(PUBLISHED_FILE) as f:
        return {e.get("topic", "").lower() for e in json.load(f)}


def _parse_rss(xml_text: str) -> list:
    """Extract <title> tags from RSS XML, skip the feed title (first one)."""
    titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', xml_text)
    if not titles:
        # Try plain title tags
        titles = re.findall(r'<title>(.*?)</title>', xml_text)
        titles = titles[1:]  # skip feed title
    return [t.strip() for t in titles if t.strip() and len(t.strip()) > 3]


def _fetch_rss(url: str, timeout: int = 10) -> list:
    """Fetch and parse a Google Trends RSS feed. Returns list of topic strings."""
    try:
        import requests as req_lib
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SoonTrend/1.0; +https://soontrend.com)",
            "Accept": "application/rss+xml, application/xml, text/xml",
        }
        resp = req_lib.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return _parse_rss(resp.text)
    except Exception:
        pass
    return []


def get_trending_topics(max_total: int = 20) -> list:
    """
    Returns list of dicts: [{"topic": str, "source_code": str}]
    source_code is used only internally — NEVER shown on pages.
    """
    published = _load_published_topics()
    collected = []
    seen      = set(published)

    feed_list = list(TREND_FEEDS.items())
    random.shuffle(feed_list)

    rss_success = 0

    for code, url in feed_list:
        if len(collected) >= max_total * 2:
            break
        print(f"  🌐 [{code}] Fetching RSS...")
        topics = _fetch_rss(url)
        if topics:
            rss_success += 1
            for t in topics[:5]:
                key = t.lower().strip()
                if key not in seen and len(t) > 3:
                    collected.append({"topic": t.strip(), "source_code": code})
                    seen.add(key)
        else:
            print(f"  ⚠️  [{code}] RSS returned no results")
        time.sleep(random.uniform(0.5, 1.2))

    # ── Fallback: use evergreen topics if RSS completely failed ───────────────
    if not collected:
        print("  ⚠️  All RSS feeds failed — using evergreen topic fallback")
        random.shuffle(FALLBACK_TOPICS)
        for t in FALLBACK_TOPICS:
            key = t.lower().strip()
            if key not in seen:
                collected.append({"topic": t, "source_code": "FALLBACK"})
                seen.add(key)
            if len(collected) >= max_total:
                break

    random.shuffle(collected)
    result = collected[:max_total]
    print(f"✅ {len(result)} new topics found ({rss_success} RSS feeds succeeded)")
    return result
