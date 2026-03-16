#!/usr/bin/env python3
# energy_tracker.py — Seguimiento energético: Brent, LNG, Ormuz
# Alpha Vantage (con key) + fallback Yahoo Finance (sin key)

import os, json, requests
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

def get_av_key():
    try:
        secrets = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
        for line in open(secrets):
            if "ALPHA_VANTAGE" in line:
                return line.split("=")[1].strip().strip('"')
    except:
        pass
    return os.environ.get("ALPHA_VANTAGE_KEY", "")

def fetch_brent_alphavantage(key):
    url = f"https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={key}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if "data" in data:
        df = pd.DataFrame(data["data"])
        df.columns = ["date","price"]
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["commodity"] = "Brent"
        return df.head(30)
    return pd.DataFrame()

def fetch_brent_fallback():
    """Fallback sin API key — Yahoo Finance via yfinance o precio estático"""
    try:
        import yfinance as yf
        brent = yf.download("BZ=F", period="30d", progress=False)
        if not brent.empty:
            df = brent[["Close"]].reset_index()
            df.columns = ["date","price"]
            df["commodity"] = "Brent"
            df["date"] = df["date"].astype(str)
            return df
    except:
        pass
    # Último precio conocido (hardcoded como fallback final)
    print("  ⚠️  Usando precio Brent estático (sin API)")
    return pd.DataFrame([{
        "date": str(datetime.now().date()),
        "price": 107.0,
        "commodity": "Brent (estático)"
    }])

def fetch_natural_gas(key):
    url = f"https://www.alphavantage.co/query?function=NATURAL_GAS&interval=daily&apikey={key}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "data" in data:
            df = pd.DataFrame(data["data"])
            df.columns = ["date","price"]
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            df["commodity"] = "Natural Gas"
            return df.head(30)
    except:
        pass
    return pd.DataFrame()

def ormuz_status():
    """Estado del Estrecho de Ormuz basado en noticias recientes"""
    news_path = os.path.join(DATA_DIR, "iran_news.csv")
    if not os.path.exists(news_path):
        return {"status": "desconocido", "alertas": 0, "nivel": "verde"}
    df = pd.read_csv(news_path)
    keywords = ["ormuz","strait","shipping","tanker","blockade","closure"]
    mask = df["title"].str.lower().apply(
        lambda t: any(k in str(t) for k in keywords)
    )
    alertas = int(mask.sum())
    nivel = "rojo" if alertas > 10 else "naranja" if alertas > 4 else "verde"
    titulares = df[mask]["title"].head(3).tolist()
    return {"status": "monitorizando", "alertas": alertas,
            "nivel": nivel, "titulares": titulares,
            "updated": str(datetime.now())}

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"energy_tracker.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    key = get_av_key()
    frames = []
    if key and key != "TU_KEY_AQUI":
        print("🔑 Alpha Vantage key encontrada")
        df_brent = fetch_brent_alphavantage(key)
        df_gas   = fetch_natural_gas(key)
        if not df_brent.empty: frames.append(df_brent)
        if not df_gas.empty:   frames.append(df_gas)
    else:
        print("⚠️  Sin Alpha Vantage key — usando fallback")
        df_brent = fetch_brent_fallback()
        if not df_brent.empty: frames.append(df_brent)

    if frames:
        df_energy = pd.concat(frames, ignore_index=True)
        df_energy.to_csv(os.path.join(DATA_DIR, "iran_energy.csv"), index=False)
        latest = df_energy[df_energy["commodity"]=="Brent"]["price"].iloc[0] if len(df_energy) else "N/A"
        print(f"✅ Brent último: {latest} USD/barril")
    else:
        print("❌ Sin datos energéticos")

    ormuz = ormuz_status()
    json.dump(ormuz, open(os.path.join(DATA_DIR, "iran_ormuz.json"), "w"), ensure_ascii=False)
    print(f"✅ Ormuz: nivel={ormuz['nivel']} | alertas={ormuz['alertas']}")
