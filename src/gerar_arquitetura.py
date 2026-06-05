"""
gerar_arquitetura.py
==============================================================================
SENTINELA ORBITAL - Diagrama de arquitetura do sistema (para PDF/README).

Desenha o fluxo completo de dados das 3 camadas ate a entrega, com a estetica
da marca. Salva em assets/11_arquitetura.png e assets/12_fluxo_pipeline.png.
==============================================================================
"""

import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

PASTA_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")

LARANJA = "#E8501F"
AZUL = "#2E5E8C"
TEAL = "#1F9E8E"
GRAFITE = "#26262E"
CINZA = "#8A8A95"
AMARELO = "#F5A623"
FUNDO = "#FFFFFF"


def caixa(ax, x, y, w, h, titulo, sub="", cor=GRAFITE, cor_texto="white",
          fonte=10.5):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor=cor, edgecolor="none", zorder=2))
    cy = y + h / 2
    if sub:
        ax.text(x + w / 2, cy + h * 0.16, titulo, ha="center", va="center",
                color=cor_texto, fontsize=fonte, fontweight="bold", zorder=3)
        ax.text(x + w / 2, cy - h * 0.20, sub, ha="center", va="center",
                color=cor_texto, fontsize=fonte - 2.5, zorder=3, alpha=0.92)
    else:
        ax.text(x + w / 2, cy, titulo, ha="center", va="center",
                color=cor_texto, fontsize=fonte, fontweight="bold", zorder=3)


def seta(ax, x1, y1, x2, y2, cor=CINZA):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
        color=cor, linewidth=2, zorder=1,
        connectionstyle="arc3,rad=0.0"))


def diagrama_arquitetura():
    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis("off")
    fig.patch.set_facecolor(FUNDO)

    # Titulos das colunas (estagios)
    estagios = [
        (11, "1. COLETA", "Fontes de dados"),
        (35, "2. PROCESSAMENTO", "Python / Pandas"),
        (60, "3. INTELIGENCIA", "Machine Learning"),
        (85, "4. DECISAO & ENTREGA", "Fusao e visualizacao"),
    ]
    for x, t, s in estagios:
        ax.text(x, 67, t, ha="center", fontsize=11.5, fontweight="bold",
                color=GRAFITE)
        ax.text(x, 63.5, s, ha="center", fontsize=9, color=CINZA)

    # ---- Coluna 1: fontes (3 camadas) ----
    caixa(ax, 2, 48, 18, 9, "Satelites INPE", "Focos de calor", cor=LARANJA)
    caixa(ax, 2, 35, 18, 9, "NASA POWER", "Clima diario", cor=AZUL)
    caixa(ax, 2, 22, 18, 9, "Estacoes ESP32", "Sensores no chao", cor=TEAL)

    # ---- Coluna 2: ingestao + analise ----
    caixa(ax, 27, 41, 18, 9, "Ingestao", "APIs + fallback\n(ingestao_dados)",
          cor=GRAFITE)
    caixa(ax, 27, 28, 18, 9, "MQTT", "Telemetria\n(mqtt_receptor)", cor=GRAFITE)
    caixa(ax, 27, 14.5, 18, 9, "Analise (EDA)", "Pandas / Seaborn", cor="#4A4A55")

    # ---- Coluna 3: ML ----
    caixa(ax, 52, 41, 18, 11, "Modelo de IA",
          "Random Forest\nRegressao + Classif.", cor="#9B1B1B")
    caixa(ax, 52, 25, 18, 9, "Banco SQLite", "Persistencia", cor="#4A4A55")

    # ---- Coluna 4: decisao e entrega ----
    caixa(ax, 77, 44, 18, 10, "Motor de Alertas",
          "Fusao das 3 camadas\n-> score 0-100", cor=AMARELO,
          cor_texto=GRAFITE)
    caixa(ax, 77, 30, 18, 9, "Dashboard", "Streamlit + Plotly", cor=LARANJA)
    caixa(ax, 77, 17, 18, 9, "Alertas", "VERDE -> VERMELHO", cor="#D7263D")

    # ---- Setas coluna 1 -> 2 ----
    seta(ax, 20, 52, 27, 46)   # INPE -> ingestao
    seta(ax, 20, 39, 27, 45)   # NASA -> ingestao
    seta(ax, 20, 26, 27, 32)   # ESP32 -> MQTT

    # ingestao/mqtt -> analise e ML
    seta(ax, 36, 41, 36, 23.5)        # ingestao -> analise
    seta(ax, 45, 45, 52, 47)          # ingestao -> ML
    seta(ax, 45, 32, 52, 44)          # mqtt -> ML
    seta(ax, 45, 32, 52, 30)          # mqtt -> SQLite

    # analise -> ML (feedback de features)
    seta(ax, 45, 19, 52, 42)          # analise -> ML

    # ML -> motor de alertas
    seta(ax, 70, 47, 77, 49)          # ML -> motor
    seta(ax, 70, 30, 77, 33)          # SQLite -> dashboard (dados)

    # motor -> dashboard e alertas
    seta(ax, 86, 44, 86, 39)          # motor -> dashboard
    seta(ax, 86, 44, 86, 26)          # motor -> alertas (passa por dashboard)

    # faixa de acento no topo
    ax.add_patch(plt.Rectangle((2, 69.2), 6, 0.6, facecolor=LARANJA,
                 edgecolor="none"))
    ax.text(2, 60.4, "Arquitetura do Sentinela Orbital", fontsize=15,
            fontweight="bold", color=GRAFITE)

    plt.tight_layout()
    fig.savefig(os.path.join(PASTA_ASSETS, "11_arquitetura.png"),
                facecolor=FUNDO, dpi=150, bbox_inches="tight")
    plt.close()
    print("Diagrama de arquitetura salvo em assets/11_arquitetura.png")


def diagrama_pipeline():
    """Fluxograma linear simples do pipeline de execucao (passo a passo)."""
    fig, ax = plt.subplots(figsize=(12, 2.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.axis("off")
    fig.patch.set_facecolor(FUNDO)

    etapas = [
        ("gerar_dados", LARANJA),
        ("analise_\nexploratoria", AZUL),
        ("modelo_risco", "#9B1B1B"),
        ("mqtt_receptor", TEAL),
        ("motor_alertas", AMARELO),
        ("dashboard", LARANJA),
    ]
    larg = 13
    gap = (100 - larg * len(etapas)) / (len(etapas) + 1)
    x = gap
    centros = []
    for nome, cor in etapas:
        ct = "white" if cor != AMARELO else GRAFITE
        caixa(ax, x, 6, larg, 8, nome, cor=cor, cor_texto=ct, fonte=9.5)
        centros.append(x + larg)
        x += larg + gap

    for i in range(len(etapas) - 1):
        seta(ax, centros[i], 10, centros[i] + gap, 10)

    ax.text(0, 17, "Fluxo de execucao (pipeline)", fontsize=13,
            fontweight="bold", color=GRAFITE)
    plt.tight_layout()
    fig.savefig(os.path.join(PASTA_ASSETS, "12_fluxo_pipeline.png"),
                facecolor=FUNDO, dpi=150, bbox_inches="tight")
    plt.close()
    print("Fluxograma do pipeline salvo em assets/12_fluxo_pipeline.png")


if __name__ == "__main__":
    diagrama_arquitetura()
    diagrama_pipeline()
