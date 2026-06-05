"""
ingestao_dados.py
==============================================================================
SENTINELA ORBITAL - Ingestao de dados de fontes oficiais (camada orbital).

Demonstra como o sistema se conecta as APIs PUBLICAS e REAIS que alimentam a
camada orbital. As funcoes constroem as requisicoes corretas para:

  - INPE / Programa Queimadas  -> focos de calor por satelite
  - NASA POWER                 -> variaveis climaticas por coordenada

Como esta POC e executada em ambiente sem acesso externo a essas APIs, cada
funcao tenta a chamada real e, em caso de indisponibilidade de rede, faz
FALLBACK automatico para as bases locais (geradas por gerar_dados.py). Assim o
pipeline e identico ao de producao - basta haver internet para usar os dados
ao vivo.

Endpoints reais (documentacao):
  INPE: https://terrabrasilis.dpi.inpe.br/queimadas/portal/  (Programa Queimadas)
        Dados abertos de focos: https://dataserver-coids.inpe.br/queimadas/
  NASA: https://power.larc.nasa.gov/docs/services/api/  (POWER API)

Conceitos das Fases 3 e 4: consumo de APIs/Web, JSON, tratamento de excecoes,
manipulacao de dados com Pandas, integracao de fontes heterogeneas.

Uso:
    python ingestao_dados.py
==============================================================================
"""

from __future__ import annotations

import io
import os
from datetime import date

import pandas as pd

try:
    import requests
    TEM_REQUESTS = True
except ImportError:
    TEM_REQUESTS = False

PASTA_DADOS = os.path.join(os.path.dirname(__file__), "..", "dados")

# Endpoints reais
URL_NASA_POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
URL_INPE_FOCOS = ("https://dataserver-coids.inpe.br/queimadas/queimadas/"
                  "focos/csv/diario")

TIMEOUT = 8  # segundos


# ---------------------------------------------------------------------------
# NASA POWER - dados climaticos diarios por coordenada
# ---------------------------------------------------------------------------
def buscar_clima_nasa(lat: float, lon: float,
                      inicio: date, fim: date) -> pd.DataFrame:
    """Busca dados climaticos diarios na API NASA POWER para um ponto.

    Parametros (na nomenclatura da API):
      T2M         -> temperatura media a 2 m
      T2M_MAX     -> temperatura maxima a 2 m
      RH2M        -> umidade relativa a 2 m
      PRECTOTCORR -> precipitacao corrigida
      WS2M        -> vento a 2 m

    Retorna um DataFrame; em caso de falha de rede, retorna DataFrame vazio
    (o chamador entao usa o fallback local).
    """
    if not TEM_REQUESTS:
        return pd.DataFrame()

    params = {
        "parameters": "T2M,T2M_MAX,RH2M,PRECTOTCORR,WS2M",
        "community": "AG",                     # comunidade Agroclimatology
        "longitude": lon,
        "latitude": lat,
        "start": inicio.strftime("%Y%m%d"),
        "end": fim.strftime("%Y%m%d"),
        "format": "JSON",
    }
    try:
        resp = requests.get(URL_NASA_POWER, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        bruto = resp.json()["properties"]["parameter"]
        df = pd.DataFrame(bruto)
        df.index.name = "data"
        df = df.reset_index().rename(columns={
            "T2M": "t2m", "T2M_MAX": "t2m_max", "RH2M": "rh2m",
            "PRECTOTCORR": "prectotcorr", "WS2M": "ws2m",
        })
        print(f"  [NASA POWER] {len(df)} dias obtidos para "
              f"({lat:.2f}, {lon:.2f}).")
        return df
    except Exception as e:
        print(f"  [NASA POWER] indisponivel ({type(e).__name__}). "
              "Usando fallback local.")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# INPE - focos de calor
# ---------------------------------------------------------------------------
def buscar_focos_inpe(dia: date) -> pd.DataFrame:
    """Busca o CSV diario de focos do Programa Queimadas (INPE).

    O INPE disponibiliza arquivos diarios em formato CSV. Aqui montamos a URL
    do dia e tentamos baixar; em caso de falha, retornamos DataFrame vazio.
    """
    if not TEM_REQUESTS:
        return pd.DataFrame()

    nome = f"focos_diario_br_{dia.strftime('%Y%m%d')}.csv"
    url = f"{URL_INPE_FOCOS}/{nome}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        print(f"  [INPE] {len(df)} focos obtidos para {dia}.")
        return df
    except Exception as e:
        print(f"  [INPE] indisponivel ({type(e).__name__}). "
              "Usando fallback local.")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Camada de acesso unificada (com fallback)
# ---------------------------------------------------------------------------
def carregar_clima(usar_api: bool = True) -> pd.DataFrame:
    """Retorna a base climatica, preferindo a API e caindo para o CSV local."""
    if usar_api:
        # Exemplo: Brasilia-DF (representando o Cerrado)
        df_api = buscar_clima_nasa(-15.78, -47.93,
                                   date(2024, 1, 1), date(2024, 12, 31))
        if not df_api.empty:
            return df_api
    caminho = os.path.join(PASTA_DADOS, "clima_nasa.csv")
    return pd.read_csv(caminho)


def carregar_focos(usar_api: bool = True) -> pd.DataFrame:
    """Retorna a base de focos, preferindo a API e caindo para o CSV local."""
    if usar_api:
        df_api = buscar_focos_inpe(date(2024, 9, 15))
        if not df_api.empty:
            return df_api
    caminho = os.path.join(PASTA_DADOS, "focos_inpe.csv")
    return pd.read_csv(caminho)


def main() -> None:
    print(">> Testando ingestao das fontes oficiais (com fallback)...\n")
    if not TEM_REQUESTS:
        print("  (biblioteca 'requests' ausente; apenas fallback local)\n")

    clima = carregar_clima(usar_api=True)
    focos = carregar_focos(usar_api=True)

    print(f"\n>> Clima carregado : {len(clima):,} registros")
    print(f">> Focos carregados: {len(focos):,} registros")
    print("\nPipeline de ingestao pronto. Em producao, com internet, os dados "
          "vem ao vivo do INPE e da NASA; sem internet, da base local.")


if __name__ == "__main__":
    main()
