"""
AI content generator — 4-level fallback chain.
Uses Gemini v1 API (not v1beta) to avoid model-not-found errors.
Groq uses current active models (June 2026).
"""
import json, os, re, sys, time
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import (
    GEMINI_API_KEY, GROQ_API_KEY,
    GEMINI_MODEL, GEMINI_MODEL_FALLBACK,
    GROQ_MODEL, GROQ_MODEL_FALLBACK,
    GEMINI_DAILY_LIMIT, GEMINI_USAGE_FILE,
)


def _load_usage() -> dict:
    os.makedirs(os.path.dirname(GEMINI_USAGE_FILE), exist_ok=True)
    if not os.path.exists(GEMINI_USAGE_FILE):
        return {"date": str(date.today()), "count": 0}
    with open(GEMINI_USAGE_FILE) as f:
        d = json.load(f)
    if d.get("date") != str(date.today()):
        d = {"date": str(date.today()), "count": 0}
    return d

def _save_usage(d):
    with open(GEMINI_USAGE_FILE, "w") as f:
        json.dump(d, f)

def _bump():
    d = _load_usage(); d["count"] += 1; _save_usage(d)

def _gemini_ok():
    return bool(GEMINI_API_KEY) and _load_usage()["count"] < GEMINI_DAILY_LIMIT


PROMPT = '''You are a world-class SEO journalist writing for a major editorial website.

Write a comprehensive, deeply informative, SEO-optimised article about: "{topic}"

ABSOLUTE RULES:
1. ZERO geographic references. No country, city, region anywhere.
2. Write as a timeless authoritative reference article about the topic itself.
3. Use "{topic}" naturally 8-12 times across the full article.
4. Total word count: minimum 1000 words across all sections.

Return ONLY a valid raw JSON object. No markdown, no backticks, no explanation.

{{
  "title": "SEO title 52-60 chars with keyword near front",
  "meta_description": "148-155 chars with keyword and compelling hook",
  "slug": "lowercase-hyphens-only-max-55-chars",
  "h1": "Engaging conversational headline",
  "category": "ONE of: Technology | Science | Health | Business | Sports | Entertainment | Politics | Culture | Environment | Education | Lifestyle",
  "read_time": 6,
  "intro": "3-4 sentences hooking the reader with keyword used naturally",
  "sections": [
    {{
      "h2": "Section heading with secondary keyword",
      "content": "Minimum 5 paragraphs separated by \\n. Rich specific content."
    }}
  ],
  "faq": [
    {{"question": "Natural Google question about {topic}?", "answer": "Specific 3-4 sentence answer."}}
  ],
  "key_takeaways": [
    "Concrete one-sentence insight.",
    "Concrete one-sentence insight.",
    "Concrete one-sentence insight.",
    "Concrete one-sentence insight."
  ],
  "related_queries": ["term 1", "term 2", "term 3", "term 4", "term 5"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
  "schema_keywords": ["primary keyword", "variant", "long-tail phrase", "related concept"]
}}

Minimum: 5 sections, 6 FAQ items, 250 words per section.
'''


def _parse(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```json\s*|^```\s*|\s*```$', '', text, flags=re.MULTILINE).strip()
    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
    return json.loads(text)


def _call_gemini(topic: str, model: str) -> dict:
    """Call Gemini using v1 API (not v1beta) via direct HTTP to avoid SDK version issues."""
    import urllib.request, urllib.error
    import json as jsonlib

    url  = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_API_KEY}"
    body = jsonlib.dumps({
        "contents": [{"parts": [{"text": PROMPT.format(topic=topic)}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }).encode()

    req  = urllib.request.Request(url, data=body,
                                   headers={"Content-Type": "application/json"},
                                   method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = jsonlib.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini HTTP {e.code}: {e.read().decode()[:300]}")

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    data = _parse(text)
    _bump()
    return data


def _call_groq(topic: str, model: str) -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp   = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert SEO journalist. Respond with raw valid JSON only. No markdown, no backticks."},
            {"role": "user",   "content": PROMPT.format(topic=topic)},
        ],
        temperature=0.72,
        max_tokens=4096,
    )
    return _parse(resp.choices[0].message.content)


def generate_article(topic: str) -> dict:
    """4-level fallback: Gemini flash-latest → Gemini flash-8b → Groq llama3.1 → Groq llama3.3"""
    attempts = []

    # ── Level 1 & 2: Gemini (v1 API direct HTTP, bypasses SDK version issues) ──
    if _gemini_ok():
        for model in [GEMINI_MODEL, GEMINI_MODEL_FALLBACK]:
            try:
                u = _load_usage()
                print(f"    🤖 Gemini ({model}) [{u['count']}/{GEMINI_DAILY_LIMIT} today]")
                d = _call_gemini(topic, model)
                d["ai_provider"] = f"Gemini/{model}"
                return d
            except Exception as e:
                attempts.append(f"Gemini {model}: {e}")
                print(f"    ⚠️  {model} failed: {str(e)[:120]}")
                time.sleep(2)
    else:
        print("    📊 Gemini quota reached → Groq")

    # ── Level 3 & 4: Groq (current active free models) ───────────────────────
    if GROQ_API_KEY:
        for model in [GROQ_MODEL, GROQ_MODEL_FALLBACK]:
            try:
                print(f"    🤖 Groq ({model})")
                d = _call_groq(topic, model)
                d["ai_provider"] = f"Groq/{model}"
                return d
            except Exception as e:
                attempts.append(f"Groq {model}: {e}")
                print(f"    ⚠️  {model} failed: {str(e)[:120]}")
                time.sleep(2)

    raise RuntimeError("All 4 AI providers failed:\n" + "\n".join(attempts))
