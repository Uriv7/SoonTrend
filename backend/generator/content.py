"""
AI content generator with 4-level fallback chain:
  1. Gemini 1.5 Flash 8B  (free tier, 1000 req/day)
  2. Gemini 1.5 Flash     (free tier, 1500 req/day)
  3. Groq llama3-8b-8192  (free, active model)
  4. Groq mixtral-8x7b    (free, active model)
NO country/geography in any generated content.
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

ABSOLUTE RULES — never break these:
1. ZERO geographic references. No country, city, region, or location anywhere in the article.
2. ZERO phrases like "trending in X", "popular in X", "across X countries".
3. Write as a timeless authoritative reference article about the topic itself.
4. Use "{topic}" and close variants naturally 8-12 times across the full article.
5. Total word count: minimum 1000 words across all sections combined.
6. Write for real humans first. Be genuinely interesting, specific, and insightful.

Return ONLY a valid raw JSON object. No markdown, no backticks, no preamble, no explanation.

{{
  "title": "SEO title 52-60 chars — keyword near front",
  "meta_description": "148-155 chars — includes keyword — ends with compelling hook",
  "slug": "lowercase-hyphens-only-max-55-chars",
  "h1": "Engaging headline, conversational, can differ from title",
  "category": "ONE of: Technology | Science | Health | Business | Sports | Entertainment | Politics | Culture | Environment | Education | Lifestyle",
  "read_time": 6,
  "intro": "3-4 sentences. Hook the reader. State what they will learn. Use keyword naturally.",
  "sections": [
    {{
      "h2": "Section heading with secondary keyword",
      "content": "Minimum 5 paragraphs of rich, specific, well-explained content. Separate paragraphs with \\n."
    }}
  ],
  "faq": [
    {{"question": "Natural question someone Googles about {topic}?", "answer": "Specific 3-4 sentence answer."}}
  ],
  "key_takeaways": [
    "Concrete one-sentence insight.",
    "Concrete one-sentence insight.",
    "Concrete one-sentence insight.",
    "Concrete one-sentence insight."
  ],
  "related_queries": ["related term 1", "related term 2", "related term 3", "related term 4", "related term 5"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
  "schema_keywords": ["primary keyword", "semantic variant", "long-tail phrase", "related concept"]
}}

Requirements: minimum 5 sections, minimum 6 FAQ items, minimum 250 words per section content.
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
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    m    = genai.GenerativeModel(model)
    resp = m.generate_content(PROMPT.format(topic=topic))
    data = _parse(resp.text)
    _bump()
    return data


def _call_groq(topic: str, model: str) -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp   = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert SEO journalist. Respond with raw valid JSON only. No markdown, no backticks, no preamble."},
            {"role": "user",   "content": PROMPT.format(topic=topic)},
        ],
        temperature=0.72,
        max_tokens=4096,
    )
    return _parse(resp.choices[0].message.content)


def generate_article(topic: str) -> dict:
    """
    4-level fallback chain. Tries each provider in order.
    Raises RuntimeError only if ALL 4 fail.
    """
    attempts = []

    # ── Level 1: Gemini 1.5 Flash 8B (free, 1000/day) ────────────────────
    if _gemini_ok():
        try:
            u = _load_usage()
            print(f"    🤖 Gemini ({GEMINI_MODEL}) [{u['count']}/{GEMINI_DAILY_LIMIT} today]")
            d = _call_gemini(topic, GEMINI_MODEL)
            d["ai_provider"] = f"Gemini {GEMINI_MODEL}"
            return d
        except Exception as e:
            attempts.append(f"Gemini {GEMINI_MODEL}: {e}")
            print(f"    ⚠️  {GEMINI_MODEL} failed: {e}")
            time.sleep(2)

        # ── Level 2: Gemini 1.5 Flash (free, 1500/day) ───────────────────
        try:
            print(f"    🤖 Gemini fallback ({GEMINI_MODEL_FALLBACK})")
            d = _call_gemini(topic, GEMINI_MODEL_FALLBACK)
            d["ai_provider"] = f"Gemini {GEMINI_MODEL_FALLBACK}"
            return d
        except Exception as e:
            attempts.append(f"Gemini {GEMINI_MODEL_FALLBACK}: {e}")
            print(f"    ⚠️  {GEMINI_MODEL_FALLBACK} failed: {e}")
            time.sleep(2)
    else:
        print(f"    📊 Gemini quota reached → Groq")

    # ── Level 3: Groq llama3-8b-8192 (free, active) ──────────────────────
    if GROQ_API_KEY:
        try:
            print(f"    🤖 Groq ({GROQ_MODEL})")
            d = _call_groq(topic, GROQ_MODEL)
            d["ai_provider"] = f"Groq/{GROQ_MODEL}"
            return d
        except Exception as e:
            attempts.append(f"Groq {GROQ_MODEL}: {e}")
            print(f"    ⚠️  Groq {GROQ_MODEL} failed: {e}")
            time.sleep(2)

        # ── Level 4: Groq mixtral (free, active) ─────────────────────────
        try:
            print(f"    🤖 Groq fallback ({GROQ_MODEL_FALLBACK})")
            d = _call_groq(topic, GROQ_MODEL_FALLBACK)
            d["ai_provider"] = f"Groq/{GROQ_MODEL_FALLBACK}"
            return d
        except Exception as e:
            attempts.append(f"Groq {GROQ_MODEL_FALLBACK}: {e}")
            print(f"    ⚠️  Groq {GROQ_MODEL_FALLBACK} failed: {e}")

    raise RuntimeError("All 4 AI providers failed:\n" + "\n".join(attempts))
