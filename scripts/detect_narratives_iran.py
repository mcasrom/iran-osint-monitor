#!/usr/bin/env python3
# detect_narratives_iran.py — Detección de narrativas por bando
# TF-IDF clustering sobre títulos + resúmenes

import os, json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

STOPWORDS_EN = [
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","has","have","had","be","been","being",
    "that","this","it","he","she","they","we","i","you","said","says",
    "iran","iranian","israel","us","united","states","new","also","after",
]

BANDOS = {
    "pro_occidente": ["reuters","bbc","times of israel","france24","ap news"],
    "pro_iran_eje":  ["press tv","al mayadeen","tass","xinhua"],
    "neutros_regionales": ["al jazeera","middle east eye","arab news"],
    "gdelt": ["gdelt"],
}

def classify_bando(source):
    s = source.lower()
    for bando, sources in BANDOS.items():
        if any(x in s for x in sources):
            return bando
    return "desconocido"

def detect_narratives(df, n_clusters=8):
    df = df.dropna(subset=["title"])
    df["text"] = df["title"].fillna("") + " " + df["summary"].fillna("")
    df["text"] = df["text"].str.lower().str.replace(r'[^a-z\s]', ' ', regex=True)

    if len(df) < 10:
        print("  ⚠️  Insuficientes artículos para clustering")
        return pd.DataFrame(), pd.DataFrame()

    tfidf = TfidfVectorizer(
        max_features=300,
        stop_words=STOPWORDS_EN,
        ngram_range=(1, 2),
        min_df=2,
    )
    X = tfidf.fit_transform(df["text"])
    n = min(n_clusters, len(df) // 3)
    km = KMeans(n_clusters=n, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X)

    # Top keywords por cluster
    feature_names = tfidf.get_feature_names_out()
    clusters_info = []
    for c in range(n):
        center = km.cluster_centers_[c]
        top_idx = center.argsort()[-6:][::-1]
        top_kw = " · ".join(feature_names[top_idx])
        count = int((df["cluster"] == c).sum())
        # Distribución por bando
        bando_dist = df[df["cluster"] == c]["bando"].value_counts().to_dict()
        clusters_info.append({
            "cluster": c,
            "label": top_kw,
            "count": count,
            "pro_occidente": bando_dist.get("pro_occidente", 0),
            "pro_iran_eje":  bando_dist.get("pro_iran_eje", 0),
            "neutros":       bando_dist.get("neutros_regionales", 0),
            "gdelt":         bando_dist.get("gdelt", 0),
        })

    df_clusters = pd.DataFrame(clusters_info).sort_values("count", ascending=False)

    # Keywords emergentes globales
    sums = np.asarray(X.sum(axis=0)).flatten()
    top_global = sorted(zip(feature_names, sums), key=lambda x: -x[1])[:30]
    df_keywords = pd.DataFrame(top_global, columns=["keyword", "score"])

    return df_clusters, df_keywords, df

def divergencia_narrativa(df):
    """Mide qué tan distinta es la cobertura entre bandos para cada cluster"""
    results = []
    for c in df["cluster"].unique():
        sub = df[df["cluster"] == c]
        total = len(sub)
        if total == 0:
            continue
        occ = len(sub[sub["bando"] == "pro_occidente"])
        iran = len(sub[sub["bando"] == "pro_iran_eje"])
        div = abs(occ - iran) / total if total > 0 else 0
        results.append({"cluster": c, "divergencia": round(div, 3), "total": total})
    return pd.DataFrame(results)

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"detect_narratives_iran.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    news_path = os.path.join(DATA_DIR, "iran_news.csv")
    if not os.path.exists(news_path):
        print("❌ iran_news.csv no encontrado — ejecuta collect_iran.py primero")
        exit(1)
    df = pd.read_csv(news_path)
    df["bando"] = df.apply(lambda r: r["bando"] if r["bando"] != "gdelt"
                           else classify_bando(r.get("source","")), axis=1)
    print(f"📰 Artículos: {len(df)} | Bandos: {df['bando'].value_counts().to_dict()}")
    df_clusters, df_keywords, df_with_clusters = detect_narratives(df)
    if not df_clusters.empty:
        df_clusters.to_csv(os.path.join(DATA_DIR, "iran_narratives.csv"), index=False)
        df_keywords.to_csv(os.path.join(DATA_DIR, "iran_keywords.csv"), index=False)
        df_div = divergencia_narrativa(df_with_clusters)
        df_div.to_csv(os.path.join(DATA_DIR, "iran_divergencia.csv"), index=False)
        print(f"✅ {len(df_clusters)} clusters detectados")
        print(f"✅ Top keyword: {df_keywords.iloc[0]['keyword']}")
    else:
        print("⚠️  Sin clusters generados")
