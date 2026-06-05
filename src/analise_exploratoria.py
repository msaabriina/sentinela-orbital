"""
analise_exploratoria.py
==============================================================================
SENTINELA ORBITAL - Analise Exploratoria de Dados (EDA).

Carrega as bases geradas, limpa/transforma os dados com Pandas e produz um
conjunto de visualizacoes que sustentam as decisoes do projeto. Todas as
figuras sao salvas em /assets para uso no PDF e no dashboard.

Conceitos das Fases 3 e 4 exercitados:
  - Manipulacao e agregacao de dados com Pandas (groupby, resample, merge)
  - Estatistica descritiva e analise de correlacao
  - Visualizacao de dados com Matplotlib e Seaborn

Uso:
    python analise_exploratoria.py
==============================================================================
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import estilo_viz as ev

PASTA_DADOS = os.path.join(os.path.dirname(__file__), "..", "dados")
PASTA_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(PASTA_ASSETS, exist_ok=True)

ev.aplicar_estilo()

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega as tres bases e faz o parse das datas."""
    clima = pd.read_csv(os.path.join(PASTA_DADOS, "clima_nasa.csv"),
                        parse_dates=["data"])
    focos = pd.read_csv(os.path.join(PASTA_DADOS, "focos_inpe.csv"),
                        parse_dates=["data"])
    esp = pd.read_csv(os.path.join(PASTA_DADOS, "leituras_esp32.csv"),
                      parse_dates=["timestamp"])
    return clima, focos, esp


# ---------------------------------------------------------------------------
# Figura 1 - Serie temporal de focos (sazonalidade da estacao seca)
# ---------------------------------------------------------------------------
def fig_serie_temporal(focos: pd.DataFrame) -> None:
    serie = focos.set_index("data").resample("ME").size()
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.fill_between(range(len(serie)), serie.values, color=ev.LARANJA, alpha=0.18)
    ax.plot(range(len(serie)), serie.values, color=ev.LARANJA, linewidth=2.6,
            marker="o", markersize=6, markerfacecolor="white",
            markeredgecolor=ev.LARANJA, markeredgewidth=2)
    ax.set_xticks(range(len(serie)))
    ax.set_xticklabels(MESES)
    ax.set_ylabel("Focos detectados")
    # destaca o pico
    i_pico = int(np.argmax(serie.values))
    ax.annotate(f"Pico: {serie.values[i_pico]:,} focos",
                xy=(i_pico, serie.values[i_pico]),
                xytext=(i_pico - 3.2, serie.values[i_pico] * 0.92),
                fontsize=10, fontweight="bold", color=ev.GRAFITE,
                arrowprops=dict(arrowstyle="->", color=ev.CINZA))
    ev.titulo_painel(ax, "Sazonalidade dos focos de calor",
                     "Total mensal de focos detectados por satelite - Brasil 2024")
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "01_serie_temporal_focos.png"))
    plt.close()


# ---------------------------------------------------------------------------
# Figura 2 - Focos por bioma
# ---------------------------------------------------------------------------
def fig_focos_por_bioma(focos: pd.DataFrame) -> None:
    contagem = focos["bioma"].value_counts()
    cores = [ev.CORES_BIOMA.get(b, ev.LARANJA) for b in contagem.index]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    barras = ax.barh(contagem.index[::-1], contagem.values[::-1],
                     color=cores[::-1], edgecolor="white", height=0.7)
    total = contagem.sum()
    for barra, valor in zip(barras, contagem.values[::-1]):
        pct = valor / total * 100
        ax.text(valor + total * 0.01, barra.get_y() + barra.get_height() / 2,
                f"{valor:,} ({pct:.0f}%)", va="center", fontsize=9.5,
                color=ev.GRAFITE, fontweight="bold")
    ax.set_xlim(0, contagem.max() * 1.18)
    ax.set_xlabel("Focos detectados")
    ax.grid(axis="y", visible=False)
    ev.titulo_painel(ax, "Distribuicao de focos por bioma",
                     "Cerrado e Amazonia concentram a maior carga de fogo")
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "02_focos_por_bioma.png"))
    plt.close()


# ---------------------------------------------------------------------------
# Figura 3 - Heatmap de correlacao das variaveis climaticas
# ---------------------------------------------------------------------------
def fig_correlacao(clima: pd.DataFrame) -> None:
    cols = ["t2m", "t2m_max", "rh2m", "prectotcorr", "ws2m",
            "dias_sem_chuva", "vegetacao", "indice_risco"]
    rotulos = ["Temp.\nmedia", "Temp.\nmax", "Umidade", "Chuva", "Vento",
               "Dias s/\nchuva", "Vegetacao", "Indice\nrisco"]
    corr = clima[cols].corr()
    fig, ax = plt.subplots(figsize=(7.8, 6.4))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlBu_r", center=0,
                square=True, linewidths=1.2, linecolor="white",
                cbar_kws={"shrink": 0.8, "label": "Correlacao de Pearson"},
                xticklabels=rotulos, yticklabels=rotulos, ax=ax,
                annot_kws={"fontsize": 9})
    ax.set_title("")
    ax.text(0.0, 1.10, "Correlacao entre variaveis climaticas",
            transform=ax.transAxes, fontsize=15, fontweight="bold",
            color=ev.GRAFITE)
    ax.text(0.0, 1.045, "Base para a selecao de atributos do modelo de IA",
            transform=ax.transAxes, fontsize=10.5, color=ev.CINZA)
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "03_heatmap_correlacao.png"))
    plt.close()


# ---------------------------------------------------------------------------
# Figura 4 - Indice de risco medio por mes e bioma
# ---------------------------------------------------------------------------
def fig_risco_mensal(clima: pd.DataFrame) -> None:
    clima = clima.copy()
    clima["mes"] = clima["data"].dt.month
    pivot = clima.pivot_table(values="indice_risco", index="bioma",
                              columns="mes", aggfunc="mean")
    pivot = pivot.reindex(["Amazonia", "Cerrado", "Pantanal", "Caatinga",
                           "Mata Atlantica", "Pampa"])
    fig, ax = plt.subplots(figsize=(10, 4.4))
    sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt=".0f", linewidths=1,
                linecolor="white", cbar_kws={"label": "Indice de risco (0-100)"},
                xticklabels=MESES, ax=ax, annot_kws={"fontsize": 8})
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title("")
    ax.text(0.0, 1.16, "Indice de risco medio por bioma e mes",
            transform=ax.transAxes, fontsize=15, fontweight="bold",
            color=ev.GRAFITE)
    ax.text(0.0, 1.07, "A janela critica concentra-se entre julho e outubro",
            transform=ax.transAxes, fontsize=10.5, color=ev.CINZA)
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "04_risco_mensal.png"))
    plt.close()


# ---------------------------------------------------------------------------
# Figura 5 - Mapa geografico dos focos (dispersao sobre o Brasil)
# ---------------------------------------------------------------------------
def fig_mapa_focos(focos: pd.DataFrame) -> None:
    # amostra para nao poluir o grafico
    amostra = focos.sample(min(8000, len(focos)), random_state=7)
    fig, ax = plt.subplots(figsize=(7.6, 7.6))
    for bioma in amostra["bioma"].unique():
        sub = amostra[amostra["bioma"] == bioma]
        ax.scatter(sub["longitude"], sub["latitude"], s=6, alpha=0.35,
                   color=ev.CORES_BIOMA.get(bioma, ev.LARANJA), label=bioma,
                   edgecolors="none")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(-74, -33)
    ax.set_ylim(-34, 6)
    ax.set_aspect("equal", adjustable="box")
    leg = ax.legend(loc="lower right", fontsize=8.5, markerscale=2,
                    title="Bioma", title_fontsize=9)
    leg.get_title().set_color(ev.GRAFITE)
    ev.titulo_painel(ax, "Mapa de focos de calor - Brasil",
                     "Cada ponto e uma deteccao orbital (amostra de 8.000 focos)")
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "05_mapa_focos_brasil.png"))
    plt.close()


# ---------------------------------------------------------------------------
# Figura 6 - Leituras de uma estacao ESP32 com evento de fumaca
# ---------------------------------------------------------------------------
def fig_sensores_esp32(esp: pd.DataFrame) -> None:
    est = "ESP32-CER-01"
    sub = esp[esp["estacao_id"] == est].sort_values("timestamp").copy()
    # foca em uma janela de ~12 dias para enxergar os eventos
    sub = sub.iloc[:96]
    t = range(len(sub))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1]})

    ax1.plot(t, sub["temperatura_c"], color=ev.LARANJA, linewidth=2,
             label="Temperatura (C)")
    ax1b = ax1.twinx()
    ax1b.plot(t, sub["umidade_ar_pct"], color=ev.AZUL, linewidth=2,
              label="Umidade do ar (%)")
    ax1.set_ylabel("Temperatura (C)", color=ev.LARANJA)
    ax1b.set_ylabel("Umidade (%)", color=ev.AZUL)
    ax1b.grid(False)
    ax1.text(0.0, 1.22, f"Estacao de borda {est} (Cerrado / Brasilia-DF)",
             transform=ax1.transAxes, fontsize=15, fontweight="bold",
             color=ev.GRAFITE)
    ax1.text(0.0, 1.10, "Telemetria local: clima + sensor de fumaca via MQTT",
             transform=ax1.transAxes, fontsize=10.5, color=ev.CINZA)
    ax1.plot([0.0, 0.06], [1.30, 1.30], transform=ax1.transAxes,
             color=ev.LARANJA, linewidth=3, clip_on=False)

    # fumaca com limiar de alerta
    ax2.fill_between(t, sub["fumaca_ppm"], color=ev.GRAFITE, alpha=0.12)
    ax2.plot(t, sub["fumaca_ppm"], color=ev.GRAFITE, linewidth=1.8,
             label="Fumaca (ppm)")
    ax2.axhline(500, color=ev.LARANJA, linestyle="--", linewidth=1.8)
    ax2.text(len(sub) * 0.01, 520, "Limiar de alerta (500 ppm)",
             color=ev.LARANJA, fontsize=9, fontweight="bold")
    # marca os pontos de alerta
    alertas = sub[sub["fumaca_ppm"] > 500]
    idx_alertas = [list(sub.index).index(i) for i in alertas.index]
    ax2.scatter(idx_alertas, alertas["fumaca_ppm"], color=ev.LARANJA,
                s=55, zorder=5, edgecolor="white", linewidth=1.2)
    ax2.set_ylabel("Fumaca (ppm)")
    ax2.set_xlabel("Leituras sequenciais (a cada 3h)")

    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "06_serie_sensores_esp32.png"))
    plt.close()


def imprimir_estatisticas(clima, focos, esp) -> None:
    """Imprime no console um resumo estatistico usado no PDF/relatorio."""
    print("\n" + "=" * 60)
    print("RESUMO ESTATISTICO (para documentacao)")
    print("=" * 60)
    print(f"Periodo analisado......: {focos['data'].min().date()} a "
          f"{focos['data'].max().date()}")
    print(f"Total de focos.........: {len(focos):,}")
    print(f"FRP medio..............: {focos['frp_mw'].mean():.1f} MW")
    pico_mes = focos.set_index("data").resample("ME").size().idxmax()
    print(f"Mes de pico............: {MESES[pico_mes.month - 1]}/{pico_mes.year}")
    corr = clima[["t2m_max", "rh2m", "dias_sem_chuva", "indice_risco"]].corr()
    print(f"Corr. temp_max x risco.: {corr.loc['t2m_max', 'indice_risco']:.2f}")
    print(f"Corr. umidade x risco..: {corr.loc['rh2m', 'indice_risco']:.2f}")
    print(f"Estacoes ESP32.........: {esp['estacao_id'].nunique()}")
    print(f"Alertas de fumaca......: {(esp['fumaca_ppm'] > 500).sum()} leituras")
    print("=" * 60)


def main() -> None:
    print(">> Carregando bases...")
    clima, focos, esp = carregar_dados()

    print(">> Gerando figuras...")
    fig_serie_temporal(focos)
    fig_focos_por_bioma(focos)
    fig_correlacao(clima)
    fig_risco_mensal(clima)
    fig_mapa_focos(focos)
    fig_sensores_esp32(esp)
    print("   6 figuras salvas em /assets")

    imprimir_estatisticas(clima, focos, esp)


if __name__ == "__main__":
    main()
