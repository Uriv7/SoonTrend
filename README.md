# SoonTrend 🔥
**Trending Topics, Instantly Explained** — Fully automated SEO publishing engine.

Every day at 3 AM UTC (8:30 AM IST):
1. Fetches trending topics from Google Trends across 30 countries
2. Generates 1000+ word SEO articles via Gemini 1.5 Flash → Groq fallback (both free)
3. Builds static HTML pages with Schema.org, AdSense, FAQ, related articles
4. Rebuilds homepage, topics index, sitemap
5. Commits to GitHub → Cloudflare Pages auto-deploys

**Total cost: ₹0/month** (domain only)

---

## 🚀 Deployment — Step by Step

### Step 1 — Create GitHub Repo
1. Go to github.com → Sign up / log in
2. New repository → name: `soontrend` → Public → Create

### Step 2 — Upload Files
Upload ALL files from this zip maintaining folder structure.
For each file: go to the folder path → "Add file" → "Create new file" → type the path → paste content → Commit.

### Step 3 — Get Free API Keys

**Gemini (primary AI — 1500 req/day free):**
→ aistudio.google.com → Get API Key → Create API key

**Groq (fallback AI — free):**
→ console.groq.com → Sign up → API Keys → Create

### Step 4 — Add GitHub Secrets
Repo → Settings → Secrets and variables → Actions → New repository secret:

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | your Gemini key |
| `GROQ_API_KEY` | your Groq key |
| `CLOUDFLARE_API_TOKEN` | your Cloudflare token (Step 6) |
| `CLOUDFLARE_ACCOUNT_ID` | your Cloudflare account ID (Step 6) |

### Step 5 — Create Cloudflare Pages Project
1. Go to dash.cloudflare.com → Sign up free
2. Workers & Pages → Pages → Create a project
3. Choose "Direct Upload" → name it `soontrend` → Create
4. Upload the `docs/` folder manually for first deploy

### Step 6 — Get Cloudflare Credentials
**Account ID:**
→ dash.cloudflare.com → Right sidebar → "Account ID" → copy it

**API Token:**
→ dash.cloudflare.com → My Profile → API Tokens → Create Token
→ Use template "Edit Cloudflare Workers"
→ Add permission: Account → Cloudflare Pages → Edit
→ Create Token → copy it

### Step 7 — Connect Domain
In Cloudflare Pages → your project → Custom domains → Add `soontrend.com`
Cloudflare handles DNS and SSL automatically (it's your registrar or point NS to Cloudflare).

### Step 8 — First Run
Repo → Actions → "Daily Content Generator + Deploy" → Run workflow
Articles appear on soontrend.com within 3 minutes.

### Step 9 — Google Services
**Analytics:** analytics.google.com → Create property → copy G-XXXXXXXXXX → paste in config/settings.py
**Search Console:** search.google.com/search-console → Add property → Submit sitemap: https://soontrend.com/sitemap.xml
**AdSense:** adsense.google.com → Apply → wait approval (1-7 days) → get publisher ID + slot IDs → paste in config/settings.py

---

## 📁 File Structure

```
soontrend/
├── .github/workflows/
│   ├── generate.yml        ← runs daily 3AM UTC: fetch+generate+deploy
│   └── deploy.yml          ← runs on every push: redeploy to Cloudflare
├── backend/
│   ├── data/
│   │   ├── published.json          ← registry of all published articles
│   │   └── gemini_usage.json       ← daily Gemini quota tracker
│   └── generator/
│       ├── trends.py               ← Google Trends fetcher (30 countries)
│       ├── content.py              ← Gemini→Groq article generator
│       ├── builder.py              ← Jinja2 HTML builder
│       ├── sitemap.py              ← sitemap.xml + robots.txt
│       └── publisher.py            ← git commit + push
├── frontend/templates/
│   ├── article.html                ← full SEO article page
│   ├── index.html                  ← homepage
│   ├── topics.html                 ← all topics by category
│   ├── privacy.html                ← required for AdSense
│   └── terms.html
├── docs/                           ← Cloudflare Pages serves this
│   ├── index.html
│   ├── sitemap.xml
│   ├── robots.txt
│   └── articles/{slug}/index.html
├── config/settings.py              ← all config in one place
├── main.py                         ← master script
└── requirements.txt
```

---

## 💰 Free Tier Limits

| Service | Free Limit | Daily Usage |
|---|---|---|
| Gemini Flash API | 1,500 req/day | ~5 ✅ |
| Groq API | ~14,400 req/day | fallback only ✅ |
| GitHub Actions | 2,000 min/month | ~5 min/day ✅ |
| Cloudflare Pages | Unlimited bandwidth | ✅ |
| pytrends | Unlimited | ~30 req ✅ |

## ⚙️ Customise

Change articles per day → `config/settings.py` → `MAX_PAGES_PER_RUN`
Change schedule → `.github/workflows/generate.yml` → cron line
