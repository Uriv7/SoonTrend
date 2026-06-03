"""
backend/generator/trends.py
Fetches trending topics from Google Trends across all 30 countries.
Country is used ONLY to pick which region to query — never shown on pages.
"""
import json, os, sys, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from pytrends.request import TrendReq
from config.settings  import COUNTRIES, TOPICS_PER_COUNTRY, PUBLISHED_FILE


def _load_published_topics() -> set:
    if not os.path.exists(PUBLISHED_FILE):
        return set()
    with open(PUBLISHED_FILE) as f:
        return {e.get("topic", "").lower() for e in json.load(f)}


def get_trending_topics(max_total: int = 20) -> list:
    """
    Returns list of dicts: [{"topic": str, "source_code": str}]
    source_code is only used to rotate Google Trends regions — never displayed.
    """
    published  = _load_published_topics()
    pytrends   = TrendReq(hl="en-US", tz=0, timeout=(10, 25), retries=2, backoff_factor=0.5)
    collected  = []
    seen       = set(published)
    countries  = list(COUNTRIES.items())
    random.shuffle(countries)           # Rotate so all countries get equal coverage over time

    for country_name, code in countries:
        try:
            print(f"  🌐 [{code}] {country_name}")
            df     = pytrends.trending_searches(pn=code)
            topics = df[0].tolist()
            added  = 0
            for t in topics:
                if added >= TOPICS_PER_COUNTRY:
                    break
                key = t.lower().strip()
                if key not in seen and len(t) > 3:
                    collected.append({"topic": t.strip(), "source_code": code})
                    seen.add(key)
                    added += 1
            time.sleep(random.uniform(1.5, 2.5))
        except Exception as e:
            print(f"  ⚠️  [{code}] Failed: {e}")
            continue
        if len(collected) >= max_total * 2:
            break

    random.shuffle(collected)
    result = collected[:max_total]
    print(f"✅ {len(result)} new topics found")
    return result
