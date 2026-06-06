"""SoonTrend V2 — Publisher"""
import json, os, subprocess, sys
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','..'))
from config.settings import PUBLISHED_FILE

def load_published() -> list:
    os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)
    if not os.path.exists(PUBLISHED_FILE):
        return []
    with open(PUBLISHED_FILE) as f:
        return json.load(f)

def mark_published(article: dict):
    data = load_published()
    data.append({
        "topic":        article.get("h1", article.get("title","")),
        "slug":         article["slug"],
        "title":        article["title"],
        "category":     article.get("category","General"),
        "content_type": article.get("content_type","article"),
        "tags":         article.get("tags",[]),
        "date":         str(date.today()),
        "ai_provider":  article.get("ai_provider","unknown"),
        "read_time":    article.get("read_time",6),
        "excerpt":      article.get("excerpt",""),
    })
    with open(PUBLISHED_FILE,"w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def git_commit_and_push(topics: list):
    if not topics:
        print("  ⏭️  Nothing to commit."); return
    try:
        subprocess.run(["git","config","user.email","bot@soontrend.com"], check=True)
        subprocess.run(["git","config","user.name","SoonTrend Bot"],       check=True)
        subprocess.run(["git","add","."],                                   check=True)
        n   = len(topics)
        msg = (f"🤖 {n} articles [{date.today()}]: "
               f"{', '.join(t.split('] ',1)[-1] for t in topics[:2])}"
               + (f" (+{n-2} more)" if n > 2 else ""))
        subprocess.run(["git","commit","-m",msg], check=True)
        subprocess.run(["git","push"],             check=True)
        print(f"  🚀 Pushed {n} pages → Cloudflare")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git: {e}"); raise
