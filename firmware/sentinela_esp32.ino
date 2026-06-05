/*
 * ============================================================================
 *  SENTINELA ORBITAL - Estacao de Borda (Edge) para Deteccao de Queimadas
 *  Firmware para ESP32 (Arduino Framework / C++)
 * ============================================================================
 *
 *  OBJETIVO
 *  --------
 *  Esta estacao e o "olho no chao" do Sentinela Orbital. Enquanto os satelites
 *  do INPE veem o Brasil de cima, esta estacao mede as condicoes LOCAIS em
 *  pontos criticos (Cerrado, Pantanal...) e detecta o inicio de uma queimada
 *  ANTES que o satelite consiga - reduzindo o tempo de resposta de horas para
 *  minutos.
 *
 *  ARQUITETURA EDGE (decisao na borda)
 *  -----------------------------------
 *  O ESP32 NAO depende da nuvem para soar o alarme. Ele calcula um indice de
 *  risco local e, se ultrapassar o limiar, aciona LED + buzzer imediatamente
 *  (mesmo sem internet). Em paralelo, publica a telemetria via MQTT para o
 *  servidor (mqtt_receptor.py), que alimenta o modelo de IA e o dashboard.
 *
 *  SENSORES
 *  --------
 *    - BME280 (I2C)        : temperatura, umidade do ar, pressao
 *    - MQ-135 (analogico)  : concentracao de fumaca/gases (proxy de CO2/fumaca)
 *    - Sensor capacitivo   : umidade do solo
 *    - LED + Buzzer        : alerta local na borda
 *
 *  LIGACOES (pinout sugerido)
 *  --------------------------
 *    BME280 SDA -> GPIO 21      MQ-135 AOUT -> GPIO 34 (ADC1)
 *    BME280 SCL -> GPIO 22      Solo  AOUT  -> GPIO 35 (ADC1)
 *    LED        -> GPIO 2       Buzzer      -> GPIO 4
 *
 *  BIBLIOTECAS NECESSARIAS (Library Manager)
 *  -----------------------------------------
 *    - Adafruit BME280 Library
 *    - Adafruit Unified Sensor
 *    - PubSubClient (MQTT)
 *    - ArduinoJson
 *
 *  Conceitos das Fases 3 e 4: IoT, Edge Computing, automacao e logica de
 *  controle baseada em sensores, integracao via protocolo MQTT.
 * ============================================================================
 */

#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

// ----------------------------------------------------------------------------
// CONFIGURACAO (ajustar conforme a instalacao)
// ----------------------------------------------------------------------------
const char* WIFI_SSID     = "SUA_REDE_WIFI";
const char* WIFI_SENHA    = "SUA_SENHA_WIFI";

const char* MQTT_BROKER   = "broker.hivemq.com";   // broker publico p/ POC
const int   MQTT_PORTA    = 1883;
const char* MQTT_TOPICO   = "sentinela/estacoes/telemetria";
const char* ESTACAO_ID    = "ESP32-CER-01";        // identificador da estacao
const float ESTACAO_LAT   = -15.78;                // Brasilia-DF (Cerrado)
const float ESTACAO_LON   = -47.93;

// Pinos
const int PINO_MQ135 = 34;   // ADC1 - fumaca/gas
const int PINO_SOLO  = 35;   // ADC1 - umidade do solo
const int PINO_LED   = 2;    // LED de alerta
const int PINO_BUZZER= 4;    // buzzer de alerta

// Limiares de decisao na borda
const float LIMIAR_FUMACA_PPM = 500.0;   // fumaca critica
const float LIMIAR_RISCO      = 75.0;    // indice de risco critico (0-100)
const unsigned long INTERVALO_MS = 30000; // 30 s entre leituras

// ----------------------------------------------------------------------------
// OBJETOS GLOBAIS
// ----------------------------------------------------------------------------
Adafruit_BME280 bme;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
unsigned long ultimaLeitura = 0;

// ----------------------------------------------------------------------------
// CONVERSAO DO MQ-135: valor ADC bruto (0-4095) -> ppm aproximado
// (calibracao simplificada para POC; em campo usa-se Rs/Ro do datasheet)
// ----------------------------------------------------------------------------
float lerFumacaPPM() {
  int bruto = analogRead(PINO_MQ135);
  // mapeamento linear didatico: 0 ADC ~ 10 ppm, 4095 ADC ~ 1500 ppm
  float ppm = 10.0 + (bruto / 4095.0) * 1490.0;
  return ppm;
}

// Umidade do solo: ADC -> percentual (sensor capacitivo, invertido)
float lerUmidadeSolo() {
  int bruto = analogRead(PINO_SOLO);
  float pct = 100.0 - (bruto / 4095.0) * 100.0;
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

// ----------------------------------------------------------------------------
// CALCULO DO INDICE DE RISCO LOCAL (espelha a logica do servidor)
// Mesma formula usada no Python, garantindo coerencia borda <-> nuvem.
// ----------------------------------------------------------------------------
float calcularRiscoLocal(float tempMax, float umidade, float vento,
                         float umidadeSolo) {
  float risco = 0.0;
  risco += (tempMax - 20.0) * 1.8;       // calor
  risco += (100.0 - umidade) * 0.55;     // ar seco
  risco += vento * 1.2;                  // vento
  risco += (100.0 - umidadeSolo) * 0.35; // solo seco = mais combustivel
  if (risco < 0)   risco = 0;
  if (risco > 100) risco = 100;
  return risco;
}

// ----------------------------------------------------------------------------
// ACIONAMENTO DO ALERTA LOCAL (na borda, independente da nuvem)
// ----------------------------------------------------------------------------
void acionarAlerta(bool ligar) {
  if (ligar) {
    digitalWrite(PINO_LED, HIGH);
    // bipe intermitente
    for (int i = 0; i < 3; i++) {
      tone(PINO_BUZZER, 2000, 150);
      delay(200);
    }
  } else {
    digitalWrite(PINO_LED, LOW);
    noTone(PINO_BUZZER);
  }
}

// ----------------------------------------------------------------------------
// CONECTIVIDADE
// ----------------------------------------------------------------------------
void conectarWiFi() {
  Serial.print("Conectando ao WiFi");
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" FALHA - operando em modo offline (edge).");
  }
}

void conectarMQTT() {
  while (!mqtt.connected() && WiFi.status() == WL_CONNECTED) {
    Serial.print("Conectando ao broker MQTT...");
    String clientId = String(ESTACAO_ID) + "-" + String(random(0xffff), HEX);
    if (mqtt.connect(clientId.c_str())) {
      Serial.println(" conectado!");
    } else {
      Serial.print(" falhou (rc=");
      Serial.print(mqtt.state());
      Serial.println("), nova tentativa em 3s");
      delay(3000);
    }
  }
}

// ----------------------------------------------------------------------------
// SETUP
// ----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== SENTINELA ORBITAL - Estacao de Borda ===");

  pinMode(PINO_LED, OUTPUT);
  pinMode(PINO_BUZZER, OUTPUT);
  digitalWrite(PINO_LED, LOW);

  // Inicializa BME280 (endereco 0x76 ou 0x77)
  Wire.begin(21, 22);
  if (!bme.begin(0x76)) {
    Serial.println("AVISO: BME280 nao encontrado. Verifique a fiacao I2C.");
  }

  conectarWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORTA);

  // bipe de inicializacao
  tone(PINO_BUZZER, 1500, 200);
}

// ----------------------------------------------------------------------------
// LOOP PRINCIPAL
// ----------------------------------------------------------------------------
void loop() {
  if (WiFi.status() == WL_CONNECTED && !mqtt.connected()) {
    conectarMQTT();
  }
  mqtt.loop();

  unsigned long agora = millis();
  if (agora - ultimaLeitura < INTERVALO_MS) {
    return;
  }
  ultimaLeitura = agora;

  // ---- 1. Leitura dos sensores ----
  float temperatura = bme.readTemperature();
  float umidadeAr   = bme.readHumidity();
  float pressao     = bme.readPressure() / 100.0F;  // Pa -> hPa
  float fumaca      = lerFumacaPPM();
  float umidadeSolo = lerUmidadeSolo();

  // ---- 2. Decisao na borda (edge) ----
  float risco = calcularRiscoLocal(temperatura, umidadeAr, 2.5, umidadeSolo);
  bool alerta = (fumaca > LIMIAR_FUMACA_PPM) || (risco > LIMIAR_RISCO);
  acionarAlerta(alerta);

  // ---- 3. Log local ----
  Serial.printf("T=%.1fC  UR=%.1f%%  P=%.1fhPa  Fumaca=%.0fppm  "
                "Solo=%.1f%%  Risco=%.0f  %s\n",
                temperatura, umidadeAr, pressao, fumaca, umidadeSolo, risco,
                alerta ? "[ALERTA!]" : "[OK]");

  // ---- 4. Publicacao MQTT (JSON) ----
  if (mqtt.connected()) {
    StaticJsonDocument<320> doc;
    doc["estacao_id"]       = ESTACAO_ID;
    doc["latitude"]         = ESTACAO_LAT;
    doc["longitude"]        = ESTACAO_LON;
    doc["temperatura_c"]    = round(temperatura * 10) / 10.0;
    doc["umidade_ar_pct"]   = round(umidadeAr * 10) / 10.0;
    doc["pressao_hpa"]      = round(pressao * 10) / 10.0;
    doc["umidade_solo_pct"] = round(umidadeSolo * 10) / 10.0;
    doc["fumaca_ppm"]       = (int)fumaca;
    doc["risco_local"]      = (int)risco;
    doc["alerta"]           = alerta;

    char buffer[320];
    serializeJson(doc, buffer);
    mqtt.publish(MQTT_TOPICO, buffer);
    Serial.println("  -> telemetria publicada via MQTT");
  }
}
