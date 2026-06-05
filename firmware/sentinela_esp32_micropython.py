# =============================================================================
#  SENTINELA ORBITAL - Estacao de Borda (versao MicroPython)
#  Alternativa ao firmware Arduino, para quem prefere MicroPython no ESP32.
# =============================================================================
#
#  Requer (instalar via upip / mip no dispositivo):
#    - umqtt.simple  (cliente MQTT)
#    - bme280        (driver do sensor)
#
#  Conceitos: IoT, automacao, logica de controle na borda, MQTT.
# =============================================================================

import time
import ujson
import network
from machine import Pin, ADC, I2C, PWM

try:
    import bme280
except ImportError:
    bme280 = None  # permite testar o restante sem o driver

from umqtt.simple import MQTTClient

# ----------------------------------------------------------------------------
# CONFIGURACAO
# ----------------------------------------------------------------------------
WIFI_SSID = "SUA_REDE_WIFI"
WIFI_SENHA = "SUA_SENHA_WIFI"

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPICO = b"sentinela/estacoes/telemetria"
ESTACAO_ID = "ESP32-CER-01"
ESTACAO_LAT = -15.78
ESTACAO_LON = -47.93

LIMIAR_FUMACA_PPM = 500.0
LIMIAR_RISCO = 75.0
INTERVALO_S = 30

# Pinos
mq135 = ADC(Pin(34))
mq135.atten(ADC.ATTN_11DB)          # leitura ate ~3.3V
solo = ADC(Pin(35))
solo.atten(ADC.ATTN_11DB)
led = Pin(2, Pin.OUT)
buzzer = PWM(Pin(4), freq=2000, duty=0)

i2c = I2C(0, scl=Pin(22), sda=Pin(21))


def conectar_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Conectando ao WiFi...")
        sta.connect(WIFI_SSID, WIFI_SENHA)
        t = 0
        while not sta.isconnected() and t < 20:
            time.sleep(0.5)
            t += 1
    if sta.isconnected():
        print("WiFi OK:", sta.ifconfig()[0])
    else:
        print("Sem WiFi - modo offline (edge).")
    return sta


def ler_fumaca_ppm():
    bruto = mq135.read()  # 0..4095
    return 10.0 + (bruto / 4095.0) * 1490.0


def ler_umidade_solo():
    bruto = solo.read()
    pct = 100.0 - (bruto / 4095.0) * 100.0
    return max(0.0, min(100.0, pct))


def calcular_risco_local(temp_max, umidade, vento, umidade_solo):
    risco = 0.0
    risco += (temp_max - 20.0) * 1.8
    risco += (100.0 - umidade) * 0.55
    risco += vento * 1.2
    risco += (100.0 - umidade_solo) * 0.35
    return max(0.0, min(100.0, risco))


def acionar_alerta(ligar):
    if ligar:
        led.value(1)
        for _ in range(3):
            buzzer.duty(512)
            time.sleep(0.15)
            buzzer.duty(0)
            time.sleep(0.2)
    else:
        led.value(0)
        buzzer.duty(0)


def main():
    conectar_wifi()
    cliente = MQTTClient(ESTACAO_ID, MQTT_BROKER)
    try:
        cliente.connect()
        print("MQTT conectado.")
    except Exception as e:
        print("Falha MQTT:", e)
        cliente = None

    sensor = bme280.BME280(i2c=i2c) if bme280 else None

    while True:
        if sensor:
            temperatura, pressao_pa, umidade_ar = sensor.read_compensated_data()
            temperatura = temperatura / 100.0
            pressao = pressao_pa / 25600.0  # conforme driver
            umidade_ar = umidade_ar / 1024.0
        else:
            temperatura, pressao, umidade_ar = 30.0, 1013.0, 35.0

        fumaca = ler_fumaca_ppm()
        umidade_solo = ler_umidade_solo()
        risco = calcular_risco_local(temperatura, umidade_ar, 2.5, umidade_solo)
        alerta = (fumaca > LIMIAR_FUMACA_PPM) or (risco > LIMIAR_RISCO)
        acionar_alerta(alerta)

        print("T=%.1fC UR=%.1f%% Fumaca=%.0fppm Solo=%.1f%% Risco=%.0f %s" % (
            temperatura, umidade_ar, fumaca, umidade_solo, risco,
            "[ALERTA]" if alerta else "[OK]"))

        if cliente:
            payload = ujson.dumps({
                "estacao_id": ESTACAO_ID,
                "latitude": ESTACAO_LAT,
                "longitude": ESTACAO_LON,
                "temperatura_c": round(temperatura, 1),
                "umidade_ar_pct": round(umidade_ar, 1),
                "pressao_hpa": round(pressao, 1),
                "umidade_solo_pct": round(umidade_solo, 1),
                "fumaca_ppm": int(fumaca),
                "risco_local": int(risco),
                "alerta": alerta,
            })
            try:
                cliente.publish(MQTT_TOPICO, payload)
            except Exception as e:
                print("Erro ao publicar:", e)

        time.sleep(INTERVALO_S)


if __name__ == "__main__":
    main()
