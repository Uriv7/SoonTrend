"""
SoonTrend — Master Configuration
Edit this file once, everything else is automatic.
"""
import os

# ── Site ──────────────────────────────────────────────────────────────────────
SITE_URL     = "https://soontrend.com"
SITE_NAME    = "SoonTrend"
SITE_TAGLINE = "Trending Topics, Instantly Explained"

# ── Google AdSense (fill after AdSense approval) ──────────────────────────────
GOOGLE_ADS_CLIENT     = os.environ.get("GOOGLE_ADS_CLIENT",     "ca-pub-XXXXXXXXXXXXXXXX")
GOOGLE_ADS_SLOT_TOP   = os.environ.get("GOOGLE_ADS_SLOT_TOP",   "1111111111")
GOOGLE_ADS_SLOT_MID   = os.environ.get("GOOGLE_ADS_SLOT_MID",   "2222222222")
GOOGLE_ADS_SLOT_BOTTOM= os.environ.get("GOOGLE_ADS_SLOT_BOTTOM","3333333333")

# ── Google Analytics (fill after GA4 setup) ───────────────────────────────────
GOOGLE_ANALYTICS_ID   = os.environ.get("GOOGLE_ANALYTICS_ID",   "G-XXXXXXXXXX")

# ── 30 Target countries (Google Trends codes) ─────────────────────────────────
COUNTRIES = {
    "India":          "IN", "United States":  "US", "Switzerland":    "CH",
    "Australia":      "AU", "Canada":         "CA", "United Kingdom": "GB",
    "Norway":         "NO", "Denmark":        "DK", "Sweden":         "SE",
    "Germany":        "DE", "Netherlands":    "NL", "Finland":        "FI",
    "Austria":        "AT", "Ireland":        "IE", "Luxembourg":     "LU",
    "New Zealand":    "NZ", "Belgium":        "BE", "Singapore":      "SG",
    "UAE":            "AE", "Qatar":          "QA", "Japan":          "JP",
    "South Korea":    "KR", "France":         "FR", "Israel":         "IL",
    "Saudi Arabia":   "SA", "Iceland":        "IS", "Hong Kong":      "HK",
    "Italy":          "IT", "Spain":          "ES", "Czech Republic": "CZ",
    "Poland":         "PL",
}

# ── Generation limits ─────────────────────────────────────────────────────────
MAX_PAGES_PER_RUN  = 5      # Articles generated per daily run
TOPICS_PER_COUNTRY = 3      # Trends fetched per country before dedup
API_SLEEP_SECONDS  = 4      # Pause between AI calls

# ── AI providers ─────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY",  "")
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY",    "")
GEMINI_MODEL     = "gemini-1.5-flash"
GROQ_MODEL       = "llama3-70b-8192"
GEMINI_DAILY_LIMIT = 1400

# ── Paths ─────────────────────────────────────────────────────────────────────
GEMINI_USAGE_FILE = "backend/data/gemini_usage.json"
PUBLISHED_FILE    = "backend/data/published.json"
ARTICLES_DIR      = "docs/articles"
SITEMAP_FILE      = "docs/sitemap.xml"
