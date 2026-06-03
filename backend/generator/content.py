"""
backend/generator/content.py
AI content generator — Gemini 1.5 Flash (primary) → Groq llama3-70b (fallback).
NO country/geography appears anywhere in generated content.
"""
import json, os, re, sys, time
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import (
    GEMINI_API_KEY, GROQ_API_KEY, GEMINI_MODEL, GROQ_MODEL,
    GEMINI_DAILY_LIMIT, GEMINI_USAGE_FILE,
)


# ── Usage tracker ─────────────────────────────────────────────────────────────
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


# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT = '''You are a world-class SEO journalist and content strategist writing for a major editorial website.

Write a comprehensive, deeply informative, SEO-optimised article about: "{topic}"

ABSOLUTE RULES — never break these:
1. ZERO geographic references. No country, city, region, continent, or location anywhere.
2. ZERO phrases like "trending in X", "popular in X", "across X".
3. Write as a timeless, authoritative reference article about the topic itself.
4. Use "{topic}" and close variants naturally 8-12 times across the full article.
5. Total word count: 1000-1300 words minimum across all sections combined.
6. Write for real humans first. Be genuinely interesting, specific, and insightful.

Return ONLY a valid raw JSON object. Absolutely no markdown, no backticks, no preamble.

{{
  "title": "SEO title 52-60 chars — keyword near front",
  "meta_description": "148-155 chars — includes keyword — ends with a compelling hook or question",
  "slug": "lowercase-hyphens-only-max-55-chars",
  "h1": "Engaging headline, can differ from title, more conversational",
  "category": "ONE of: Technology | Science | Health | Business | Sports | Entertainment | Politics | Culture | Environment | Education | Lifestyle",
  "read_time": 6,
  "intro": "3-4 sentences. Immediately hook the reader. State what they will learn. Use the keyword naturally.",
  "sections": [
    {{
      "h2": "Keyword-rich section heading with secondary keyword",
      "content": "Minimum 5 paragraphs of rich, specific, well-explained content. Use \\n between paragraphs. No fluff. Real insight."
    }}
  ],
  "faq": [
    {{"question": "Natural question someone would Google about {topic}?", "answer": "Specific 3-4 sentence answer with real detail."}}
  ],
  "key_takeaways": [
    "One-sentence takeaway with a concrete insight.",
    "One-sentence takeaway with a concrete insight.",
    "One-sentence takeaway with a concrete insight.",
    "One-sentence takeaway with a concrete insight."
  ],
  "related_queries": ["related search term 1", "related search term 2", "related search term 3", "related search term 4", "related search term 5"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
  "schema_keywords": ["primary keyword", "semantic variant", "long-tail phrase", "related concept"]
}}

Requirements:
- sections: minimum 5 (each with h2 + content)
- faq: minimum 6 items
- Every section content: minimum 200 words
- key_takeaways: exactly 4 items
- slug: no special chars, no numbers unless part of topic name
'''


def _parse(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```json\s*|^```\s*|\s*```$', '', text, flags=re.MULTILINE).strip()
    # Find first { and last } to be safe
    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
    return json.loads(text)


def _gemini(topic: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    resp  = model.generate_content(PROMPT.format(topic=topic))
    data  = _parse(resp.text)
    _bump()
    return data


def _groq(topic: str) -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp   = client.chat.completions.create(
        model=GROQ_MODEL,
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
    Generate full SEO article for topic.
    Tries Gemini first; auto-falls back to Groq when quota is hit.
    Raises RuntimeError if both fail.
    """
    errors = []

    if _gemini_ok():
        try:
            u = _load_usage()
            print(f"    🤖 Gemini Flash ({u['count']}/{GEMINI_DAILY_LIMIT} used today)")
            d = _gemini(topic)
            d["ai_provider"] = "Gemini 1.5 Flash"
            return d
        except Exception as e:
            errors.append(f"Gemini: {e}")
            print(f"    ⚠️  Gemini failed: {e}")
            time.sleep(2)
    else:
        print(f"    📊 Gemini quota reached → Groq fallback")

    if GROQ_API_KEY:
        try:
            print(f"    🤖 Groq ({GROQ_MODEL})")
            d = _groq(topic)
            d["ai_provider"] = f"Groq/{GROQ_MODEL}"
            return d
        except Exception as e:
            errors.append(f"Groq: {e}")
            print(f"    ⚠️  Groq failed: {e}")

    raise RuntimeError("Both AI providers failed:\n" + "\n".join(errors))
