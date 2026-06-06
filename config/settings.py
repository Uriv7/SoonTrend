"""
SoonTrend V2 — Master Configuration
8 articles per run × 3 runs/day = 24 articles/day
4 regular SEO articles + 4 NewsArticles per run
"""
import os

SITE_URL      = "https://soontrend.com"
SITE_NAME     = "SoonTrend"
SITE_TAGLINE  = "Trending Topics, Instantly Explained"

# ── Google Monetisation ────────────────────────────────────────────────────────
GOOGLE_ADS_CLIENT      = os.environ.get("GOOGLE_ADS_CLIENT",      "ca-pub-XXXXXXXXXXXXXXXX")
GOOGLE_ADS_SLOT_TOP    = os.environ.get("GOOGLE_ADS_SLOT_TOP",    "1111111111")
GOOGLE_ADS_SLOT_MID    = os.environ.get("GOOGLE_ADS_SLOT_MID",    "2222222222")
GOOGLE_ADS_SLOT_BOTTOM = os.environ.get("GOOGLE_ADS_SLOT_BOTTOM", "3333333333")
GOOGLE_ADS_SLOT_STICKY = os.environ.get("GOOGLE_ADS_SLOT_STICKY", "4444444444")
GOOGLE_ANALYTICS_ID    = os.environ.get("GOOGLE_ANALYTICS_ID",    "G-XXXXXXXXXX")

# ── HIGH RPM COUNTRIES ─────────────────────────────────────────────────────────
HIGH_RPM_COUNTRIES = {
    "United States":"US","United Kingdom":"GB","Australia":"AU",
    "Canada":"CA","Switzerland":"CH","Norway":"NO","Sweden":"SE",
    "Denmark":"DK","Netherlands":"NL","Germany":"DE","Finland":"FI",
    "Austria":"AT","Ireland":"IE","New Zealand":"NZ","Belgium":"BE",
    "Luxembourg":"LU","Singapore":"SG","Hong Kong":"HK","Japan":"JP",
    "India":"IN",
}
SECONDARY_COUNTRIES = {
    "UAE":"AE","Qatar":"QA","Israel":"IL","South Korea":"KR",
    "France":"FR","Italy":"IT","Spain":"ES",
}
COUNTRIES = {**HIGH_RPM_COUNTRIES, **SECONDARY_COUNTRIES}

# ── Content sources ────────────────────────────────────────────────────────────
NEWS_API_KEY  = os.environ.get("NEWS_API_KEY",  "")
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")

# ── V2: 8 per run (4 Article + 4 NewsArticle), 3 runs/day = 24/day ────────────
MAX_PAGES_PER_RUN      = 8   # total per run
ARTICLES_PER_RUN       = 4   # regular evergreen SEO articles
NEWS_ARTICLES_PER_RUN  = 4   # breaking news articles
TOPICS_PER_COUNTRY     = 2
API_SLEEP_SECONDS      = 3

# ── AI providers ──────────────────────────────────────────────────────────────
GEMINI_API_KEY        = os.environ.get("GEMINI_API_KEY",  "")
GROQ_API_KEY          = os.environ.get("GROQ_API_KEY",    "")
GEMINI_MODEL          = "gemini-1.5-flash-latest"
GEMINI_MODEL_FALLBACK = "gemini-1.5-flash-8b-latest"
GROQ_MODEL            = "llama-3.1-8b-instant"
GROQ_MODEL_FALLBACK   = "llama-3.3-70b-versatile"
GEMINI_DAILY_LIMIT    = 1400

# ── Paths ──────────────────────────────────────────────────────────────────────
GEMINI_USAGE_FILE = "backend/data/gemini_usage.json"
PUBLISHED_FILE    = "backend/data/published.json"
ARTICLES_DIR      = "docs/articles"
SITEMAP_FILE      = "docs/sitemap.xml"
