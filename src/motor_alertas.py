"""
motor_alertas.py
==============================================================================
SENTINELA ORBITAL - Motor de Fusao e Alertas (camada de decisao).

E o "cerebro" do sistema. Funde as TRES camadas de informacao e decide, de
forma autonoma, quais regioes do Brasil precisam de atencao imediata:

   CAMADA ORBITAL  (focos INPE)         --\
   CAMADA CLIMATICA + IA (risco previsto) --> FUSAO --> ALERTAS PRIORIZADOS
   CAMADA DE BORDA (sensores ESP32)     --/

Logica de fusao (regras de negocio):
  - Cada bioma recebe um "score" combinando focos recentes, risco do modelo de
    IA e leituras criticas das estacoes de borda.
  - O score define o nivel do alerta (VERDE / AMARELO / LARANJA / VERMELHO).
  - Alertas VERMELHOS geram acao recomendada (acionar brigada, etc.).

Demonstra fortemente os conceitos das Fases 3 e 4:
  - Logica de programacao: condicionais, lacos, funcoes
  - Manipulacao de dados com Pandas
  - Sistemas autonomos / automacao inspirada em missoes espaciais
  - Integracao de um modelo de ML em uma regra de decisao

Uso:
    python motor_alertas.py
==============================================================================
"""

from __future__ import annotations

import os
from datetime import timedelta

import joblib
import pandas as pd

PASTA_BASE = os.path.join(os.path.dirname(__file__), "..")
PASTA_DADOS = os.path.join(PASTA_BASE, "dados")
PASTA_MODELOS = os.path.join(PASTA_BASE, "modelos")

ATRIBUTOS = ["t2m", "t2m_max", "rh2m", "prectotcorr", "ws2m",
             "dias_sem_chuva", "vegetacao"]

# Niveis de alerta (cor, faixa de score e acao recomendada)
NIVEIS = [
    ("VERMELHO", 80, "Acionar brigada de incendio e emitir aviso a populacao."),
    ("LARANJA",  60, "Mobilizar equipes e intensificar o monitoramento."),
    ("AMARELO",  35, "Atencao elevada; reforcar vigilancia por satelite."),
    ("VERDE",     0, "Situacao sob controle; monitoramento de rotina."),
]


def classificar_nivel(score: float) -> tuple[str, str]:
    """Mapeia um score (0-100) para (nivel, acao recomendada)."""
    for nome, limiar, acao in NIVEIS:
        if score >= limiar:
            return nome, acao
    return "VERDE", NIVEIS[-1][2]


def carregar_camadas():
    """Carrega as bases das tres camadas e o modelo de IA."""
    focos = pd.read_csv(os.path.join(PASTA_DADOS, "focos_inpe.csv"),
                        parse_dates=["data"])
    clima = pd.read_csv(os.path.join(PASTA_DADOS, "clima_nasa.csv"),
                        parse_dates=["data"])
    esp = pd.read_csv(os.path.join(PASTA_DADOS, "leituras_esp32.csv"),
                      parse_dates=["timestamp"])
    caminho_modelo = os.path.join(PASTA_MODELOS, "modelo_classificacao.joblib")
    modelo = joblib.load(caminho_modelo) if os.path.exists(caminho_modelo) else None
    return focos, clima, esp, modelo


def gerar_alertas(data_referencia=None):
    """Gera o painel de alertas por bioma para uma data de referencia.

    Se nenhuma data for informada, usa a data de maior atividade do periodo
    (tipicamente no pico da estacao seca) para demonstracao.
    """
    focos, clima, esp, modelo = carregar_camadas()

    if data_referencia is None:
        # data com mais focos (mais interessante para demonstrar)
        data_referencia = (focos.groupby("data").size().idxmax())
    janela_inicio = data_referencia - timedelta(days=7)

    print("=" * 70)
    print("  SENTINELA ORBITAL - PAINEL DE ALERTAS")
    print(f"  Data de referencia: {data_referencia.date()}  "
          f"(janela movel de 7 dias)")
    print("=" * 70)

    # ---- mapeia score de IA por classe ----
    score_classe = {"Baixo": 15, "Moderado": 45, "Alto": 70, "Critico": 92}

    alertas = []
    biomas = ["Amazonia", "Cerrado", "Pantanal", "Caatinga",
              "Mata Atlantica", "Pampa"]

    for bioma in biomas:
        # --- CAMADA 1: focos orbitais recentes (ultimos 7 dias) ---
        focos_recentes = focos[
            (focos["bioma"] == bioma)
            & (focos["data"] >= janela_inicio)
            & (focos["data"] <= data_referencia)
        ]
        n_focos = len(focos_recentes)
        frp_medio = focos_recentes["frp_mw"].mean() if n_focos else 0.0

        # --- CAMADA 2: risco previsto pela IA para a data ---
        clima_dia = clima[
            (clima["bioma"] == bioma) & (clima["data"] == data_referencia)
        ]
        if not clima_dia.empty and modelo is not None:
            vetor = clima_dia[ATRIBUTOS]
            classe_ia = str(modelo.predict(vetor)[0])
        elif not clima_dia.empty:
            classe_ia = str(clima_dia.iloc[0]["classe_risco"])
        else:
            classe_ia = "Baixo"

        # --- CAMADA 3: sensores de borda no bioma (janela) ---
        sensores = esp[
            (esp["bioma"] == bioma)
            & (esp["timestamp"] >= janela_inicio)
            & (esp["timestamp"] <= data_referencia + timedelta(days=1))
        ]
        leituras_criticas = int((sensores["fumaca_ppm"] > 500).sum())
        tem_estacao = len(sensores) > 0

        # --- FUSAO: combina as tres camadas em um score 0-100 ---
        score = 0.0
        # foco orbital: ate 35 pts (saturando em ~300 focos/semana)
        score += min(n_focos / 300.0, 1.0) * 35
        # intensidade do fogo (FRP): ate 10 pts
        score += min(frp_medio / 60.0, 1.0) * 10
        # risco da IA: ate 40 pts
        score += score_classe.get(classe_ia, 15) / 92.0 * 40
        # sensores de borda: ate 15 pts (sinal de confirmacao no chao)
        if tem_estacao:
            score += min(leituras_criticas / 10.0, 1.0) * 15

        score = round(min(score, 100.0), 1)
        nivel, acao = classificar_nivel(score)

        alertas.append({
            "bioma": bioma,
            "nivel": nivel,
            "score": score,
            "focos_7d": n_focos,
            "frp_medio": round(frp_medio, 1),
            "ia_risco": classe_ia,
            "sensores_criticos": leituras_criticas if tem_estacao else None,
            "acao": acao,
        })

    df_alertas = pd.DataFrame(alertas).sort_values("score", ascending=False)

    # ---- impressao formatada do painel ----
    icones = {"VERMELHO": "[!!!]", "LARANJA": "[!! ]",
              "AMARELO": "[!  ]", "VERDE": "[ ok]"}
    for _, a in df_alertas.iterrows():
        sens = ("sem estacao" if pd.isna(a["sensores_criticos"])
                else f"{int(a['sensores_criticos'])} criticas")
        print(f"\n{icones[a['nivel']]} {a['bioma']:<15} "
              f"NIVEL {a['nivel']:<9} (score {a['score']:>5})")
        print(f"      Focos (7d): {a['focos_7d']:<5} | "
              f"FRP medio: {a['frp_medio']:>5} MW | "
              f"IA: {a['ia_risco']:<9} | Sensores: {sens}")
        if a["nivel"] in ("VERMELHO", "LARANJA"):
            print(f"      ACAO: {a['acao']}")

    # ---- resumo ----
    vermelhos = (df_alertas["nivel"] == "VERMELHO").sum()
    laranjas = (df_alertas["nivel"] == "LARANJA").sum()
    print("\n" + "=" * 70)
    print(f"  RESUMO: {vermelhos} alerta(s) VERMELHO, {laranjas} LARANJA. "
          f"Prioridade maxima: {df_alertas.iloc[0]['bioma']}.")
    print("=" * 70)

    return df_alertas


if __name__ == "__main__":
    gerar_alertas()
