from machine import Pin, ADC
from umqtt.simple import MQTTClient
import dht
import ujson
import time
import network

class Sensor: 
    # pir-motion-sensor = 23 Verde
    # dht22 = 22 Verde
    # gas-sensor = 34 Aout Azul
    # gas-sensor = 21 Dout Amarelo
    # photoresistor-sensor = 35 AO Azul
    # photoresistor-sensor = 19 DO Amarelo
    def __init__(self):
        self.dht = dht.DHT22(Pin(22))
        self.ldr = ADC(Pin(35))
        self.gas = ADC(Pin(34))
        self.motion = Pin(23, Pin.IN)

class Relays:
    # Relay = 18 Roxo
    # Relay = 17 Roxo
    # Relay = 16 Roxo
    # Relay = 4  Roxo
    def __init__(self):
        self.tranca = Pin(18, Pin.OUT)
        self.lampada = Pin(17, Pin.OUT)
        self.condicianado = Pin(16, Pin.OUT)
        self.umidificador = Pin(4, Pin.OUT)

class MQTT:
    def __init__(self, MQTT_CLIENT_ID, MQTT_BROKER, MQTT_USER, MQTT_PASSWORD, topic):
        self.MQTT_BROKER = MQTT_BROKER
        self.topic = topic
        self.client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_BROKER, port=8883, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60, ssl=True, ssl_params={'server_hostname': MQTT_BROKER})
    
    def connectMQTT(self):
        try:
            self.client.connect()
            print("MQTT Conectado!")
        except Exception as e:
            print(f"Erro ao conectar no MQTT: {e}")
            time.sleep(3)

    # Publicação
    def publish(self, dados):
        try:
            message = ujson.dumps(dados)
            print(f"Publicando no tópico '{self.topic}': {message}")
            self.client.publish(self.topic, message)
        except Exception as e:
            print(f"Erro ao publicar MQTT: {e}")
            self.connectMQTT()

class ConexaoWifi:
    def connectWifi(self):
        print("Connecting to WiFi", end="")
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        sta_if.connect('microcontroler', '')

        while not sta_if.isconnected():
            print(".", end="")
            time.sleep(0.1)
            print("Connected!")

wifi = ConexaoWifi()
wifi.connectWifi()

mqtt = MQTT(
  MQTT_CLIENT_ID="micropython-estufa",
  MQTT_BROKER="3de8a2c7550545e9924723f1202e8918.s1.eu.hivemq.cloud",
  MQTT_USER="Teste",
  MQTT_PASSWORD="TestPassword1",
  topic="autohome"
)
mqtt.connectMQTT()

while True:
    print("ok")
    time.sleep(1)