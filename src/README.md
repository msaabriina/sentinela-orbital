# Código-fonte (`src/`)

Módulos do Sentinela Orbital, na ordem em que se encaixam no pipeline.

| # | Módulo | Papel | Conceitos exercitados |
|---|---|---|---|
| 1 | `gerar_dados.py` | Gera as 3 bases sintéticas (focos INPE, clima NASA, sensores ESP32) modeladas em padrões reais. | Lógica, laços, NumPy, distribuições estatísticas |
| 2 | `estilo_viz.py` | Identidade visual única para todos os gráficos. | Boas práticas, reuso |
| 3 | `analise_exploratoria.py` | Limpeza, agregação e visualização dos dados (EDA). | Pandas, Seaborn, estatística |
| 4 | `modelo_risco.py` | Treina e avalia os modelos de ML; salva `.joblib` e métricas. | Machine Learning, métricas, seleção de modelo |
| 5 | `ingestao_dados.py` | Integração real com APIs INPE e NASA POWER (com fallback). | APIs/Web, JSON, exceções |
| 6 | `mqtt_receptor.py` | Recebe telemetria ESP32 (MQTT ou simulação) e aplica a IA; grava no SQLite. | MQTT, SQL/SQLite, ML em produção |
| 7 | `motor_alertas.py` | Funde as 3 camadas em um score e gera alertas priorizados. | Regras de decisão, automação |
| 8 | `dashboard.py` | Dashboard web interativo com previsor de risco ao vivo. | Visualização, dashboards |
| — | `gerar_preview_dashboard.py` | Gera a imagem do dashboard para a documentação. | Visualização |
| — | `gerar_arquitetura.py` | Gera os diagramas de arquitetura e pipeline. | Visualização |

## Ordem de execução

```bash
python gerar_dados.py
python analise_exploratoria.py
python modelo_risco.py
python mqtt_receptor.py --sim
python motor_alertas.py
streamlit run dashboard.py
```

Cada script é **independente e testável**: pode ser executado isoladamente para inspecionar sua etapa. Os comentários no código são didáticos e explicam as decisões de projeto.
