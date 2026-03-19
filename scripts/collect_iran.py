#!/usr/bin/env python3
# collect_iran.py — Recolección de noticias Iran OSINT Monitor
# Fuentes: RSS directos + GDELT
# Cron: cada 30 min

import os, sys, yaml, feedparser, json, hashlib
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
CONFIG   = os.path.join(BASE_DIR, "config", "sources_iran.yaml")
os.makedirs(DATA_DIR, exist_ok=True)

def load_config():
    with open(CONFIG, "r") as f:
        return yaml.safe_load(f)

def article_id(title, source):
    return hashlib.md5(f"{title}{source}".encode()).hexdigest()[:12]

def fetch_rss(sources_dict):
    articles = []
    for bando, sources in sources_dict.items():
        if bando == "keywords_iran":
            continue
        for src in sources:
            try:
                feed = feedparser.parse(src["url"])
                for entry in feed.entries[:20]:
                    articles.append({
                        "id":      article_id(entry.get("title",""), src["name"]),
                        "title":   entry.get("title", ""),
                        "summary": entry.get("summary", "")[:300],
                        "source":  src["name"],
                        "bias":    src["bias"],
                        "bando":   bando,
                        "lang":    src["lang"],
                        "url":     entry.get("link", ""),
                        "published": entry.get("published", str(datetime.now())),
                        "fetched_at": str(datetime.now()),
                    })
                print(f"  ✅ {src['name']}: {len(feed.entries)} artículos")
            except Exception as e:
                print(f"  ❌ {src['name']}: {e}")
    return articles

def fetch_gdelt(keywords, max_records=250):
    """Fetch via GDELT GKG API — no key needed"""
    try:
        from gdeltdoc import GdeltDoc, Filters
        gd = GdeltDoc()
        kw_str = " OR ".join(keywords[:5])
        f = Filters(
            keyword=kw_str,
            start_date=(datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
        )
        articles = gd.article_search(f)
        if articles is not None and len(articles) > 0:
            articles["bando"]   = "gdelt"
            articles["bias"]    = "mixed"
            articles["fetched_at"] = str(datetime.now())
            print(f"  ✅ GDELT: {len(articles)} artículos")
            return articles.to_dict("records")
    except Exception as e:
        print(f"  ⚠️  GDELT: {e}")
    return []

def save_articles(articles):
    out = os.path.join(DATA_DIR, "iran_news.csv")
    df_new = pd.DataFrame(articles).drop_duplicates(subset=["id"])
    if os.path.exists(out):
        df_old = pd.read_csv(out)
        df = pd.concat([df_old, df_new]).drop_duplicates(subset=["id"])
        # Rotación — mantener solo últimos 30 días
        if "fetched_at" in df.columns:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"], errors="coerce")
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
            df = df[df["fetched_at"] >= cutoff]
        # Mantener solo últimas 72h
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], errors="coerce")
        cutoff = datetime.now() - timedelta(hours=72)
        df = df[df["fetched_at"] > cutoff]
    else:
        df = df_new
    df.to_csv(out, index=False)
    print(f"📦 Total artículos en BD: {len(df)}")
    return df

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"collect_iran.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    cfg = load_config()
    print("\n📡 RSS directos:")
    rss_articles = fetch_rss(cfg)
    print("\n🌐 GDELT:")
    gdelt_articles = fetch_gdelt(cfg["keywords_iran"]["core"])
    all_articles = rss_articles + gdelt_articles
    print(f"\n📥 Total recolectados: {len(all_articles)}")
    df = save_articles(all_articles)
    # Metadata
    meta = {"last_collect": str(datetime.now()), "total_articles": len(df)}
    json.dump(meta, open(os.path.join(DATA_DIR, "iran_meta.json"), "w"))
    print("\n✅ collect_iran.py completado")
