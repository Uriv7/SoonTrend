"""
SoonTrend V2 — Maximum SEO Content Generator
4-level AI fallback: Gemini flash → Gemini flash-8b → Groq llama3.1 → Groq llama3.3

Generates 2 content types per run:
  Article     — deep evergreen SEO (ranks for months, targets long-tail)
  NewsArticle — breaking news style (Google News eligible, fast index)

Both are optimised for:
  - Semantic SEO (LSI keywords, topic clusters)
  - Featured snippet eligibility
  - People Also Ask eligibility
  - Google News inclusion (for NewsArticles)
  - E-E-A-T signals
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

# ── Usage tracker ──────────────────────────────────────────────────────────────
def _load_usage():
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


# ── SEO Article Prompt (evergreen, long-tail keyword targeting) ───────────────
SEO_PROMPT = '''You are a senior SEO journalist and content strategist.
Write a maximum-SEO, deeply informative evergreen article about: "{topic}"

TARGET: English-speaking audience in US, UK, Australia, Canada.
GOAL: Rank #1 on Google for "{topic}" and 20+ related long-tail keywords.

STRICT RULES:
1. Zero geographic references. No country, city, or region anywhere.
2. Use "{topic}" exactly 10-14 times naturally throughout the article.
3. Use 8-12 semantic/LSI keyword variants (related terms Google associates with this topic).
4. Minimum 1200 words across all sections.
5. Write the intro so it could win a Google Featured Snippet (direct answer in first 50 words).
6. Each H2 must be a question or keyword phrase people actually search for.
7. Pure flowing prose — no bullet lists, no numbered lists inside section content.
8. Include specific statistics, named studies, expert quotes where possible.
9. Make it genuinely the best article on the internet about this topic.

Return ONLY raw JSON. No markdown, no backticks, no explanation.

{{
  "title": "Primary keyword + benefit — exactly 55-60 chars",
  "meta_description": "Primary keyword in first 10 words. Benefit. Call to action. Exactly 150-155 chars.",
  "slug": "primary-keyword-slug-max-55-chars",
  "h1": "Slightly different from title — more conversational — includes keyword",
  "category": "ONE of: Technology|Science|Health|Business|Finance|Sports|Entertainment|Politics|Culture|Environment|Education|Lifestyle|Law",
  "content_type": "article",
  "read_time": 7,
  "lsi_keywords": ["semantic variant 1","semantic variant 2","semantic variant 3","semantic variant 4","semantic variant 5","semantic variant 6"],
  "intro": "FEATURED SNIPPET BAIT: Start with a direct 1-sentence definition or answer. Then 3 sentences of context. Must include keyword in first sentence.",
  "sections": [
    {{
      "h2": "What Is [topic]? (Definition and Overview)",
      "content": "7+ paragraphs separated by \\n. Open with a clear definition. Build depth. Include statistics."
    }},
    {{
      "h2": "How Does [topic] Work?",
      "content": "6+ paragraphs. Mechanistic explanation. Build to complexity."
    }},
    {{
      "h2": "The Key Benefits of [topic]",
      "content": "6+ paragraphs. Evidence-based. Specific examples."
    }},
    {{
      "h2": "Common Misconceptions About [topic]",
      "content": "5+ paragraphs. Myth-busting. Authoritative."
    }},
    {{
      "h2": "Recent Developments in [topic]",
      "content": "5+ paragraphs. Latest research, breakthroughs, or changes."
    }},
    {{
      "h2": "What the Future Holds for [topic]",
      "content": "5+ paragraphs. Forward-looking. Expert perspective."
    }}
  ],
  "faq": [
    {{"question": "What is [topic]?", "answer": "Direct 2-sentence definition."}},
    {{"question": "How does [topic] work?", "answer": "3-sentence explanation."}},
    {{"question": "Is [topic] safe?", "answer": "3-sentence factual answer."}},
    {{"question": "What are the benefits of [topic]?", "answer": "3-sentence answer."}},
    {{"question": "How long does [topic] take?", "answer": "2-sentence answer."}},
    {{"question": "Who should know about [topic]?", "answer": "3-sentence answer."}},
    {{"question": "What are the risks of [topic]?", "answer": "3-sentence balanced answer."}}
  ],
  "key_takeaways": [
    "Most important fact — one sentence with specific detail.",
    "Second key insight — one sentence.",
    "Third key point — one sentence.",
    "Fourth insight — one sentence.",
    "Fifth actionable insight — one sentence."
  ],
  "related_queries": ["long-tail query 1","long-tail query 2","long-tail query 3","long-tail query 4","long-tail query 5","long-tail query 6","long-tail query 7","long-tail query 8"],
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "schema_keywords": ["primary keyword","semantic variant 1","semantic variant 2","long-tail phrase 1","long-tail phrase 2"],
  "excerpt": "2-sentence compelling summary. Include keyword. Written to be shared on social media."
}}'''


# ── NewsArticle Prompt (breaking, Google News eligible) ───────────────────────
NEWS_PROMPT = '''You are a breaking news editor at a major English-language publication.
Write an urgent, well-structured news article about: "{topic}"

TARGET: English-speaking audience globally. Eligible for Google News.
GOAL: Get indexed in Google News within 1 hour of publishing. Go viral on social.

STRICT RULES:
1. Zero geographic references. No country, city, or region anywhere.
2. Write in inverted pyramid — most critical fact in the very first sentence.
3. Use "{topic}" naturally 8-10 times.
4. Minimum 900 words.
5. Make it personally relevant — "what this means for you" angle is mandatory.
6. Headline must create urgency or curiosity without being clickbait.
7. Include a "what to watch for next" section — forward-looking hook for return visits.
8. Make it shareable — people should want to send this to someone they know.

Return ONLY raw JSON. No markdown, no backticks, no explanation.

{{
  "title": "Urgent/newsworthy title — 52-60 chars — creates curiosity",
  "meta_description": "What happened + why it matters to the reader — 150-155 chars.",
  "slug": "news-slug-lowercase-hyphens-max-55-chars",
  "h1": "Punchy news headline — makes people want to read immediately",
  "category": "ONE of: Technology|Science|Health|Business|Finance|Sports|Entertainment|Politics|Culture|Environment|Education|Lifestyle|Law",
  "content_type": "news",
  "read_time": 5,
  "lsi_keywords": ["related news term 1","related news term 2","related news term 3","related news term 4"],
  "intro": "Lead sentence: the single most important fact. Then 3 sentences of immediate context. Must grab attention in first 10 words.",
  "sections": [
    {{
      "h2": "What Is Happening Right Now",
      "content": "5+ paragraphs. Core story, verified facts, timeline, scope."
    }},
    {{
      "h2": "Why This Matters",
      "content": "4+ paragraphs. Significance, impact, stakes involved."
    }},
    {{
      "h2": "What Experts and Analysts Are Saying",
      "content": "4+ paragraphs. Multiple expert perspectives, analysis."
    }},
    {{
      "h2": "What This Means For You",
      "content": "4+ paragraphs. Direct personal relevance. Practical implications. Actionable insight."
    }},
    {{
      "h2": "What Happens Next",
      "content": "3+ paragraphs. Forward-looking. Key dates or milestones to watch. Creates reason to return."
    }}
  ],
  "faq": [
    {{"question": "What exactly is happening with {topic}?", "answer": "3-sentence direct answer."}},
    {{"question": "When did this start?", "answer": "2-sentence timeline answer."}},
    {{"question": "Who is affected by {topic}?", "answer": "3-sentence answer."}},
    {{"question": "What should I do about {topic}?", "answer": "3-sentence practical answer."}},
    {{"question": "How serious is {topic}?", "answer": "3-sentence measured answer."}},
    {{"question": "What happens next with {topic}?", "answer": "3-sentence forward-looking answer."}}
  ],
  "key_takeaways": [
    "The single most important fact — one sentence.",
    "Why this matters — one sentence.",
    "Who is affected — one sentence.",
    "What action to consider — one sentence.",
    "What to watch next — one sentence."
  ],
  "related_queries": ["news query 1","news query 2","news query 3","news query 4","news query 5","news query 6"],
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7"],
  "schema_keywords": ["primary news term","news variant 1","news variant 2","long-tail news phrase"],
  "excerpt": "2-sentence punchy news summary. Written to be retweeted. Must create urgency."
}}'''


def _parse(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```json\s*|^```\s*|\s*```$', '', text, flags=re.MULTILINE).strip()
    start = text.find('{'); end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
    return json.loads(text)


def _call_gemini(prompt: str, model: str) -> dict:
    import urllib.request, urllib.error
    url  = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_API_KEY}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":     0.7,
            "maxOutputTokens": 4096,
            "topP":            0.95,
            "topK":            40,
        }
    }).encode()
    request = urllib.request.Request(url, data=body,
                headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini HTTP {e.code}: {e.read().decode()[:300]}")
    data = _parse(result["candidates"][0]["content"]["parts"][0]["text"])
    _bump()
    return data


def _call_groq(prompt: str, model: str) -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp   = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional SEO journalist and editor. Return raw valid JSON only. Absolutely no markdown, no backticks, no preamble, no explanation."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.72,
        max_tokens=4096,
    )
    return _parse(resp.choices[0].message.content)


def _generate(topic: str, prompt_template: str, label: str) -> dict:
    prompt   = prompt_template.format(topic=topic)
    attempts = []

    if _gemini_ok():
        for model in [GEMINI_MODEL, GEMINI_MODEL_FALLBACK]:
            try:
                u = _load_usage()
                print(f"    🤖 Gemini ({model}) [{u['count']}/{GEMINI_DAILY_LIMIT}]")
                d = _call_gemini(prompt, model)
                d["ai_provider"] = f"Gemini/{model}"
                return d
            except Exception as e:
                attempts.append(f"Gemini {model}: {str(e)[:100]}")
                print(f"    ⚠️  {model}: {str(e)[:100]}")
                time.sleep(2)
    else:
        print("    📊 Gemini quota → Groq")

    if GROQ_API_KEY:
        for model in [GROQ_MODEL, GROQ_MODEL_FALLBACK]:
            try:
                print(f"    🤖 Groq ({model})")
                d = _call_groq(prompt, model)
                d["ai_provider"] = f"Groq/{model}"
                return d
            except Exception as e:
                attempts.append(f"Groq {model}: {str(e)[:100]}")
                print(f"    ⚠️  {model}: {str(e)[:100]}")
                time.sleep(2)

    raise RuntimeError(f"All 4 providers failed for {label}:\n" + "\n".join(attempts))


def generate_article(topic: str) -> dict:
    """Deep evergreen SEO article — targets long-tail keywords, featured snippets."""
    return _generate(topic, SEO_PROMPT, "Article")


def generate_news_article(topic: str) -> dict:
    """Breaking news article — Google News eligible, viral social sharing."""
    return _generate(topic, NEWS_PROMPT, "NewsArticle")
