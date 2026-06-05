"""
mqtt_receptor.py
==============================================================================
SENTINELA ORBITAL - Receptor de telemetria das estacoes ESP32 (lado servidor).

Recebe via MQTT os pacotes JSON publicados pelas estacoes de borda, aplica o
modelo de IA treinado para classificar o nivel de risco e persiste as leituras
em banco SQLite. Tambem dispara o motor de alertas quando o risco e critico.

DOIS MODOS DE EXECUCAO
----------------------
  1) --mqtt  : conecta a um broker MQTT real e escuta o topico em tempo real
               (requer broker acessivel; usa paho-mqtt).
  2) --sim   : modo SIMULACAO (padrao). Reproduz as leituras do CSV como se
               estivessem chegando do broker - permite testar todo o pipeline
               sem hardware nem rede. Ideal para a banca avaliar a POC.

Conceitos das Fases 3 e 4: protocolo MQTT, banco de dados (SQLite/SQL),
integracao de modelo de ML em producao, manipulacao de dados.

Uso:
    python mqtt_receptor.py --sim         # simulacao (recomendado p/ teste)
    python mqtt_receptor.py --sim --limite 50
    python mqtt_receptor.py --mqtt        # broker real
==============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from datetime import datetime

import joblib
import pandas as pd

PASTA_BASE = os.path.join(os.path.dirname(__file__), "..")
PASTA_DADOS = os.path.join(PASTA_BASE, "dados")
PASTA_MODELOS = os.path.join(PASTA_BASE, "modelos")
CAMINHO_BD = os.path.join(PASTA_DADOS, "sentinela.db")

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORTA = 1883
MQTT_TOPICO = "sentinela/estacoes/telemetria"

# Atributos esperados pelo modelo (mesma ordem do treino)
ATRIBUTOS = ["t2m", "t2m_max", "rh2m", "prectotcorr", "ws2m",
             "dias_sem_chuva", "vegetacao"]


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
def inicializar_bd() -> sqlite3.Connection:
    """Cria (se necessario) a tabela de leituras e retorna a conexao."""
    conn = sqlite3.connect(CAMINHO_BD)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            estacao_id TEXT,
            latitude REAL,
            longitude REAL,
            temperatura_c REAL,
            umidade_ar_pct REAL,
            pressao_hpa REAL,
            umidade_solo_pct REAL,
            fumaca_ppm INTEGER,
            risco_local INTEGER,
            classe_ia TEXT,
            alerta INTEGER
        )
    """)
    conn.commit()
    return conn


def salvar_leitura(conn: sqlite3.Connection, pacote: dict) -> None:
    conn.execute("""
        INSERT INTO leituras (timestamp, estacao_id, latitude, longitude,
            temperatura_c, umidade_ar_pct, pressao_hpa, umidade_solo_pct,
            fumaca_ppm, risco_local, classe_ia, alerta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pacote.get("timestamp", datetime.now().isoformat()),
        pacote["estacao_id"], pacote["latitude"], pacote["longitude"],
        pacote["temperatura_c"], pacote["umidade_ar_pct"],
        pacote.get("pressao_hpa", 1013.0), pacote["umidade_solo_pct"],
        pacote["fumaca_ppm"], pacote.get("risco_local", 0),
        pacote.get("classe_ia", "?"), int(pacote.get("alerta", False)),
    ))
    conn.commit()


# ---------------------------------------------------------------------------
# Modelo de IA
# ---------------------------------------------------------------------------
def carregar_modelo():
    """Carrega o classificador treinado, se existir."""
    caminho = os.path.join(PASTA_MODELOS, "modelo_classificacao.joblib")
    if os.path.exists(caminho):
        return joblib.load(caminho)
    print("AVISO: modelo nao encontrado. Rode modelo_risco.py antes.")
    return None


def classificar_pacote(modelo, pacote: dict) -> str:
    """Estima o nivel de risco a partir da leitura do sensor + clima estimado.

    A estacao mede temperatura, umidade e solo; complementamos com estimativas
    climaticas (vento, chuva, dias sem chuva, vegetacao) para montar o vetor de
    atributos esperado pelo modelo. Numa implantacao real, esses campos viriam
    do casamento com a API NASA POWER para a coordenada da estacao.
    """
    if modelo is None:
        return "?"
    # Estimativas conservadoras a partir da leitura local
    temp = pacote["temperatura_c"]
    umid = pacote["umidade_ar_pct"]
    solo = pacote["umidade_solo_pct"]
    vetor = pd.DataFrame([{
        "t2m": temp,
        "t2m_max": temp + 4,                         # pico ~4C acima da media
        "rh2m": umid,
        "prectotcorr": 0.0 if solo < 20 else 3.0,    # solo seco => sem chuva
        "ws2m": 2.5,
        "dias_sem_chuva": max(0, int((40 - solo) / 4)),
        "vegetacao": 0.70,
    }])[ATRIBUTOS]
    return str(modelo.predict(vetor)[0])


# ---------------------------------------------------------------------------
# Processamento de cada pacote (comum aos dois modos)
# ---------------------------------------------------------------------------
def processar(conn, modelo, pacote: dict, contador: dict) -> None:
    pacote["classe_ia"] = classificar_pacote(modelo, pacote)
    salvar_leitura(conn, pacote)
    contador["total"] += 1

    nivel = pacote["classe_ia"]
    fumaca = pacote["fumaca_ppm"]
    critico = pacote.get("alerta") or nivel in ("Alto", "Critico") \
        or fumaca > 500

    marcador = "  !! ALERTA !!" if critico else ""
    print(f"[{contador['total']:>3}] {pacote['estacao_id']:<14} "
          f"T={pacote['temperatura_c']:.1f}C  "
          f"UR={pacote['umidade_ar_pct']:.0f}%  "
          f"Fumaca={fumaca:>4}ppm  "
          f"IA={nivel:<9}{marcador}")

    if critico:
        contador["alertas"] += 1
        # Em producao: dispara o motor de alertas (e-mail, SMS, webhook).
        # Aqui apenas registramos para nao acoplar dependencias externas.


# ---------------------------------------------------------------------------
# MODO SIMULACAO
# ---------------------------------------------------------------------------
def rodar_simulacao(limite: int | None, intervalo: float) -> None:
    """Reproduz as leituras do CSV como se chegassem do broker MQTT."""
    print("=== MODO SIMULACAO (reproduzindo leituras do CSV) ===\n")
    df = pd.read_csv(os.path.join(PASTA_DADOS, "leituras_esp32.csv"))
    # prioriza eventos interessantes (alta fumaca) misturados com normais
    df = df.sort_values("fumaca_ppm", ascending=False)
    if limite:
        df = df.head(limite)
    df = df.sample(frac=1, random_state=1)  # embaralha a ordem de chegada

    conn = inicializar_bd()
    # limpa execucoes anteriores para nao acumular
    conn.execute("DELETE FROM leituras")
    conn.commit()
    modelo = carregar_modelo()
    contador = {"total": 0, "alertas": 0}

    for _, linha in df.iterrows():
        pacote = {
            "timestamp": linha["timestamp"],
            "estacao_id": linha["estacao_id"],
            "latitude": linha["latitude"],
            "longitude": linha["longitude"],
            "temperatura_c": float(linha["temperatura_c"]),
            "umidade_ar_pct": float(linha["umidade_ar_pct"]),
            "pressao_hpa": float(linha["pressao_hpa"]),
            "umidade_solo_pct": float(linha["umidade_solo_pct"]),
            "fumaca_ppm": int(linha["fumaca_ppm"]),
            "alerta": bool(linha["fumaca_ppm"] > 500),
        }
        processar(conn, modelo, pacote, contador)
        if intervalo > 0:
            time.sleep(intervalo)

    print(f"\nResumo: {contador['total']} leituras processadas, "
          f"{contador['alertas']} alertas disparados.")
    print(f"Dados persistidos em: {os.path.relpath(CAMINHO_BD, PASTA_BASE)}")
    conn.close()


# ---------------------------------------------------------------------------
# MODO MQTT REAL
# ---------------------------------------------------------------------------
def rodar_mqtt() -> None:
    """Conecta a um broker MQTT real e processa pacotes em tempo real."""
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("Instale o paho-mqtt: pip install paho-mqtt")
        return

    print(f"=== MODO MQTT (broker {MQTT_BROKER}) ===\n")
    conn = inicializar_bd()
    modelo = carregar_modelo()
    contador = {"total": 0, "alertas": 0}

    def ao_conectar(client, userdata, flags, rc, *args):
        print(f"Conectado ao broker (rc={rc}). Inscrevendo em {MQTT_TOPICO}")
        client.subscribe(MQTT_TOPICO)

    def ao_receber(client, userdata, msg):
        try:
            pacote = json.loads(msg.payload.decode())
            processar(conn, modelo, pacote, contador)
        except json.JSONDecodeError:
            print("Pacote invalido recebido (nao e JSON).")

    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber
    cliente.connect(MQTT_BROKER, MQTT_PORTA, 60)
    print("Aguardando telemetria... (Ctrl+C para encerrar)")
    cliente.loop_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Receptor de telemetria ESP32")
    parser.add_argument("--mqtt", action="store_true",
                        help="conecta a um broker MQTT real")
    parser.add_argument("--sim", action="store_true",
                        help="modo simulacao (padrao)")
    parser.add_argument("--limite", type=int, default=40,
                        help="n. de leituras na simulacao")
    parser.add_argument("--intervalo", type=float, default=0.0,
                        help="segundos entre leituras na simulacao")
    args = parser.parse_args()

    if args.mqtt:
        rodar_mqtt()
    else:
        rodar_simulacao(args.limite, args.intervalo)


if __name__ == "__main__":
    main()
