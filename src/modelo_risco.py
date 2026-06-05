"""
modelo_risco.py
==============================================================================
SENTINELA ORBITAL - Modelos de Machine Learning (nucleo de IA).

Treina e avalia dois modelos complementares a partir do cruzamento entre a
serie climatica (NASA POWER) e a contagem diaria de focos (INPE):

  MODELO 1 - REGRESSAO (principal)
    Objetivo: prever a QUANTIDADE de focos de calor esperada para o dia em um
    bioma, a partir das condicoes climaticas. Como os focos sao gerados por um
    processo de Poisson (com ruido real), a tarefa nao e trivial - exige
    aprendizado de padroes. Comparamos Regressao Linear x Random Forest.

  MODELO 2 - CLASSIFICACAO (apoio operacional)
    Objetivo: classificar o NIVEL de risco (Baixo/Moderado/Alto/Critico) para
    alimentar o motor de alertas e o dashboard. Traduz a previsao continua em
    uma categoria acionavel para bombeiros e gestores.

Saidas:
  - assets/07_importancia_variaveis.png
  - assets/08_matriz_confusao.png
  - assets/09_regressao_pred_vs_real.png
  - modelos/modelo_classificacao.joblib  (modelo treinado, reutilizavel)
  - modelos/metricas.json                (metricas para PDF/dashboard)

Conceitos das Fases 3 e 4 exercitados:
  - Machine Learning introdutorio (regressao e classificacao)
  - Separacao treino/teste, metricas (R2, RMSE, MAE, acuracia, F1)
  - Selecao e comparacao de modelos
  - Importancia de variaveis (feature importance)
  - Persistencia de modelo (joblib)

Uso:
    python modelo_risco.py
==============================================================================
"""

from __future__ import annotations

import json
import os

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, mean_absolute_error,
                             mean_squared_error, r2_score)
from sklearn.model_selection import train_test_split

import estilo_viz as ev

PASTA_DADOS = os.path.join(os.path.dirname(__file__), "..", "dados")
PASTA_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
PASTA_MODELOS = os.path.join(os.path.dirname(__file__), "..", "modelos")
os.makedirs(PASTA_MODELOS, exist_ok=True)

ev.aplicar_estilo()

ATRIBUTOS = ["t2m", "t2m_max", "rh2m", "prectotcorr", "ws2m",
             "dias_sem_chuva", "vegetacao"]
ROTULOS_ATRIBUTOS = {
    "t2m": "Temp. media",
    "t2m_max": "Temp. maxima",
    "rh2m": "Umidade do ar",
    "prectotcorr": "Precipitacao",
    "ws2m": "Vento",
    "dias_sem_chuva": "Dias sem chuva",
    "vegetacao": "Carga de vegetacao",
}
ORDEM_CLASSES = ["Baixo", "Moderado", "Alto", "Critico"]


def montar_dataset() -> pd.DataFrame:
    """Cruza clima (features) com a contagem diaria de focos (alvo de regressao).

    Cada linha representa um par (bioma, dia) com suas condicoes climaticas e
    o numero de focos observado naquele dia/bioma. Dias sem foco recebem 0.
    """
    clima = pd.read_csv(os.path.join(PASTA_DADOS, "clima_nasa.csv"))
    focos = pd.read_csv(os.path.join(PASTA_DADOS, "focos_inpe.csv"))

    contagem = (focos.groupby(["bioma", "data"])
                .size()
                .reset_index(name="n_focos"))

    df = clima.merge(contagem, on=["bioma", "data"], how="left")
    df["n_focos"] = df["n_focos"].fillna(0).astype(int)
    return df


# ---------------------------------------------------------------------------
# MODELO 1 - Regressao
# ---------------------------------------------------------------------------
def treinar_regressao(df: pd.DataFrame) -> dict:
    """Treina e compara Regressao Linear x Random Forest para prever focos."""
    X = df[ATRIBUTOS]
    y = df["n_focos"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42)

    # --- baseline: Regressao Linear (Fase 4) ---
    lin = LinearRegression()
    lin.fit(X_tr, y_tr)
    pred_lin = lin.predict(X_te)
    r2_lin = r2_score(y_te, pred_lin)
    rmse_lin = float(np.sqrt(mean_squared_error(y_te, pred_lin)))

    # --- modelo mais expressivo: Random Forest ---
    rf = RandomForestRegressor(n_estimators=200, max_depth=12,
                               random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    pred_rf = rf.predict(X_te)
    r2_rf = r2_score(y_te, pred_rf)
    rmse_rf = float(np.sqrt(mean_squared_error(y_te, pred_rf)))
    mae_rf = float(mean_absolute_error(y_te, pred_rf))

    print("\n--- MODELO 1: REGRESSAO (prever n. de focos) ---")
    print(f"Regressao Linear : R2 = {r2_lin:.3f} | RMSE = {rmse_lin:.1f}")
    print(f"Random Forest    : R2 = {r2_rf:.3f} | RMSE = {rmse_rf:.1f} | "
          f"MAE = {mae_rf:.1f}")
    print(f"Ganho de R2 (RF vs Linear): +{(r2_rf - r2_lin):.3f}")

    # ---- grafico: previsto vs real (melhor modelo) ----
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    ax.scatter(y_te, pred_rf, s=22, alpha=0.4, color=ev.LARANJA,
               edgecolors="none")
    lim = max(y_te.max(), pred_rf.max()) * 1.05
    ax.plot([0, lim], [0, lim], color=ev.GRAFITE, linestyle="--",
            linewidth=1.6, label="Previsao perfeita")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Focos observados (real)")
    ax.set_ylabel("Focos previstos (modelo)")
    ax.legend(loc="upper left")
    ax.text(0.97, 0.06, f"R2 = {r2_rf:.3f}\nRMSE = {rmse_rf:.1f}",
            transform=ax.transAxes, ha="right", fontsize=11,
            fontweight="bold", color=ev.GRAFITE,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F7F7F9",
                      edgecolor="#D9D9DE"))
    ev.titulo_painel(ax, "Regressao: focos previstos vs observados",
                     "Random Forest Regressor - conjunto de teste (25%)")
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "09_regressao_pred_vs_real.png"))
    plt.close()

    return {
        "linear": {"r2": round(r2_lin, 3), "rmse": round(rmse_lin, 1)},
        "random_forest": {"r2": round(r2_rf, 3), "rmse": round(rmse_rf, 1),
                          "mae": round(mae_rf, 1)},
        "modelo_rf": rf,
    }


# ---------------------------------------------------------------------------
# MODELO 2 - Classificacao
# ---------------------------------------------------------------------------
def treinar_classificacao(df: pd.DataFrame) -> dict:
    """Treina um classificador de nivel de risco a partir do clima.

    O modelo aprende a 'regra operacional' de risco (no espirito da Formula de
    Monte Alegre) diretamente dos dados, sem usar o indice como atributo - so
    as variaveis climaticas observaveis. Isso permite generalizar para novas
    regioes onde a formula manual nao foi calibrada.
    """
    X = df[ATRIBUTOS]
    y = df["classe_risco"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    clf = RandomForestClassifier(n_estimators=200, max_depth=10,
                                 random_state=42, n_jobs=-1,
                                 class_weight="balanced")
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)

    acc = accuracy_score(y_te, pred)
    f1 = f1_score(y_te, pred, average="macro")

    print("\n--- MODELO 2: CLASSIFICACAO (nivel de risco) ---")
    print(f"Acuracia : {acc:.3f}")
    print(f"F1-macro : {f1:.3f}")
    print("\nRelatorio por classe:")
    print(classification_report(y_te, pred, zero_division=0))

    # ---- matriz de confusao ----
    cm = confusion_matrix(y_te, pred, labels=ORDEM_CLASSES)
    fig, ax = plt.subplots(figsize=(6.8, 5.8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Oranges", linewidths=1.2,
                linecolor="white", cbar_kws={"label": "Amostras"},
                xticklabels=ORDEM_CLASSES, yticklabels=ORDEM_CLASSES, ax=ax,
                annot_kws={"fontsize": 11, "fontweight": "bold"})
    ax.set_xlabel("Classe prevista")
    ax.set_ylabel("Classe real")
    ax.set_title("")
    ax.text(0.0, 1.12, "Matriz de confusao - nivel de risco",
            transform=ax.transAxes, fontsize=15, fontweight="bold",
            color=ev.GRAFITE)
    ax.text(0.0, 1.05, f"Acuracia {acc:.1%} | F1-macro {f1:.2f} "
            "(conjunto de teste)",
            transform=ax.transAxes, fontsize=10.5, color=ev.CINZA)
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "08_matriz_confusao.png"))
    plt.close()

    # ---- importancia das variaveis ----
    importancias = pd.Series(clf.feature_importances_, index=ATRIBUTOS)
    importancias = importancias.sort_values()
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    cores = plt.cm.Oranges(np.linspace(0.45, 0.95, len(importancias)))
    ax.barh([ROTULOS_ATRIBUTOS[i] for i in importancias.index],
            importancias.values, color=cores, edgecolor="white")
    for i, (nome, val) in enumerate(importancias.items()):
        ax.text(val + 0.005, i, f"{val:.1%}", va="center", fontsize=9.5,
                fontweight="bold", color=ev.GRAFITE)
    ax.set_xlim(0, importancias.max() * 1.18)
    ax.set_xlabel("Importancia relativa")
    ax.grid(axis="y", visible=False)
    ev.titulo_painel(ax, "O que mais pesa na previsao de risco",
                     "Importancia das variaveis no Random Forest")
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_ASSETS, "07_importancia_variaveis.png"))
    plt.close()

    return {
        "modelo": clf,
        "acuracia": round(float(acc), 3),
        "f1_macro": round(float(f1), 3),
        "importancias": {k: round(float(v), 4)
                         for k, v in zip(ATRIBUTOS, clf.feature_importances_)},
    }


def main() -> None:
    print(">> Montando dataset de treino (clima x focos)...")
    df = montar_dataset()
    print(f"   {len(df):,} registros (pares bioma/dia)")
    print(f"   Atributos: {ATRIBUTOS}")

    res_reg = treinar_regressao(df)
    res_clf = treinar_classificacao(df)

    # ---- persistir modelo e metricas ----
    joblib.dump(res_clf["modelo"],
                os.path.join(PASTA_MODELOS, "modelo_classificacao.joblib"))
    joblib.dump(res_reg["modelo_rf"],
                os.path.join(PASTA_MODELOS, "modelo_regressao.joblib"))

    metricas = {
        "regressao": {
            "linear": res_reg["linear"],
            "random_forest": res_reg["random_forest"],
        },
        "classificacao": {
            "acuracia": res_clf["acuracia"],
            "f1_macro": res_clf["f1_macro"],
            "importancias": res_clf["importancias"],
        },
        "atributos": ATRIBUTOS,
        "n_registros": int(len(df)),
    }
    with open(os.path.join(PASTA_MODELOS, "metricas.json"), "w") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    print("\n>> Modelos salvos em /modelos (.joblib)")
    print(">> Metricas salvas em /modelos/metricas.json")
    print(">> 3 figuras salvas em /assets")


if __name__ == "__main__":
    main()
