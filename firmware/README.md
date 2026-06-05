# Firmware — Estação de Borda ESP32

Esta pasta contém o firmware das **estações de borda** do Sentinela Orbital: os "olhos no chão" que detectam o início de uma queimada localmente, em minutos, e publicam a telemetria para o servidor via MQTT.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `sentinela_esp32.ino` | Firmware principal em **Arduino C++** (recomendado). |
| `sentinela_esp32_micropython.py` | Versão alternativa em **MicroPython**. |

## Hardware necessário

- 1× **ESP32** (DevKit v1 ou equivalente)
- 1× sensor **BME280** (temperatura, umidade do ar, pressão — I2C)
- 1× sensor de gás/fumaça **MQ-135** (ou MQ-2) — saída analógica
- 1× sensor de **umidade do solo** capacitivo — saída analógica
- 1× **LED** (alerta visual) + 1× **buzzer** (alerta sonoro)
- Protoboard, jumpers e resistor de 220Ω para o LED

## Pinagem (wiring)

```
            ┌─────────────── ESP32 ───────────────┐
  BME280    │                                      │
   VCC ─────┤ 3V3                              GPIO2├──── LED (+ resistor 220Ω) ── GND
   GND ─────┤ GND                              GPIO4├──── Buzzer ── GND
   SDA ─────┤ GPIO21 (SDA)                          │
   SCL ─────┤ GPIO22 (SCL)                          │
            │                              GPIO34   ├──── MQ-135 (AOUT)
            │                              GPIO35   ├──── Umidade do solo (AOUT)
            └──────────────────────────────────────┘
```

> Os pinos **GPIO34** e **GPIO35** são entradas analógicas (ADC1), ideais para sensores analógicos e compatíveis com o uso simultâneo do Wi‑Fi.

## Bibliotecas (Arduino IDE → Library Manager)

- **Adafruit BME280 Library**
- **Adafruit Unified Sensor**
- **PubSubClient** (cliente MQTT)
- **ArduinoJson**

## Configuração antes de gravar

No início do `.ino`, ajuste:

```cpp
const char* WIFI_SSID  = "SUA_REDE_WIFI";
const char* WIFI_SENHA = "SUA_SENHA_WIFI";
const char* ESTACAO_ID = "ESP32-CER-01";   // identificador único da estação
```

O broker MQTT padrão é o público `broker.hivemq.com` (ótimo para POC). Em produção, troque por um broker próprio (ex.: Mosquitto).

## Decisão na borda (edge computing)

O grande diferencial: a estação **não depende da nuvem** para soar o alarme. Ela calcula um índice de risco local e, se a fumaça ultrapassar `500 ppm` **ou** o risco ultrapassar `75/100`, aciona LED + buzzer **imediatamente** — mesmo sem internet. A telemetria é enviada em paralelo, quando há conexão, para alimentar a IA e o dashboard.

## Tópico MQTT

As estações publicam JSON no tópico:

```
sentinela/estacoes/telemetria
```

Exemplo de payload:

```json
{
  "estacao_id": "ESP32-CER-01",
  "latitude": -15.78,
  "longitude": -47.93,
  "temperatura_c": 34.2,
  "umidade_ar_pct": 21.0,
  "pressao_hpa": 1012.4,
  "umidade_solo_pct": 8.5,
  "fumaca_ppm": 640,
  "risco_local": 82,
  "alerta": true
}
```

No servidor, `src/mqtt_receptor.py` recebe esses pacotes, aplica o modelo de IA e grava tudo no banco SQLite.
