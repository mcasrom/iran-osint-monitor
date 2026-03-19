#!/usr/bin/env python3
# dashboard.py — Iran OSINT Monitor
# Sprint 1: Radar Narrativo · Mapa de Alianzas · Energía y Mercados
# Autor: M. Castillo · mybloggingnotes@gmail.com

import os, json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

st.set_page_config(
    page_title="Iran OSINT Monitor",
    page_icon="🛰️",
    layout="wide"
)

# ── Cabecera ─────────────────────────────────────────────────────────────────
st.title("🛰️ Iran OSINT Monitor")
st.markdown("""
> Monitor en tiempo real del conflicto iraní — narrativas, alianzas, energía y desinformación  
> desde **todos los ángulos**, **todos los países**, **todas las esferas geopolíticas**
""")

# ── Metadata pipeline ─────────────────────────────────────────────────────────
meta_path = os.path.join(DATA_DIR, "iran_meta.json")
if os.path.exists(meta_path):
    meta = json.load(open(meta_path))
    last = meta.get("last_collect", "pendiente")
    total = meta.get("total_articles", 0)
    st.caption(f"🕐 Última recolección: {last} · 📰 Artículos en BD: {total} · Pipeline: cada 30 min")
else:
    st.warning("⚠️ Pipeline aún no ejecutado — corre `python3 scripts/run_all_iran.py` en el Odroid")

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡 Radar Narrativo",
    "🗺️ Mapa de Alianzas",
    "⚡ Energía & Ormuz",
    "📰 Últimas Noticias",
    "ℹ️ Guía & Créditos",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RADAR NARRATIVO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("📡 Radar Narrativo por Bando")
    st.markdown("""
    Clusters temáticos detectados mediante TF-IDF.  
    **Verde** = narrativa dominada por occidente · **Rojo** = narrativa dominada por eje iraní · **Gris** = equilibrada
    """)

    nar_path = os.path.join(DATA_DIR, "iran_narratives.csv")
    kw_path  = os.path.join(DATA_DIR, "iran_keywords.csv")
    sent_path = os.path.join(DATA_DIR, "iran_sentiment_bando.csv")

    if os.path.exists(nar_path):
        df_nar = pd.read_csv(nar_path)

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Clusters detectados", len(df_nar))
        col2.metric("Narrativa dominante", df_nar.iloc[0]["label"][:35] if len(df_nar) else "—")
        occ_dom = int(df_nar["pro_occidente"].sum())
        iran_dom = int(df_nar["pro_iran_eje"].sum())
        col3.metric("Artículos pro-Occidente", occ_dom)
        col4.metric("Artículos pro-Irán", iran_dom)

        st.markdown("---")
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Clusters por volumen")
            fig = px.bar(
                df_nar.head(10), x="count", y="label",
                orientation="h", color="count",
                color_continuous_scale="Reds",
                title="Top 10 narrativas por volumen",
                labels={"count": "Artículos", "label": "Narrativa"}
            )
            fig.update_layout(height=420)
            st.plotly_chart(fig, width="stretch")

        with col_b:
            st.subheader("Cobertura por bando por cluster")
            df_melt = df_nar.head(8).melt(
                id_vars=["label"],
                value_vars=["pro_occidente","pro_iran_eje","neutros","gdelt"],
                var_name="bando", value_name="articulos"
            )
            fig2 = px.bar(
                df_melt, x="articulos", y="label",
                color="bando", orientation="h", barmode="stack",
                title="Distribución por bando",
                color_discrete_map={
                    "pro_occidente": "#1f77b4",
                    "pro_iran_eje":  "#d62728",
                    "neutros":       "#9467bd",
                    "gdelt":         "#c7c7c7",
                },
                labels={"articulos":"Artículos","label":"Narrativa","bando":"Bando"}
            )
            fig2.update_layout(height=420)
            st.plotly_chart(fig2, width="stretch")

        # Divergencia narrativa
        div_path = os.path.join(DATA_DIR, "iran_divergencia.csv")
        if os.path.exists(div_path):
            st.subheader("📐 Divergencia narrativa por cluster")
            df_div = pd.read_csv(div_path)
            df_div = df_div.merge(df_nar[["cluster","label"]], on="cluster", how="left")
            fig3 = px.bar(
                df_div.sort_values("divergencia", ascending=False),
                x="label", y="divergencia", color="divergencia",
                color_continuous_scale="RdYlGn_r",
                title="Divergencia occidente vs eje iraní (1=máxima)",
                labels={"divergencia":"Índice divergencia","label":"Narrativa"}
            )
            st.plotly_chart(fig3, width="stretch")

    else:
        st.info("Sin datos de narrativas aún — ejecuta el pipeline en el Odroid")

    # Keywords globales
    if os.path.exists(kw_path):
        st.subheader("☁️ Keywords más frecuentes")
        df_kw = pd.read_csv(kw_path)
        try:
            from wordcloud import WordCloud
            import io
            freq = dict(zip(df_kw["keyword"], df_kw["score"]))
            wc = WordCloud(width=900, height=300, background_color="black",
                           colormap="Reds", max_words=50)
            wc.generate_from_frequencies(freq)
            buf = io.BytesIO()
            wc.to_image().save(buf, format="PNG")
            buf.seek(0)
            st.image(buf, width="stretch")
        except:
            fig_kw = px.bar(df_kw.head(20), x="keyword", y="score",
                            color="score", color_continuous_scale="Reds")
            st.plotly_chart(fig_kw, width="stretch")

    # Sentimiento por bando
    if os.path.exists(sent_path):
        st.subheader("🧠 Sentimiento por bando")
        df_sb = pd.read_csv(sent_path)
        fig_sb = px.bar(
            df_sb, x="bando", y="count", color="sentiment",
            barmode="stack",
            color_discrete_map={"positivo":"#2ECC71","negativo":"#E74C3C","neutral":"#95A5A6"},
            title="Distribución de sentimiento por bando geopolítico"
        )
        st.plotly_chart(fig_sb, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MAPA DE ALIANZAS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("🗺️ Mapa de Alianzas Geopolíticas")
    st.markdown("Posicionamiento de países respecto al conflicto — datos estáticos actualizados manualmente + narrativa mediática detectada.")

    # Datos de alianzas (estáticos, actualizados a Mar-2026)
    alianzas = [
        # Pro-EEUU/Israel
        {"pais":"United States","lat":37.09,"lon":-95.71,"posicion":"Pro-EEUU/Israel","peso":10,"detalle":"Operación Epic Fury — ataque directo"},
        {"pais":"Israel","lat":31.05,"lon":34.85,"posicion":"Pro-EEUU/Israel","peso":10,"detalle":"Coautor del ataque"},
        {"pais":"United Kingdom","lat":55.38,"lon":-3.44,"posicion":"Pro-EEUU/Israel","peso":7,"detalle":"Apoyo logístico"},
        {"pais":"Germany","lat":51.17,"lon":10.45,"posicion":"Pro-EEUU/Israel","peso":5,"detalle":"Apoyo político E3"},
        {"pais":"France","lat":46.23,"lon":2.21,"posicion":"Pro-EEUU/Israel","peso":5,"detalle":"Apoyo político E3"},
        {"pais":"Saudi Arabia","lat":23.89,"lon":45.08,"posicion":"Pro-EEUU/Israel","peso":6,"detalle":"Apoyo tácito — rivalidad regional"},
        {"pais":"UAE","lat":23.42,"lon":53.85,"posicion":"Pro-EEUU/Israel","peso":5,"detalle":"Apoyo logístico bases"},
        {"pais":"Jordan","lat":30.59,"lon":36.24,"posicion":"Pro-EEUU/Israel","peso":4,"detalle":"Espacio aéreo"},
        {"pais":"Australia","lat":-25.27,"lon":133.78,"posicion":"Pro-EEUU/Israel","peso":4,"detalle":"Apoyo político"},
        {"pais":"Canada","lat":56.13,"lon":-106.35,"posicion":"Pro-EEUU/Israel","peso":4,"detalle":"Apoyo político"},
        # Pro-Irán
        {"pais":"Russia","lat":61.52,"lon":105.32,"posicion":"Pro-Irán/Eje","peso":9,"detalle":"Veto ONU — suministro militar"},
        {"pais":"China","lat":35.86,"lon":104.20,"posicion":"Pro-Irán/Eje","peso":9,"detalle":"Veto ONU — socio energético"},
        {"pais":"Syria","lat":34.80,"lon":38.99,"posicion":"Pro-Irán/Eje","peso":6,"detalle":"Frente norte activo"},
        {"pais":"Iraq","lat":33.22,"lon":43.68,"posicion":"Pro-Irán/Eje","peso":6,"detalle":"Milicias PMF activas"},
        {"pais":"Yemen","lat":15.55,"lon":48.52,"posicion":"Pro-Irán/Eje","peso":5,"detalle":"Houthis — ataques Bab-el-Mandeb"},
        {"pais":"Venezuela","lat":6.42,"lon":-66.59,"posicion":"Pro-Irán/Eje","peso":3,"detalle":"Apoyo político — petróleo"},
        {"pais":"North Korea","lat":40.34,"lon":127.51,"posicion":"Pro-Irán/Eje","peso":4,"detalle":"Suministro munición"},
        {"pais":"Belarus","lat":53.71,"lon":27.95,"posicion":"Pro-Irán/Eje","peso":3,"detalle":"Apoyo político"},
        # Neutros / ambiguos
        {"pais":"India","lat":20.59,"lon":78.96,"posicion":"Neutro/Ambiguo","peso":7,"detalle":"Petróleo iraní — presión EEUU"},
        {"pais":"Turkey","lat":38.96,"lon":35.24,"posicion":"Neutro/Ambiguo","peso":6,"detalle":"OTAN + comercio con Irán"},
        {"pais":"Qatar","lat":25.35,"lon":51.18,"posicion":"Neutro/Ambiguo","peso":5,"detalle":"Mediador + Al Jazeera"},
        {"pais":"Pakistan","lat":30.38,"lon":69.35,"posicion":"Neutro/Ambiguo","peso":5,"detalle":"Frontera iraní — presión interna"},
        {"pais":"South Africa","lat":-30.56,"lon":22.94,"posicion":"Neutro/Ambiguo","peso":4,"detalle":"BRICS — posición neutral"},
        {"pais":"Brazil","lat":-14.24,"lon":-51.93,"posicion":"Neutro/Ambiguo","peso":4,"detalle":"BRICS — abstención ONU"},
        {"pais":"Indonesia","lat":-0.79,"lon":113.92,"posicion":"Neutro/Ambiguo","peso":4,"detalle":"Mayor país musulmán — neutralidad"},
        {"pais":"Egypt","lat":26.82,"lon":30.80,"posicion":"Neutro/Ambiguo","peso":5,"detalle":"Canal Suez — equilibrio regional"},
        {"pais":"Spain","lat":40.42,"lon":-3.70,"posicion":"Neutro/Ambiguo","peso":6,"detalle":"OTAN member — bases usadas (Morón, Rota) — Sánchez: 'No a la guerra'"},
    ]

    df_map = pd.DataFrame(alianzas)

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Pro-EEUU/Israel", len(df_map[df_map["posicion"]=="Pro-EEUU/Israel"]))
    col_m2.metric("Pro-Irán/Eje", len(df_map[df_map["posicion"]=="Pro-Irán/Eje"]))
    col_m3.metric("Neutros/Ambiguos", len(df_map[df_map["posicion"]=="Neutro/Ambiguo"]))

    fig_map = px.scatter_geo(
        df_map,
        lat="lat", lon="lon",
        size="peso",
        color="posicion",
        hover_name="pais",
        hover_data={"detalle":True,"peso":False,"lat":False,"lon":False},
        color_discrete_map={
            "Pro-EEUU/Israel": "#1f77b4",
            "Pro-Irán/Eje":    "#d62728",
            "Neutro/Ambiguo":  "#f0a500",
        },
        size_max=30,
        title="Mapa de alianzas — Conflicto Iraní 2026",
        text="pais",
    )
    fig_map.update_traces(textposition="top center", textfont=dict(size=9))
    fig_map.update_geos(
        showland=True, landcolor="#1a1a2e",
        showcoastlines=True, coastlinecolor="#555577",
        showcountries=True, countrycolor="#555577",
        showocean=True, oceancolor="#0d0d1a",
        bgcolor="#0d0d1a",
        projection_type="natural earth",
    )
    fig_map.update_layout(
        height=520,
        paper_bgcolor="#0d0d1a",
        font=dict(color="white"),
        legend=dict(title="Posición", bgcolor="rgba(0,0,0,0.5)"),
        margin={"r":0,"t":40,"l":0,"b":0},
    )
    st.plotly_chart(fig_map, width="stretch")

    st.subheader("📋 Detalle por país")
    posicion_sel = st.selectbox("Filtrar por posición:",
        ["Todos","Pro-EEUU/Israel","Pro-Irán/Eje","Neutro/Ambiguo"])
    df_show = df_map if posicion_sel == "Todos" else df_map[df_map["posicion"]==posicion_sel]
    st.dataframe(df_show[["pais","posicion","peso","detalle"]].sort_values("peso",ascending=False),
                 width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ENERGÍA & ORMUZ
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("⚡ Energía, Mercados y Estrecho de Ormuz")
    st.markdown("El conflicto iraní controla el **20% del comercio mundial de petróleo** — Brent subió >40% en 10 días desde el inicio.")

    energy_path = os.path.join(DATA_DIR, "iran_energy.csv")
    ormuz_path  = os.path.join(DATA_DIR, "iran_ormuz.json")

    # Ormuz status
    if os.path.exists(ormuz_path):
        ormuz = json.load(open(ormuz_path))
        nivel = ormuz.get("nivel","verde")
        color_nivel = {"verde":"🟢","naranja":"🟠","rojo":"🔴"}.get(nivel,"⚪")
        alertas = ormuz.get("alertas", 0)
        col_o1, col_o2, col_o3 = st.columns(3)
        col_o1.metric("Estado Ormuz", f"{color_nivel} {nivel.upper()}")
        col_o2.metric("Alertas en noticias", alertas)
        col_o3.metric("Actualizado", ormuz.get("updated","")[:16])
        if ormuz.get("titulares"):
            st.markdown("**Últimas noticias sobre Ormuz:**")
            for t in ormuz["titulares"]:
                st.markdown(f"- {t}")
        st.markdown("---")

    # Precio Brent
    if os.path.exists(energy_path):
        df_en = pd.read_csv(energy_path)
        df_brent = df_en[df_en["commodity"].str.contains("Brent")]
        df_gas   = df_en[df_en["commodity"].str.contains("Gas")]

        col_e1, col_e2, col_e3 = st.columns(3)
        if not df_brent.empty:
            precio_actual = df_brent["price"].iloc[0]
            precio_prev   = df_brent["price"].iloc[1] if len(df_brent) > 1 else precio_actual
            col_e1.metric("Brent (USD/barril)", f"{precio_actual:.1f}",
                          f"{precio_actual-precio_prev:+.1f} vs anterior")
        if not df_gas.empty:
            col_e2.metric("Gas Natural", f"{df_gas['price'].iloc[0]:.2f}")
        col_e3.metric("Ref. pre-conflicto", "73.0 USD", "-31% desde 27-Feb")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if len(df_brent) > 1:
                fig_e = px.line(
                    df_brent.sort_values("date"), x="date", y="price",
                    title="Precio Brent (USD/barril)",
                    labels={"date":"Fecha","price":"USD/barril"},
                    markers=True,
                )
                fig_e.update_traces(line_color="#e05c00", line_width=2)
                fig_e.add_hline(y=73, line_dash="dash", line_color="green",
                                annotation_text="Pre-conflicto 73$")
                fig_e.add_hline(y=107, line_dash="dash", line_color="red",
                                annotation_text="Pico 107$ (8-Mar)")
                st.plotly_chart(fig_e, width="stretch")
            else:
                st.info("Historial Brent: disponible con Alpha Vantage key")

        with col_g2:
            # Impacto por país importador
            impacto = pd.DataFrame([
                {"pais":"China","importacion_mbpd":10.5,"exposicion":"Alta"},
                {"pais":"India","importacion_mbpd":4.8,"exposicion":"Alta"},
                {"pais":"Japan","importacion_mbpd":2.9,"exposicion":"Media"},
                {"pais":"South Korea","importacion_mbpd":2.1,"exposicion":"Media"},
                {"pais":"EU","importacion_mbpd":1.8,"exposicion":"Media"},
                {"pais":"USA","importacion_mbpd":0.8,"exposicion":"Baja"},
            ])
            fig_imp = px.bar(
                impacto, x="pais", y="importacion_mbpd",
                color="exposicion",
                color_discrete_map={"Alta":"#d62728","Media":"#f0a500","Baja":"#2ca02c"},
                title="Importación petróleo Golfo (millones bpd)",
                labels={"importacion_mbpd":"M barriles/día","pais":"País"}
            )
            st.plotly_chart(fig_imp, width="stretch")
    else:
        st.info("Sin datos energéticos aún — ejecuta energy_tracker.py")
        st.markdown("""
**Contexto manual (actualizado 16-Mar-2026):**
- Brent: ~107 USD/barril (+46% desde 27-Feb)
- Natural Gas EU: +38% desde inicio del conflicto
- Estrecho de Ormuz: 20% comercio mundial petróleo en riesgo
- Arabia Saudí ha aumentado producción para compensar
        """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ÚLTIMAS NOTICIAS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("📰 Últimas Noticias por Bando")

    news_path = os.path.join(DATA_DIR, "iran_news.csv")
    if os.path.exists(news_path):
        df_news = pd.read_csv(news_path)
        bandos_disp = ["Todos"] + sorted(df_news["bando"].dropna().unique().tolist())
        col_f1, col_f2 = st.columns(2)
        bando_sel  = col_f1.selectbox("Bando:", bandos_disp)
        source_sel = col_f2.selectbox("Fuente:", ["Todas"] + sorted(df_news["source"].dropna().unique().tolist()))

        df_filt = df_news.copy()
        if bando_sel != "Todos":
            df_filt = df_filt[df_filt["bando"] == bando_sel]
        if source_sel != "Todas":
            df_filt = df_filt[df_filt["source"] == source_sel]

        st.markdown(f"**{len(df_filt)} artículos** encontrados")
        for _, row in df_filt.head(30).iterrows():
            bando_color = {
                "pro_occidente":"🔵","pro_iran_eje":"🔴",
                "neutros_regionales":"🟡","gdelt":"⚪"
            }.get(str(row.get("bando","")), "⚫")
            url = row.get("url","")
            titulo = row.get("title","Sin título")
            if url and str(url) != "nan":
                st.markdown(f"{bando_color} [{titulo}]({url}) — *{row.get('source','')}*")
            else:
                st.markdown(f"{bando_color} {titulo} — *{row.get('source','')}*")
    else:
        st.info("Sin noticias aún — ejecuta el pipeline primero")

with tab5:
    st.header("ℹ️ Guía de uso & Créditos")
    st.markdown("---")

    st.subheader("🎯 ¿Qué es Iran OSINT Monitor?")
    st.markdown("""
Plataforma de inteligencia de fuentes abiertas (OSINT) para el seguimiento del conflicto iraní.
Monitoriza narrativas, alianzas geopolíticas, mercados energéticos y desinformación en tiempo real
desde **múltiples bandos y perspectivas**.
    """)

    st.subheader("📡 Cómo interpretar cada tab")
    st.markdown("""
| Tab | Qué muestra | Cómo leerlo |
|-----|-------------|-------------|
| **Radar Narrativo** | Clusters temáticos por bando | Verde = Occidente domina · Rojo = Irán domina · Gris = equilibrado |
| **Mapa de Alianzas** | Posicionamiento de países | Azul = Pro-EEUU/Israel · Rojo = Pro-Irán · Amarillo = Neutro |
| **Energía & Ormuz** | Precio Brent + estado estrecho | Rojo = alerta · Verde = estable |
| **Últimas Noticias** | Feed por bando geopolítico | 🔵 Occidente · 🔴 Irán · 🟡 Neutros |
    """)

    st.subheader("➕ Cómo añadir nuevas fuentes RSS")
    st.markdown("""
Edita el fichero `config/sources_iran.yaml` en el Odroid:
```yaml
pro_occidente:
  - name: NombreFuente
    url: https://ejemplo.com/rss.xml
    lang: en
    bias: western
```

**Bandos disponibles:** `pro_occidente`, `pro_iran_eje`, `neutros_regionales`

Tras añadir la fuente, el pipeline la recogerá automáticamente en el siguiente ciclo (cada 30 min).
    """)

    st.subheader("🔄 Pipeline automático")
    st.markdown("""
- **Frecuencia**: cada 30 minutos via cron
- **Scripts**: `collect_iran.py` → `detect_narratives_iran.py` → `detect_sentiment_iran.py` → `energy_tracker.py`
- **Log**: `pipeline_iran.log` en el directorio raíz
    """)

    st.subheader("⚠️ Limitaciones")
    st.markdown("""
- El análisis de sentimiento es léxico — no detecta ironía ni contexto complejo
- Los datos de alianzas del Mapa son semi-estáticos (actualización manual)
- GDELT requiere ajuste de fechas para funcionar correctamente
- La API de Claude es opcional — el pipeline funciona sin ella
    """)

    st.markdown("---")
    st.subheader("© Créditos & Contacto")
    st.markdown("""
**Autor:** M. Castillo  
**Email:** [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)  
**Proyecto:** Iran OSINT Monitor — Plataforma OSINT Geopolítica  
**Versión:** v0.2 · Sprint 1  
**Licencia:** Uso personal e investigación — no redistribuir sin permiso  

*Datos obtenidos de fuentes públicas (RSS, GDELT, Alpha Vantage).  
Este proyecto no representa ninguna posición política oficial.*
    """)

st.markdown("---")
st.caption("🛰️ Iran OSINT Monitor · Sprint 1 · © M. Castillo · mybloggingnotes@gmail.com · v0.1")
