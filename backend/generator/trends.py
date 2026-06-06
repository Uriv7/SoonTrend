"""
SoonTrend V2 — Multi-source trend fetcher.
Sources: Reddit + Wikipedia + HackerNews + GNews + NewsAPI + Evergreen fallback
Scores topics by RPM potential (Finance/Health/Tech = highest).
Returns 2 batches: evergreen topics + breaking news topics.
"""
import json, os, sys, time, random, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import PUBLISHED_FILE, NEWS_API_KEY, GNEWS_API_KEY

try:
    import requests as req
except ImportError:
    req = None

SUBREDDITS_NEWS = ["worldnews","news","UpliftingNews","technology","science","business","health"]
SUBREDDITS_NICHE = ["personalfinance","investing","environment","Futurology","medicine","artificial"]

HIGH_RPM_KEYWORDS = [
    "stock","market","invest","bitcoin","crypto","mortgage","insurance","loan",
    "credit","bank","tax","fund","economy","inflation","interest rate","401k",
    "health","cancer","treatment","drug","medical","disease","therapy","mental",
    "diet","weight","fitness","vaccine","surgery","diabetes","heart",
    "ai","artificial intelligence","tech","cyber","software","electric vehicle",
    "quantum","robot","autonomous","space","energy","climate",
    "lawyer","lawsuit","legal","court","settlement","attorney","lawsuit",
]

EVERGREEN_HIGH_RPM = [
    "Stock Market Outlook","Bitcoin Price Analysis","Mortgage Rate Changes",
    "Best High Yield Savings Accounts","Federal Reserve Interest Rate Decision",
    "Artificial Intelligence in Healthcare","Cancer Research Breakthrough",
    "Electric Vehicle Tax Credit","Climate Change Solutions",
    "Cybersecurity Threats","Mental Health Treatment","Weight Loss Science",
    "Renewable Energy Costs","Gene Therapy Advances","Autonomous Vehicle Safety",
    "Cryptocurrency Regulation","Life Insurance Guide","College Tuition Costs",
    "Remote Work Productivity","Social Media Mental Health Impact",
    "Antibiotic Resistance Crisis","Nuclear Fusion Progress",
    "Quantum Computing Applications","5G Technology Impact",
    "Personal Finance Tips","Retirement Planning Guide",
]

BREAKING_FALLBACK = [
    "Major Tech Company Layoffs","AI Regulation Update","Climate Summit Results",
    "Central Bank Policy Change","Healthcare System Reform","Space Mission Update",
    "Cybersecurity Data Breach","Electric Vehicle Market Shift",
    "Global Supply Chain Crisis","Inflation Economic Impact",
    "Social Media Platform Changes","Renewable Energy Record",
    "Medical Research Discovery","Stock Market Volatility",
    "Technology Antitrust Case",
]


def _load_published() -> set:
    if not os.path.exists(PUBLISHED_FILE):
        return set()
    with open(PUBLISHED_FILE) as f:
        return {e.get("topic","").lower() for e in json.load(f)}


def _get(url, timeout=10, headers=None):
    if req is None:
        return None
    try:
        h = {"User-Agent": "SoonTrend/2.0 (+https://soontrend.com)"}
        if headers:
            h.update(headers)
        r = req.get(url, headers=h, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _reddit_topics() -> list:
    topics = []
    subs = SUBREDDITS_NEWS + SUBREDDITS_NICHE
    random.shuffle(subs)
    for sub in subs[:6]:
        data = _get(f"https://www.reddit.com/r/{sub}/hot.json?limit=8")
        if not data:
            continue
        for post in data.get("data", {}).get("children", []):
            t = post.get("data", {}).get("title", "").strip()
            t = re.sub(r'\[.*?\]|\(.*?\)', '', t).strip()
            t = re.sub(r'\s+', ' ', t)
            if 15 < len(t) < 90 and not t.endswith('?'):
                topics.append(t)
        time.sleep(0.4)
    print(f"  📱 Reddit: {len(topics)} topics")
    return topics


def _wikipedia_topics() -> list:
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y/%m/%d")
    data = _get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{yesterday}")
    if not data:
        return []
    articles = data.get("items", [{}])[0].get("articles", [])
    skip = {"Main_Page","Special:","Wikipedia:","Portal:","File:","Help:"}
    topics = []
    for art in articles[:60]:
        title = art.get("article","").replace("_"," ")
        if not any(s in title for s in skip) and len(title) > 5:
            topics.append(title)
    print(f"  📖 Wikipedia: {len(topics)} topics")
    return topics


def _hackernews_topics() -> list:
    data = _get("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not data:
        return []
    topics = []
    for sid in data[:15]:
        story = _get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if story and story.get("type") == "story":
            t = story.get("title","").strip()
            if t and len(t) > 10:
                topics.append(t)
        time.sleep(0.08)
    print(f"  💻 HackerNews: {len(topics)} topics")
    return topics


def _gnews_topics() -> list:
    if not GNEWS_API_KEY:
        return []
    topics = []
    for cat in ["general","technology","business","health"]:
        data = _get(f"https://gnews.io/api/v4/top-headlines?category={cat}&lang=en&country=us&max=5&apikey={GNEWS_API_KEY}")
        if data:
            for art in data.get("articles",[]):
                t = art.get("title","").split(" - ")[0].strip()
                if t and len(t) > 15:
                    topics.append(t)
        time.sleep(0.4)
    print(f"  📰 GNews: {len(topics)} topics")
    return topics


def _newsapi_topics() -> list:
    if not NEWS_API_KEY:
        return []
    data = _get(f"https://newsapi.org/v2/top-headlines?language=en&pageSize=20&apiKey={NEWS_API_KEY}",
                headers={"X-Api-Key": NEWS_API_KEY})
    if not data:
        return []
    topics = []
    for art in data.get("articles",[]):
        t = art.get("title","").split(" - ")[0].strip()
        if t and len(t) > 15:
            topics.append(t)
    print(f"  🗞️  NewsAPI: {len(topics)} topics")
    return topics


def _score(topic: str) -> int:
    t = topic.lower()
    score = 0
    for kw in HIGH_RPM_KEYWORDS:
        if kw in t:
            score += 2
    if len(topic) < 65:
        score += 1
    return score


def get_trending_topics(max_total: int = 24) -> dict:
    """
    Returns dict with two lists:
      - 'evergreen': topics for deep SEO articles
      - 'breaking': topics for NewsArticle (viral, urgent)
    Both scored by RPM potential.
    """
    published = _load_published()
    seen      = set(published)

    print("  📡 Fetching from all sources...")
    raw = []
    for fn in [_reddit_topics, _wikipedia_topics, _hackernews_topics,
               _gnews_topics, _newsapi_topics]:
        try:
            topics = fn()
            raw.extend(topics)
        except Exception as e:
            print(f"  ⚠️  Source failed: {e}")

    # Deduplicate
    unique = []
    seen_lower = set(seen)
    for t in raw:
        key = t.lower().strip()
        if key not in seen_lower and len(t) > 5:
            unique.append(t)
            seen_lower.add(key)

    scored = sorted(unique, key=_score, reverse=True)

    # Split: top half = breaking news, bottom = evergreen
    half = max_total // 2

    # Fallback if sources failed
    if len(scored) < half:
        print("  ⚠️  Insufficient live topics — using fallback lists")
        random.shuffle(EVERGREEN_HIGH_RPM)
        random.shuffle(BREAKING_FALLBACK)
        for t in EVERGREEN_HIGH_RPM:
            if t.lower() not in seen_lower:
                scored.append(t); seen_lower.add(t.lower())
        for t in BREAKING_FALLBACK:
            if t.lower() not in seen_lower:
                scored.append(t); seen_lower.add(t.lower())

    # Breaking = higher scored (more current/viral), evergreen = rest
    breaking  = [{"topic": t, "source_code": "MULTI"} for t in scored[:half]]
    evergreen = [{"topic": t, "source_code": "MULTI"} for t in scored[half:half*2]]

    print(f"✅ {len(breaking)} breaking + {len(evergreen)} evergreen topics ready")
    return {"breaking": breaking, "evergreen": evergreen}
