"""
dashboard.py
==============================================================================
SENTINELA ORBITAL - Dashboard interativo (camada de visualizacao).

Painel web que consolida as tres camadas do sistema em uma unica interface,
com filtros por bioma e periodo. Inclui um PREVISOR DE RISCO interativo: o
usuario ajusta as condicoes climaticas e o modelo de IA estima o nivel de
risco em tempo real - mostrando o modelo "vivo", e nao apenas metricas.

TECNOLOGIAS: Streamlit (app web) + Plotly (graficos interativos) + o modelo
de Machine Learning treinado (joblib).

COMO EXECUTAR:
    pip install streamlit plotly
    streamlit run dashboard.py

Conceitos das Fases 3 e 4: visualizacao de dados, dashboards interativos,
integracao de modelo de ML em uma aplicacao, manipulacao de dados.
==============================================================================
"""

from __future__ import annotations

import os

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PASTA_BASE = os.path.join(os.path.dirname(__file__), "..")
PASTA_DADOS = os.path.join(PASTA_BASE, "dados")
PASTA_MODELOS = os.path.join(PASTA_BASE, "modelos")

LARANJA = "#E8501F"
CORES_RISCO = {"Baixo": "#2E8B57", "Moderado": "#F5A623",
               "Alto": "#E8501F", "Critico": "#9B1B1B"}
ATRIBUTOS = ["t2m", "t2m_max", "rh2m", "prectotcorr", "ws2m",
             "dias_sem_chuva", "vegetacao"]

st.set_page_config(page_title="Sentinela Orbital",
                   page_icon="[*]", layout="wide")


# ---------------------------------------------------------------------------
# Carregamento (cacheado para performance)
# ---------------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    focos = pd.read_csv(os.path.join(PASTA_DADOS, "focos_inpe.csv"),
                        parse_dates=["data"])
    clima = pd.read_csv(os.path.join(PASTA_DADOS, "clima_nasa.csv"),
                        parse_dates=["data"])
    esp = pd.read_csv(os.path.join(PASTA_DADOS, "leituras_esp32.csv"),
                      parse_dates=["timestamp"])
    return focos, clima, esp


@st.cache_resource
def carregar_modelo():
    caminho = os.path.join(PASTA_MODELOS, "modelo_classificacao.joblib")
    return joblib.load(caminho) if os.path.exists(caminho) else None


focos, clima, esp = carregar_dados()
modelo = carregar_modelo()

# ---------------------------------------------------------------------------
# Cabecalho
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{LARANJA};margin-bottom:0'>SENTINELA ORBITAL</h1>"
    "<p style='color:#888;margin-top:0'>Previsao e monitoramento de queimadas "
    "- dados orbitais (INPE/NASA) + IA + sensores ESP32</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")
    biomas_sel = st.multiselect(
        "Biomas", sorted(focos["bioma"].unique()),
        default=sorted(focos["bioma"].unique()))
    meses = st.slider("Periodo (mes)", 1, 12, (7, 10))

mask = (focos["bioma"].isin(biomas_sel)
        & focos["data"].dt.month.between(meses[0], meses[1]))
focos_f = focos[mask]

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Focos no periodo", f"{len(focos_f):,}")
c2.metric("FRP medio", f"{focos_f['frp_mw'].mean():.0f} MW"
          if len(focos_f) else "0 MW")
c3.metric("Estacoes ESP32", f"{esp['estacao_id'].nunique()}")
alertas_sensores = int((esp["fumaca_ppm"] > 500).sum())
c4.metric("Alertas de fumaca", f"{alertas_sensores}")

st.divider()

col_mapa, col_serie = st.columns([1.2, 1])

# ---------------------------------------------------------------------------
# Mapa de focos
# ---------------------------------------------------------------------------
with col_mapa:
    st.subheader("Mapa de focos de calor")
    amostra = focos_f.sample(min(3000, len(focos_f)), random_state=1) \
        if len(focos_f) else focos_f
    if len(amostra):
        fig_mapa = px.scatter_geo(
            amostra, lat="latitude", lon="longitude", color="bioma",
            hover_data=["satelite", "frp_mw"], scope="south america",
            opacity=0.6)
        fig_mapa.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0),
                               legend_title_text="Bioma")
        fig_mapa.update_geos(showcountries=True, landcolor="#f2f2f2")
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.info("Sem focos para os filtros selecionados.")

# ---------------------------------------------------------------------------
# Serie temporal
# ---------------------------------------------------------------------------
with col_serie:
    st.subheader("Evolucao mensal")
    serie = focos_f.set_index("data").resample("ME").size()
    fig_serie = go.Figure()
    fig_serie.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines+markers",
        line=dict(color=LARANJA, width=3), fill="tozeroy",
        fillcolor="rgba(232,80,31,0.15)"))
    fig_serie.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0),
                            yaxis_title="Focos")
    st.plotly_chart(fig_serie, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Previsor de risco (modelo de IA ao vivo)
# ---------------------------------------------------------------------------
st.subheader("Previsor de risco com IA")
st.caption("Ajuste as condicoes climaticas e veja a estimativa do modelo.")

pc1, pc2, pc3 = st.columns(3)
with pc1:
    t2m_max = st.slider("Temperatura maxima (C)", 15.0, 45.0, 38.0, 0.5)
    rh2m = st.slider("Umidade do ar (%)", 5.0, 100.0, 22.0, 1.0)
with pc2:
    prec = st.slider("Precipitacao (mm)", 0.0, 50.0, 0.0, 0.5)
    dias_sem_chuva = st.slider("Dias sem chuva", 0, 30, 18, 1)
with pc3:
    vento = st.slider("Vento (m/s)", 0.0, 12.0, 3.0, 0.5)
    vegetacao = st.slider("Carga de vegetacao", 0.3, 1.0, 0.7, 0.05)

if modelo is not None:
    entrada = pd.DataFrame([{
        "t2m": t2m_max - 4, "t2m_max": t2m_max, "rh2m": rh2m,
        "prectotcorr": prec, "ws2m": vento,
        "dias_sem_chuva": dias_sem_chuva, "vegetacao": vegetacao,
    }])[ATRIBUTOS]
    classe = str(modelo.predict(entrada)[0])
    probs = modelo.predict_proba(entrada)[0]
    cor = CORES_RISCO.get(classe, LARANJA)

    rc1, rc2 = st.columns([1, 2])
    with rc1:
        st.markdown(
            f"<div style='background:{cor};padding:24px;border-radius:12px;"
            f"text-align:center'><span style='color:white;font-size:14px'>"
            f"NIVEL DE RISCO</span><br><span style='color:white;"
            f"font-size:34px;font-weight:bold'>{classe.upper()}</span></div>",
            unsafe_allow_html=True)
    with rc2:
        fig_prob = go.Figure(go.Bar(
            x=modelo.classes_, y=probs,
            marker_color=[CORES_RISCO.get(c, LARANJA)
                          for c in modelo.classes_]))
        fig_prob.update_layout(height=220, yaxis_title="Probabilidade",
                               margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_prob, use_container_width=True)
else:
    st.warning("Modelo nao encontrado. Rode 'python modelo_risco.py' antes.")

st.divider()
st.caption("Sentinela Orbital - Global Solution 2026.1 / FIAP - "
           "POC academica com dados sinteticos modelados em padroes reais.")
