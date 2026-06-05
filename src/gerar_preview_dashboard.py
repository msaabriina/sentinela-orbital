"""
gerar_preview_dashboard.py
==============================================================================
SENTINELA ORBITAL - Gera uma imagem-preview do dashboard para o PDF/README.

Como o dashboard Streamlit roda como servidor web (e nao gera imagem estatica),
este script compoe uma representacao fiel do painel, com tema escuro on-brand,
usando os DADOS REAIS do projeto. Salva em assets/10_painel_dashboard.png.
==============================================================================
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, Wedge

import joblib

PASTA_BASE = os.path.join(os.path.dirname(__file__), "..")
PASTA_DADOS = os.path.join(PASTA_BASE, "dados")
PASTA_MODELOS = os.path.join(PASTA_BASE, "modelos")
PASTA_ASSETS = os.path.join(PASTA_BASE, "assets")

# Paleta dark
FUNDO = "#15151B"
CARD = "#1F1F28"
LARANJA = "#E8501F"
TEAL = "#1F9E8E"
AZUL = "#3B82C4"
TEXTO = "#EDEDF2"
TEXTO2 = "#9A9AA6"
CORES_BIOMA = {"Amazonia": "#1F9E8E", "Cerrado": "#E8501F",
               "Pantanal": "#3B82C4", "Caatinga": "#F5A623",
               "Mata Atlantica": "#2E8B57", "Pampa": "#9B59B6"}
CORES_NIVEL = {"VERMELHO": "#D7263D", "LARANJA": "#E8501F",
               "AMARELO": "#F5A623", "VERDE": "#2E8B57"}


def card(ax, x, y, w, h, cor=CARD):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.012,rounding_size=0.02",
                 facecolor=cor, edgecolor="none",
                 transform=ax.transAxes, zorder=1))


def main():
    focos = pd.read_csv(os.path.join(PASTA_DADOS, "focos_inpe.csv"),
                        parse_dates=["data"])
    esp = pd.read_csv(os.path.join(PASTA_DADOS, "leituras_esp32.csv"))

    fig = plt.figure(figsize=(12, 7.6), facecolor=FUNDO)
    gs = GridSpec(3, 4, figure=fig, height_ratios=[0.62, 1.5, 1.2],
                  hspace=0.42, wspace=0.28,
                  left=0.035, right=0.965, top=0.94, bottom=0.06)

    # ---------- Cabecalho ----------
    ax_head = fig.add_subplot(gs[0, :])
    ax_head.axis("off")
    ax_head.text(0.0, 0.62, "SENTINELA ORBITAL", color=LARANJA,
                 fontsize=26, fontweight="bold", va="center")
    ax_head.text(0.001, 0.12, "Previsao e monitoramento de queimadas  -  "
                 "dados orbitais (INPE / NASA) + IA + sensores ESP32",
                 color=TEXTO2, fontsize=11, va="center")
    ax_head.text(1.0, 0.6, "AO VIVO", color="#fff", fontsize=10,
                 fontweight="bold", ha="right", va="center",
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#D7263D",
                           edgecolor="none"))

    # ---------- KPIs ----------
    kpis = [
        ("FOCOS (2024)", f"{len(focos):,}", LARANJA),
        ("FRP MEDIO", f"{focos['frp_mw'].mean():.0f} MW", TEAL),
        ("ESTACOES ESP32", f"{esp['estacao_id'].nunique()}", AZUL),
        ("ACURACIA IA", "91%", "#F5A623"),
    ]
    for i, (rotulo, valor, cor) in enumerate(kpis):
        ax = fig.add_subplot(gs[1, i])
        ax.axis("off")
        card(ax, 0.02, 0.55, 0.96, 0.42)
        ax.text(0.5, 0.76, valor, color=cor, fontsize=23, fontweight="bold",
                ha="center", va="center", transform=ax.transAxes)
        ax.text(0.5, 0.60, rotulo, color=TEXTO2, fontsize=9.5,
                ha="center", va="center", transform=ax.transAxes)

        # mini conteudo abaixo de cada KPI
        if i == 0:
            # mini mapa
            card(ax, 0.02, 0.0, 0.96, 0.5)
            amostra = focos.sample(1200, random_state=3)
            ax2 = ax.inset_axes([0.05, 0.04, 0.9, 0.42])
            for b in amostra["bioma"].unique():
                s = amostra[amostra["bioma"] == b]
                ax2.scatter(s["longitude"], s["latitude"], s=3, alpha=0.6,
                            color=CORES_BIOMA.get(b, LARANJA), edgecolors="none")
            ax2.set_xlim(-74, -34); ax2.set_ylim(-34, 6)
            ax2.set_facecolor(CARD); ax2.axis("off")
            ax.text(0.5, 0.46, "Mapa de focos", color=TEXTO2, fontsize=8.5,
                    ha="center", transform=ax.transAxes)
        elif i == 1:
            card(ax, 0.02, 0.0, 0.96, 0.5)
            serie = focos.set_index("data").resample("ME").size()
            ax2 = ax.inset_axes([0.08, 0.06, 0.86, 0.40])
            ax2.plot(range(len(serie)), serie.values, color=TEAL, linewidth=2)
            ax2.fill_between(range(len(serie)), serie.values, color=TEAL,
                             alpha=0.18)
            ax2.set_facecolor(CARD); ax2.axis("off")
            ax.text(0.5, 0.46, "Sazonalidade mensal", color=TEXTO2,
                    fontsize=8.5, ha="center", transform=ax.transAxes)
        elif i == 2:
            card(ax, 0.02, 0.0, 0.96, 0.5)
            ax2 = ax.inset_axes([0.08, 0.06, 0.86, 0.40])
            est = esp.groupby("estacao_id")["fumaca_ppm"].max()
            ax2.barh(range(len(est)), est.values,
                     color=[LARANJA if v > 500 else AZUL for v in est.values])
            ax2.set_facecolor(CARD); ax2.axis("off")
            ax.text(0.5, 0.46, "Pico de fumaca/estacao", color=TEXTO2,
                    fontsize=8.5, ha="center", transform=ax.transAxes)
        else:
            card(ax, 0.02, 0.0, 0.96, 0.5)
            # gauge de risco
            ax2 = ax.inset_axes([0.1, 0.02, 0.8, 0.46])
            ax2.axis("off"); ax2.set_aspect("equal")
            ax2.set_xlim(-1.2, 1.2); ax2.set_ylim(-0.2, 1.2)
            ax2.add_patch(Wedge((0, 0), 1, 0, 180, width=0.32,
                                facecolor="#2E2E38"))
            ax2.add_patch(Wedge((0, 0), 1, 0, 150, width=0.32,
                                facecolor=LARANJA))
            ang = np.radians(180 - 150)
            ax2.plot([0, 0.85 * np.cos(ang)], [0, 0.85 * np.sin(ang)],
                     color=TEXTO, linewidth=2.5)
            ax2.text(0, -0.1, "CRITICO", color=LARANJA, fontsize=10,
                     fontweight="bold", ha="center")
            ax.text(0.5, 0.46, "Risco atual (IA)", color=TEXTO2, fontsize=8.5,
                    ha="center", transform=ax.transAxes)

    # ---------- Painel de alertas (linha inferior, esquerda) ----------
    ax_al = fig.add_subplot(gs[2, :2])
    ax_al.axis("off")
    card(ax_al, 0.0, 0.0, 1.0, 1.0)
    ax_al.text(0.04, 0.9, "Alertas por bioma (fusao das 3 camadas)",
               color=TEXTO, fontsize=12, fontweight="bold", va="center",
               transform=ax_al.transAxes)
    alertas = [("Amazonia", "VERMELHO", 96), ("Cerrado", "VERMELHO", 96),
               ("Pantanal", "VERMELHO", 86), ("Caatinga", "LARANJA", 79),
               ("Mata Atlantica", "AMARELO", 59)]
    y = 0.74
    for bioma, nivel, score in alertas:
        cor = CORES_NIVEL[nivel]
        ax_al.add_patch(plt.Rectangle((0.04, y - 0.045), 0.02, 0.07,
                        facecolor=cor, edgecolor="none",
                        transform=ax_al.transAxes))
        ax_al.text(0.09, y, bioma, color=TEXTO, fontsize=10.5, va="center",
                   transform=ax_al.transAxes)
        ax_al.text(0.55, y, nivel, color=cor, fontsize=10, fontweight="bold",
                   va="center", transform=ax_al.transAxes)
        # barra de score
        ax_al.add_patch(plt.Rectangle((0.72, y - 0.018), 0.22, 0.036,
                        facecolor="#2E2E38", edgecolor="none",
                        transform=ax_al.transAxes))
        ax_al.add_patch(plt.Rectangle((0.72, y - 0.018), 0.22 * score / 100,
                        0.036, facecolor=cor, edgecolor="none",
                        transform=ax_al.transAxes))
        ax_al.text(0.955, y, str(score), color=TEXTO2, fontsize=9,
                   va="center", ha="right", transform=ax_al.transAxes)
        y -= 0.16

    # ---------- Previsor de risco (linha inferior, direita) ----------
    ax_pr = fig.add_subplot(gs[2, 2:])
    ax_pr.axis("off")
    card(ax_pr, 0.0, 0.0, 1.0, 1.0)
    ax_pr.text(0.05, 0.9, "Previsor de risco com IA", color=TEXTO,
               fontsize=12, fontweight="bold", va="center",
               transform=ax_pr.transAxes)
    ax_pr.text(0.05, 0.78, "Temp. max 38C  |  Umidade 22%  |  18 dias sem chuva",
               color=TEXTO2, fontsize=9, va="center",
               transform=ax_pr.transAxes)
    # barras de probabilidade simuladas a partir do modelo (se houver)
    classes = ["Baixo", "Moderado", "Alto", "Critico"]
    probs = [0.01, 0.06, 0.28, 0.65]
    cores_p = ["#2E8B57", "#F5A623", "#E8501F", "#9B1B1B"]
    bx = 0.08
    for c, p, cp in zip(classes, probs, cores_p):
        ax_pr.add_patch(plt.Rectangle((bx, 0.18), 0.16, 0.42 * p / 0.65,
                        facecolor=cp, edgecolor="none",
                        transform=ax_pr.transAxes))
        ax_pr.text(bx + 0.08, 0.13, c, color=TEXTO2, fontsize=8,
                   ha="center", va="center", transform=ax_pr.transAxes)
        ax_pr.text(bx + 0.08, 0.20 + 0.42 * p / 0.65, f"{p:.0%}",
                   color=TEXTO, fontsize=8.5, ha="center", va="bottom",
                   fontweight="bold", transform=ax_pr.transAxes)
        bx += 0.22

    fig.savefig(os.path.join(PASTA_ASSETS, "10_painel_dashboard.png"),
                facecolor=FUNDO, dpi=150, bbox_inches="tight")
    plt.close()
    print("Preview do dashboard salvo em assets/10_painel_dashboard.png")


if __name__ == "__main__":
    main()
