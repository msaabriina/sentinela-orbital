# Arquitetura do Sentinela Orbital

Documento técnico que detalha as decisões de projeto, o fluxo de dados e a integração entre as disciplinas.

![Arquitetura](../assets/11_arquitetura.png)

## Visão geral

O sistema é organizado em **quatro estágios** que transformam dados brutos de três fontes em **decisões acionáveis**:

1. **Coleta** — três fontes heterogêneas (orbital, climática, de borda).
2. **Processamento** — ingestão, limpeza e análise com Python/Pandas.
3. **Inteligência** — modelos de Machine Learning.
4. **Decisão & entrega** — fusão, alertas e visualização.

## Camada 1 — Coleta

| Fonte | O que fornece | Módulo | Padrão real |
|---|---|---|---|
| Satélites INPE | Focos de calor (lat, lon, satélite, FRP) | `ingestao_dados.py` | Programa Queimadas/INPE |
| NASA POWER | Clima diário (temp, umidade, chuva, vento) | `ingestao_dados.py` | API NASA POWER |
| Estações ESP32 | Telemetria local + fumaça | `mqtt_receptor.py` | MQTT |

**Decisão de projeto:** a ingestão tenta a API real e faz *fallback* para CSV local. Isso desacopla o desenvolvimento da disponibilidade de rede e torna a POC 100% reproduzível.

## Camada 2 — Processamento

`analise_exploratoria.py` faz a limpeza e a análise: agregações temporais (`resample`), correlações e visualizações. A **matriz de correlação** orienta a seleção de atributos do modelo — evitamos variáveis redundantes e priorizamos as de maior sinal.

**Atributos escolhidos:** `t2m`, `t2m_max`, `rh2m`, `prectotcorr`, `ws2m`, `dias_sem_chuva`, `vegetacao`.

## Camada 3 — Inteligência (ML)

Dois modelos complementares (`modelo_risco.py`):

- **Regressão** (prever a quantidade de focos): comparamos Regressão Linear (baseline) com Random Forest. O ganho de R² de 0,48 → 0,96 mostra que o problema é **não linear** e justifica o modelo mais expressivo.
- **Classificação** (nível de risco): Random Forest com `class_weight="balanced"`, atingindo 91% de acurácia. A matriz de confusão revela que os erros ocorrem apenas entre **classes adjacentes** (ex.: Alto ↔ Crítico) — nunca um erro catastrófico (Baixo previsto como Crítico).

O modelo é persistido em `.joblib` e reutilizado em produção pelo receptor MQTT e pelo dashboard, sem retreinar.

## Camada 4 — Decisão & entrega

### Motor de fusão (`motor_alertas.py`)

Cada bioma recebe um **score de 0 a 100** que pondera:

| Componente | Peso máximo | Fonte |
|---|---|---|
| Focos orbitais (7 dias) | 35 | INPE |
| Intensidade do fogo (FRP) | 10 | INPE |
| Risco previsto pela IA | 40 | Modelo ML |
| Confirmação por sensores | 15 | ESP32 |

O score é traduzido em nível operacional: **VERDE (0–34) → AMARELO (35–59) → LARANJA (60–79) → VERMELHO (80–100)**, cada um com uma ação recomendada.

**Por que fundir?** Satélite sozinho atrasa; sensor sozinho cobre pouca área; IA sozinha é previsão sem confirmação. Juntos, cobrem as fraquezas uns dos outros.

### Dashboard (`dashboard.py`)

Streamlit + Plotly. Destaque para o **previsor interativo**: o usuário ajusta o clima e o modelo responde o nível de risco e as probabilidades em tempo real.

## Persistência

`mqtt_receptor.py` grava toda a telemetria recebida (já classificada pela IA) em **SQLite** (`dados/sentinela.db`, tabela `leituras`), permitindo histórico e auditoria.

## Mapeamento de disciplinas (Fases 3 e 4)

| Disciplina | Onde aparece |
|---|---|
| Lógica de programação | Todo o código (condicionais, laços, funções) |
| Análise de dados (Pandas/NumPy) | `gerar_dados.py`, `analise_exploratoria.py` |
| Estatística | Correlações, distribuições, métricas |
| Machine Learning | `modelo_risco.py` |
| IoT / Edge / ESP32 | `firmware/`, decisão na borda |
| Comunicação (MQTT) | `firmware/`, `mqtt_receptor.py` |
| Banco de dados (SQL) | `mqtt_receptor.py` (SQLite) |
| APIs / Web | `ingestao_dados.py` |
| Visualização & Dashboards | `analise_exploratoria.py`, `dashboard.py` |
| Versionamento (Git) | Estrutura do repositório |
