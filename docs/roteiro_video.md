# Roteiro do Vídeo Demonstrativo — Sentinela Orbital

> **Duração-alvo:** 4min30 – 5min00 (limite de 5 minutos).
> **Plataforma:** YouTube configurado como **NÃO LISTADO**.
> **Dica:** grave a tela (dashboard + código rodando) com narração; mostre o time no início.

---

## Checklist de obrigatoriedades (não esqueça!)

- [ ] Dizer **"QUERO CONCORRER"** nos primeiros segundos.
- [ ] Apresentar o **nome do grupo** e dos integrantes logo no início.
- [ ] Mostrar o **sistema funcionando** (não só slides).
- [ ] Evidenciar a **integração de disciplinas** (dados, IA, IoT/ESP32, dashboard).
- [ ] Manter abaixo de **5 minutos**.

---

## Bloco 1 — Abertura (0:00 – 0:25)

**Tela:** capa do projeto (logo "Sentinela Orbital") com os nomes do grupo.

**Narração (sugestão):**
> "Olá! Nós somos o grupo **[NOME DO GRUPO]** — [Integrante 1], [Integrante 2], [Integrante 3] e [Integrante 4]. E **nós queremos concorrer**. Este é o **Sentinela Orbital**, nossa solução para a Global Solution 2026.1."

---

## Bloco 2 — O problema (0:25 – 1:00)

**Tela:** gráfico `01_serie_temporal_focos.png` (a curva da estação seca) e o mapa `05_mapa_focos_brasil.png`.

**Narração:**
> "Todo ano o Brasil queima — centenas de milhares de focos, concentrados entre julho e outubro, na Amazônia e no Cerrado. Os satélites do INPE enxergam o fogo, mas enxergam o fogo que **já começou**. Nossa pergunta foi: e se a gente pudesse **prever o risco antes** e **confirmar o foco no chão, em minutos**?"

---

## Bloco 3 — A arquitetura (1:00 – 1:40)

**Tela:** diagrama `11_arquitetura.png`.

**Narração:**
> "O Sentinela une **três camadas**. A **orbital**, com focos do INPE e clima da NASA. A de **inteligência**, com modelos de Machine Learning. E a de **borda**, com estações **ESP32** que medem o ambiente e decidem o alerta na própria placa. Um motor de fusão junta tudo num único score de risco por bioma."

---

## Bloco 4 — Dados e IA rodando (1:40 – 2:55)

**Tela:** terminal executando, em sequência:
1. `python gerar_dados.py` (mostra os volumes: 64 mil focos etc.)
2. `python modelo_risco.py` (mostra as métricas saindo no console)

**Narração:**
> "Aqui o sistema gera as bases e treina a IA. Repare no resultado: uma regressão linear simples explica só 48% da variação dos focos. Trocando por um **Random Forest**, saltamos para **96%**. E o classificador de nível de risco atinge **91% de acurácia**. Melhor: as variáveis que mais pesam — temperatura, chuva, umidade — são exatamente as que a ciência do fogo aponta. O modelo é preciso **e** interpretável."

**Tela:** mostrar `08_matriz_confusao.png` e `07_importancia_variaveis.png` rapidamente.

---

## Bloco 5 — A camada de borda (ESP32) (2:55 – 3:35)

**Tela:** trecho do `firmware/sentinela_esp32.ino` (a função de decisão na borda) e, em seguida, `python mqtt_receptor.py --sim` rodando.

**Narração:**
> "No chão, a estação ESP32 lê temperatura, umidade e fumaça. Se a fumaça passa de 500 ppm, ela aciona o alarme **na hora, mesmo sem internet** — isso é edge computing. Quando há rede, ela publica a telemetria por **MQTT**. No servidor, cada pacote passa pelo modelo de IA e é gravado no banco. Veja os alertas sendo disparados em tempo real."

---

## Bloco 6 — Dashboard e fusão (3:35 – 4:30)

**Tela:** `streamlit run dashboard.py` — navegue pelo mapa, mexa nos **sliders do previsor de risco** e mostre a previsão mudando ao vivo. Depois rode `python motor_alertas.py`.

**Narração:**
> "Tudo isso vira decisão neste dashboard. Aqui posso simular uma condição climática e a IA me diz o risco na hora. E o motor de alertas cruza as três camadas e prioriza: hoje, Amazônia e Cerrado em **vermelho**. É a informação certa, no lugar certo, para quem precisa apagar o fogo."

---

## Bloco 7 — Fechamento (4:30 – 4:55)

**Tela:** volta para a capa com os nomes + link do repositório.

**Narração:**
> "Sentinela Orbital: tecnologia espacial, inteligência artificial e sensores trabalhando juntos para proteger nossos biomas. Obrigado — e **queremos concorrer**!"

---

## Dicas de gravação

- Use **OBS Studio** (grátis) para capturar tela + voz.
- Deixe os scripts **já testados** antes de gravar (evita travar no vídeo).
- Se algo demorar (treino do modelo), **corte/acelere** na edição.
- Exporte em 1080p e suba no YouTube como **Não listado**; cole o link no PDF e no README.
