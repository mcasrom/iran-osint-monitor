#!/usr/bin/env python3
# detect_sentiment_iran.py — Análisis de sentimiento por bando y fuente
# Léxico básico + Claude API para muestra representativa

import os, json
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# Léxico básico sin API (funciona sin keys)
LEXICO_POS = [
    "ceasefire","peace","agreement","deal","diplomatic","cooperation",
    "relief","stabilize","resolve","withdraw","negotiate","progress",
]
LEXICO_NEG = [
    "attack","strike","kill","death","missile","bomb","war","conflict",
    "threat","nuclear","sanction","retaliate","escalate","casualties",
    "explosion","destroyed","invasion","offensive","siege",
]
LEXICO_NEU = ["said","announced","statement","meeting","talks","report"]

def sentiment_lexico(text):
    t = str(text).lower()
    pos = sum(1 for w in LEXICO_POS if w in t)
    neg = sum(1 for w in LEXICO_NEG if w in t)
    if neg > pos: return "negativo", round(-neg / (pos + neg + 0.001), 3)
    if pos > neg: return "positivo", round(pos / (pos + neg + 0.001), 3)
    return "neutral", 0.0

def analizar_sentimiento(df):
    df = df.copy()
    df["text"] = df["title"].fillna("") + " " + df["summary"].fillna("")
    df[["sentiment","score"]] = df["text"].apply(
        lambda t: pd.Series(sentiment_lexico(t))
    )
    # Resumen global
    summary = df.groupby("sentiment")["score"].agg(["count","mean"]).reset_index()
    summary.columns = ["sentiment","count","avg_score"]

    # Por bando
    by_bando = df.groupby(["bando","sentiment"]).size().reset_index(name="count")

    # Por fuente
    by_source = df.groupby("source").agg(
        total=("score","count"),
        avg_score=("score","mean"),
        negativity_pct=("sentiment", lambda x: (x=="negativo").mean()*100),
        positivity_pct=("sentiment", lambda x: (x=="positivo").mean()*100),
    ).reset_index().sort_values("avg_score")

    return summary, by_bando, by_source

def claude_sentiment_sample(df, n=20):
    """Analiza muestra con Claude API si está disponible"""
    try:
        import anthropic, os
        key = os.environ.get("ANTHROPIC_API_KEY") or ""
        if not key:
            secrets = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
            if os.path.exists(secrets):
                for line in open(secrets):
                    if "ANTHROPIC" in line:
                        key = line.split("=")[1].strip().strip('"')
        if not key:
            print("  ⚠️  Sin ANTHROPIC_API_KEY — usando solo léxico")
            return pd.DataFrame()

        client = anthropic.Anthropic(api_key=key)
        sample = df.sample(min(n, len(df)))
        results = []
        for _, row in sample.iterrows():
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=60,
                messages=[{"role":"user","content":
                    f"Clasifica el sentimiento de este titular sobre el conflicto iraní. "
                    f"Responde SOLO: positivo, negativo o neutral. "
                    f"Titular: {row['title']}"
                }]
            )
            sent = resp.content[0].text.strip().lower()
            results.append({"title": row["title"], "source": row["source"],
                            "bando": row["bando"], "claude_sentiment": sent})
            print(f"  → {sent[:8]} | {row['title'][:60]}")
        return pd.DataFrame(results)
    except Exception as e:
        print(f"  ⚠️  Claude API: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"detect_sentiment_iran.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    news_path = os.path.join(DATA_DIR, "iran_news.csv")
    if not os.path.exists(news_path):
        print("❌ iran_news.csv no encontrado")
        exit(1)
    df = pd.read_csv(news_path)
    print(f"📰 Analizando {len(df)} artículos...")
    summary, by_bando, by_source = analizar_sentimiento(df)
    summary.to_csv(os.path.join(DATA_DIR, "iran_sentiment.csv"), index=False)
    by_bando.to_csv(os.path.join(DATA_DIR, "iran_sentiment_bando.csv"), index=False)
    by_source.to_csv(os.path.join(DATA_DIR, "iran_sentiment_source.csv"), index=False)
    print(f"✅ Sentimiento global:\n{summary.to_string(index=False)}")
    print("\n🤖 Muestra Claude API (10 titulares):")
    df_claude = claude_sentiment_sample(df, n=10)
    if not df_claude.empty:
        df_claude.to_csv(os.path.join(DATA_DIR, "iran_sentiment_claude.csv"), index=False)
        print(f"✅ {len(df_claude)} titulares analizados con Claude")
