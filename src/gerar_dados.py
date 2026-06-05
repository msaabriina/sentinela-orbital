"""
gerar_dados.py
==============================================================================
SENTINELA ORBITAL - Geracao de bases de dados sinteticas realistas.

Este modulo cria tres bases que alimentam todo o pipeline do projeto:

  1) focos_inpe.csv    -> deteccoes de focos de calor por satelite (padrao INPE)
  2) clima_nasa.csv    -> serie climatica diaria por regiao (padrao NASA POWER)
  3) leituras_esp32.csv-> leituras de estacoes de borda com ESP32 + sensores

Os dados sao SINTETICOS, porem modelados a partir de padroes reais das
queimadas brasileiras: sazonalidade (estacao seca de maio a outubro, pico em
agosto/setembro), distribuicao por bioma (Amazonia e Cerrado concentram a
maior parte dos focos) e correlacao fisica entre clima e risco de fogo.

A relacao "clima -> risco -> focos" e construida de forma coerente para que os
modelos de Machine Learning aprendam padroes com significado real, e nao ruido.

Conceitos das Fases 3 e 4 exercitados aqui:
  - Logica de programacao: condicionais, lacos e funcoes
  - Manipulacao de dados com Pandas e NumPy
  - Pensamento estatistico (distribuicoes Normal, Poisson, Uniforme)

Uso:
    python gerar_dados.py
==============================================================================
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Reprodutibilidade: fixar a semente garante que qualquer pessoa que rodar o
# projeto obtenha exatamente os mesmos dados, facilitando a correcao.
# ----------------------------------------------------------------------------
SEMENTE = 42
np.random.seed(SEMENTE)

PASTA_SAIDA = os.path.join(os.path.dirname(__file__), "..", "dados")
os.makedirs(PASTA_SAIDA, exist_ok=True)

# ----------------------------------------------------------------------------
# Caracterizacao dos biomas brasileiros.
# 'peso_focos' aproxima a participacao de cada bioma no total de focos do pais.
# 'lat'/'lon' definem a "caixa" geografica aproximada de cada bioma para
# sortear coordenadas plausiveis dos focos.
# 'umidade_base' e 'temp_base' definem o microclima tipico do bioma.
# ----------------------------------------------------------------------------
BIOMAS = {
    "Amazonia":      dict(peso_focos=0.42, lat=(-9.5, -2.0),  lon=(-70.0, -50.0),
                          umidade_base=78, temp_base=27, vegetacao=0.92),
    "Cerrado":       dict(peso_focos=0.33, lat=(-20.0, -5.0), lon=(-60.0, -42.0),
                          umidade_base=55, temp_base=29, vegetacao=0.70),
    "Pantanal":      dict(peso_focos=0.11, lat=(-21.0, -16.0),lon=(-58.5, -55.0),
                          umidade_base=62, temp_base=30, vegetacao=0.80),
    "Caatinga":      dict(peso_focos=0.07, lat=(-16.0, -3.0), lon=(-44.0, -36.0),
                          umidade_base=45, temp_base=31, vegetacao=0.45),
    "Mata Atlantica":dict(peso_focos=0.05, lat=(-28.0, -7.0), lon=(-50.0, -39.0),
                          umidade_base=72, temp_base=24, vegetacao=0.78),
    "Pampa":         dict(peso_focos=0.02, lat=(-33.5, -29.0),lon=(-57.5, -50.0),
                          umidade_base=75, temp_base=20, vegetacao=0.65),
}

# Satelites efetivamente usados pelo Programa Queimadas do INPE.
SATELITES = ["AQUA_M-T", "TERRA_M-T", "NOAA-20", "NOAA-21", "GOES-16", "METOP-C"]

DATA_INICIO = date(2024, 1, 1)
DATA_FIM = date(2024, 12, 31)


def _fator_sazonal(dia_do_ano: int) -> float:
    """Retorna multiplicador de risco (0.1 a 1.0) conforme a estacao seca.

    Modelamos a estacao seca brasileira (mais critica entre maio e outubro,
    com pico em agosto/setembro, dia ~250 do ano) usando uma curva gaussiana.
    """
    pico = 250  # ~ inicio de setembro
    largura = 70.0
    base = np.exp(-((dia_do_ano - pico) ** 2) / (2 * largura ** 2))
    return float(0.12 + 0.88 * base)


def gerar_clima() -> pd.DataFrame:
    """Gera a serie climatica diaria por bioma (variaveis estilo NASA POWER).

    Variaveis (nomenclatura inspirada na API NASA POWER):
      - t2m         : temperatura media a 2 m (C)
      - t2m_max     : temperatura maxima a 2 m (C)
      - rh2m        : umidade relativa a 2 m (%)
      - prectotcorr : precipitacao diaria corrigida (mm)
      - ws2m        : velocidade do vento a 2 m (m/s)
    """
    registros = []
    dias = (DATA_FIM - DATA_INICIO).days + 1

    for nome_bioma, info in BIOMAS.items():
        dias_sem_chuva = 0
        for i in range(dias):
            dia_atual = DATA_INICIO + timedelta(days=i)
            doy = dia_atual.timetuple().tm_yday
            sazonal = _fator_sazonal(doy)

            # Na seca a umidade cai e a temperatura sobe.
            umidade = info["umidade_base"] - 30 * sazonal + np.random.normal(0, 5)
            umidade = float(np.clip(umidade, 8, 100))

            temp_max = info["temp_base"] + 8 * sazonal + np.random.normal(0, 2)
            temp_media = temp_max - np.random.uniform(4, 8)

            # Probabilidade de chuva cai bastante na estacao seca.
            prob_chuva = 0.55 * (1 - sazonal) + 0.05
            if np.random.random() < prob_chuva:
                precipitacao = float(np.random.exponential(8) * (1 - 0.5 * sazonal))
                dias_sem_chuva = 0
            else:
                precipitacao = 0.0
                dias_sem_chuva += 1

            vento = float(np.clip(np.random.normal(2.5 + sazonal, 1.0), 0.2, 12))

            registros.append({
                "data": dia_atual.isoformat(),
                "bioma": nome_bioma,
                "t2m": round(temp_media, 1),
                "t2m_max": round(temp_max, 1),
                "rh2m": round(umidade, 1),
                "prectotcorr": round(precipitacao, 1),
                "ws2m": round(vento, 1),
                "dias_sem_chuva": dias_sem_chuva,
                "vegetacao": info["vegetacao"],
            })

    df = pd.DataFrame(registros)
    return df


def calcular_indice_risco(linha: pd.Series) -> float:
    """Indice de risco de fogo (0 a 100) a partir das variaveis climaticas.

    Inspirado na logica da Formula de Monte Alegre (FMA) usada no Brasil,
    porem simplificado para fins didaticos. O risco cresce com temperatura,
    seca acumulada e carga de vegetacao, e cai com umidade e chuva recente.
    """
    risco = 0.0
    risco += (linha["t2m_max"] - 20) * 1.8          # calor
    risco += (100 - linha["rh2m"]) * 0.55           # ar seco
    risco += min(linha["dias_sem_chuva"], 30) * 1.6 # seca acumulada
    risco += linha["ws2m"] * 1.2                    # vento espalha fogo
    risco += linha["vegetacao"] * 18                # combustivel disponivel
    risco -= linha["prectotcorr"] * 1.5             # chuva recente reduz risco
    return float(np.clip(risco, 0, 100))


def classificar_risco(indice: float) -> str:
    """Converte o indice numerico em uma categoria operacional."""
    if indice < 30:
        return "Baixo"
    elif indice < 55:
        return "Moderado"
    elif indice < 75:
        return "Alto"
    else:
        return "Critico"


def gerar_focos(df_clima: pd.DataFrame) -> pd.DataFrame:
    """Gera deteccoes de focos de calor coerentes com o risco climatico.

    O numero de focos por bioma/dia e sorteado de uma distribuicao de Poisson
    cujo lambda cresce com o indice de risco e com o peso historico do bioma.
    Assim, dias secos e quentes em biomas criticos concentram mais focos -
    exatamente o que se observa nos dados reais do INPE.
    """
    registros = []

    for _, linha in df_clima.iterrows():
        info = BIOMAS[linha["bioma"]]
        indice = calcular_indice_risco(linha)

        # lambda do Poisson: combina risco do dia e peso do bioma.
        lam = (indice / 100.0) ** 2.2 * 60 * info["peso_focos"] * 6
        n_focos = np.random.poisson(lam)

        for _ in range(int(n_focos)):
            lat = np.random.uniform(*info["lat"])
            lon = np.random.uniform(*info["lon"])
            # FRP (Fire Radiative Power) maior em focos mais intensos.
            frp = float(np.random.exponential(25) * (0.5 + indice / 100))
            confianca = float(np.clip(np.random.normal(78, 12), 30, 100))
            registros.append({
                "data": linha["data"],
                "bioma": linha["bioma"],
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "satelite": np.random.choice(SATELITES),
                "frp_mw": round(frp, 1),
                "confianca_pct": round(confianca, 0),
                "indice_risco": round(indice, 1),
            })

    df = pd.DataFrame(registros)
    df = df.sort_values("data").reset_index(drop=True)
    return df


def gerar_leituras_esp32(df_clima: pd.DataFrame) -> pd.DataFrame:
    """Simula leituras das estacoes de borda (ESP32 + sensores).

    Cada estacao fica instalada em um bioma critico e mede, a cada 30 min,
    variaveis locais. Quando ha foco de calor proximo, a fumaca (proxy do
    sensor de gas) e a temperatura local sobem - acionando o alerta na borda.

    Sensores simulados:
      - DHT22 / BME280 : temperatura, umidade do ar, pressao
      - MQ-135 / MQ-2  : concentracao de fumaca/gas (ppm)
      - sensor capacitivo: umidade do solo (%)
      - LDR / UV        : indice ultravioleta
    """
    # 4 estacoes instaladas em pontos criticos
    estacoes = [
        dict(id="ESP32-CER-01", bioma="Cerrado",  lat=-15.78, lon=-47.93),
        dict(id="ESP32-AMZ-02", bioma="Amazonia", lat=-3.10,  lon=-60.02),
        dict(id="ESP32-PAN-03", bioma="Pantanal", lat=-19.00, lon=-57.65),
        dict(id="ESP32-CAA-04", bioma="Caatinga", lat=-9.40,  lon=-40.50),
    ]

    # indexa clima por (bioma, data) para consulta rapida
    clima_idx = df_clima.set_index(["bioma", "data"]).sort_index()

    registros = []
    # Amostra 45 dias dentro da estacao seca (mais relevante para sensores)
    datas_seca = [
        (DATA_INICIO + timedelta(days=d)).isoformat()
        for d in range(200, 290)  # ~ jul a set
    ]

    for est in estacoes:
        for data_str in datas_seca:
            try:
                clima_dia = clima_idx.loc[(est["bioma"], data_str)]
            except KeyError:
                continue

            indice = calcular_indice_risco(clima_dia)
            # 8 leituras por dia (a cada 3h) para manter o CSV enxuto
            for hora in range(0, 24, 3):
                # variacao diurna da temperatura
                fator_hora = np.sin((hora - 6) / 24 * 2 * np.pi)
                temp = clima_dia["t2m"] + 5 * fator_hora + np.random.normal(0, 1)
                umid_ar = float(np.clip(
                    clima_dia["rh2m"] - 5 * fator_hora + np.random.normal(0, 3),
                    5, 100))
                pressao = float(np.random.normal(1013, 4))
                umid_solo = float(np.clip(
                    clima_dia["rh2m"] * 0.6 - clima_dia["dias_sem_chuva"] * 0.8
                    + np.random.normal(0, 4), 2, 90))

                # fumaca: base baixa, mas dispara quando o risco e alto
                fumaca_base = np.random.normal(40, 10)
                if indice > 70 and np.random.random() < 0.25:
                    fumaca = fumaca_base + np.random.uniform(300, 900)  # evento!
                else:
                    fumaca = fumaca_base + indice * 1.5
                fumaca = float(np.clip(fumaca, 10, 1500))

                uv = float(np.clip(
                    8 * max(fator_hora, 0) + np.random.normal(0, 1), 0, 13))

                registros.append({
                    "timestamp": f"{data_str}T{hora:02d}:00:00",
                    "estacao_id": est["id"],
                    "bioma": est["bioma"],
                    "latitude": est["lat"],
                    "longitude": est["lon"],
                    "temperatura_c": round(temp, 1),
                    "umidade_ar_pct": round(umid_ar, 1),
                    "pressao_hpa": round(pressao, 1),
                    "umidade_solo_pct": round(umid_solo, 1),
                    "fumaca_ppm": round(fumaca, 0),
                    "indice_uv": round(uv, 1),
                })

    df = pd.DataFrame(registros)
    return df


def main() -> None:
    print(">> Gerando base climatica (NASA POWER - sintetica)...")
    df_clima = gerar_clima()
    # anexa indice e classe de risco ao clima (uteis para ML e dashboard)
    df_clima["indice_risco"] = df_clima.apply(calcular_indice_risco, axis=1).round(1)
    df_clima["classe_risco"] = df_clima["indice_risco"].apply(classificar_risco)
    caminho_clima = os.path.join(PASTA_SAIDA, "clima_nasa.csv")
    df_clima.to_csv(caminho_clima, index=False)
    print(f"   {len(df_clima):,} registros -> {os.path.basename(caminho_clima)}")

    print(">> Gerando focos de calor (INPE - sintetico)...")
    df_focos = gerar_focos(df_clima)
    caminho_focos = os.path.join(PASTA_SAIDA, "focos_inpe.csv")
    df_focos.to_csv(caminho_focos, index=False)
    print(f"   {len(df_focos):,} focos -> {os.path.basename(caminho_focos)}")

    print(">> Gerando leituras das estacoes ESP32...")
    df_esp = gerar_leituras_esp32(df_clima)
    caminho_esp = os.path.join(PASTA_SAIDA, "leituras_esp32.csv")
    df_esp.to_csv(caminho_esp, index=False)
    print(f"   {len(df_esp):,} leituras -> {os.path.basename(caminho_esp)}")

    print("\n>> Resumo por bioma (focos detectados):")
    resumo = (df_focos.groupby("bioma")
              .size()
              .sort_values(ascending=False))
    for bioma, qtd in resumo.items():
        print(f"   {bioma:<16} {qtd:>6,} focos")

    print("\nConcluido. Bases salvas em /dados.")


if __name__ == "__main__":
    main()
