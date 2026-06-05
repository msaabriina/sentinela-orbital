"""
estilo_viz.py
==============================================================================
SENTINELA ORBITAL - Identidade visual compartilhada para todos os graficos.

Centralizar a paleta e os ajustes do Matplotlib em um unico modulo garante
consistencia visual entre todas as figuras do projeto (principio de design
"single source of truth") e mantem o codigo dos modulos de analise limpo.

Paleta inspirada na identidade "SPACE CONNECT" da Global Solution 2026.1.
==============================================================================
"""

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paleta da marca
# ---------------------------------------------------------------------------
LARANJA = "#E8501F"        # acento primario (marca)
LARANJA_CLARO = "#F5A623"  # acento secundario
AZUL = "#2E5E8C"           # apoio frio
TEAL = "#1F9E8E"           # contraste
GRAFITE = "#26262E"        # texto / elementos escuros
CINZA = "#8A8A95"          # texto secundario
FUNDO = "#FFFFFF"

# Escala de severidade de risco (Baixo -> Critico)
CORES_RISCO = {
    "Baixo": "#2E8B57",
    "Moderado": "#F5A623",
    "Alto": "#E8501F",
    "Critico": "#9B1B1B",
}

# Cores por bioma (consistentes em todo o projeto)
CORES_BIOMA = {
    "Amazonia": "#1F9E8E",
    "Cerrado": "#E8501F",
    "Pantanal": "#2E5E8C",
    "Caatinga": "#F5A623",
    "Mata Atlantica": "#2E8B57",
    "Pampa": "#9B59B6",
}

PALETA_SEQ = [LARANJA, AZUL, TEAL, LARANJA_CLARO, "#9B59B6", "#2E8B57"]


def aplicar_estilo() -> None:
    """Aplica o tema visual padrao do projeto ao Matplotlib."""
    mpl.rcParams.update({
        "figure.facecolor": FUNDO,
        "axes.facecolor": FUNDO,
        "savefig.facecolor": FUNDO,
        "axes.edgecolor": "#D9D9DE",
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "grid.color": "#ECECF0",
        "grid.linewidth": 0.9,
        "axes.axisbelow": True,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlecolor": GRAFITE,
        "axes.labelcolor": GRAFITE,
        "axes.labelsize": 11,
        "xtick.color": CINZA,
        "ytick.color": CINZA,
        "text.color": GRAFITE,
        "font.size": 10.5,
        "font.family": "DejaVu Sans",
        "legend.frameon": False,
        "figure.dpi": 120,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def titulo_painel(ax, titulo: str, subtitulo: str = "") -> None:
    """Aplica um titulo com a 'pegada' editorial da marca (barra laranja)."""
    ax.set_title("")
    ax.text(0.0, 1.14, titulo, transform=ax.transAxes,
            fontsize=15, fontweight="bold", color=GRAFITE, va="top")
    if subtitulo:
        ax.text(0.0, 1.065, subtitulo, transform=ax.transAxes,
                fontsize=10.5, color=CINZA, va="top")
    # barra de acento
    ax.plot([0.0, 0.06], [1.18, 1.18], transform=ax.transAxes,
            color=LARANJA, linewidth=3, solid_capstyle="round", clip_on=False)
