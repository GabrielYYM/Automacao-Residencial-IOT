from machine import Pin, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
from umqtt.simple import MQTTClient
import dht
import ujson
import time
import network
import socket
import gc

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

    def leitura(self):
        dados = {"temperatura":0, "umidade": 0, "iluminacao": 0, "gas":0, "movimento":0}

        #dht
        try:
            self.dht.measure()
            dados["temperatura"] = self.dht.temperature()
            dados["umidade"] = self.dht.humidity()
        except OSError as e:
            print(f"erro leitura dht{e}")
        #gas-sensor
        try:
            valor_gas = self.gas.read()
            dados["gas"] = round((valor_gas/4095)*100 ,2)
        except OSError as e:
            print(f"erro leitura gas{e}")    
        #iluminacao
        try:
            valor_iluminacao = self.ldr.read()
            if valor_iluminacao >= 1000: 
                dados["iluminacao"] = "Escuro" 
            elif 170 <= valor_iluminacao < 1000:
                dados["iluminacao"] = "Dia Nublado"
            elif 39 <= valor_iluminacao < 170:
                dados["iluminacao"] = "Claridade Total"
            else:
                dados["iluminacao"] = "Sol Direto"
        except OSError as e:
            print(f"erro leitura luz{e}")

        #movimento
        try:
            dados["movimento"] = self.motion.value()
        except OSError as e:
            print(f"erro leitura movimento{e}")  

        return dados

class Relays:
    # Relay = 18 Roxo
    # Relay = 17 Roxo
    # Relay = 16 Roxo
    # Relay = 4  Roxo
    def __init__(self):
        self.tranca = Pin(18, Pin.OUT)
        self.lampada = Pin(17, Pin.OUT)
        self.ar = Pin(16, Pin.OUT)
        self.umidificador = Pin(4, Pin.OUT)

        self.lampada.value(0)
        self.tranca.value(0)
        self.ar.value(0)
        self.umidificador.value(0)

    #controle manual    
    def processar_comando(self, topico, msg):
        comando = msg.decode('utf-8')
        print(f"Recebido no tópico {topico}: {comando}")
        
        if comando == "LIGAR_LAMPADA":
            self.lampada.value(1)
        elif comando == "DESLIGAR_LAMPADA":
            self.lampada.value(0)
        
        elif comando == "ABRIR_TRANCA":
            self.tranca.value(1)
        elif comando == "FECHAR_TRANCA":
            self.tranca.value(0)
        
        elif comando == "LIGAR_AR":
            self.ar.value(1)
        elif comando == "DESLIGAR_AR":
            self.ar.value(0)
        
        elif comando == "LIGAR_UMIDIFICADOR":
            self.umidificador.value(1)
        elif comando == "DESLIGAR_UMIDIFICADOR":
            self.umidificador.value(0)

    def automacao(self, dados):
        # ar condicionado
        if dados["temperatura"] > 28:
            self.ar.value(1) 
        else:
            self.ar.value(0)
            
        # umidificador
        if dados["umidade"] < 30:
            self.umidificador.value(1)
        else:
            self.umidificador.value(0)
            
        # lampada
        if dados["iluminacao"] in ["Escuro", "Dia Nublado"]:
            self.lampada.value(1)
        else:
            self.lampada.value(0)


class Display:
#Laranja tela oled = scl=33, sda=32     
    def __init__(self):
        self.i2c = SoftI2C(scl=Pin(33), sda=Pin(32))
        self.oled = SSD1306_I2C(128, 64, self.i2c)
        self.tela = 1

    def atualizar_tela(self, dados):
        try:
            self.oled.fill(0)
            self.oled.text(f"Temp: {dados['temperatura']}C", 0, 0)
            self.oled.text(f"Umid: {dados['umidade']}%", 0, 10)
            self.oled.text(f"Gas: {dados['gas']}%", 0, 20)
            self.oled.text(f"Luz: {dados['iluminacao']}", 0, 30)
            if dados["movimento"] == 1:
                self.oled.text("ALERTA: Movimento!", 0, 45)
            self.oled.show()
        except OSError as e:
            print(f"Erro display: {e}")

class MQTT:
    def __init__(self, MQTT_CLIENT_ID, MQTT_BROKER, MQTT_USER, MQTT_PASSWORD, topic):
        self.MQTT_BROKER = MQTT_BROKER
        self.topic = topic
        self.client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_BROKER, port=8883, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60, ssl=True, ssl_params={'server_hostname': MQTT_BROKER})
    
    def connectMQTT(self):
        gc.collect()
        try:
            self.client.connect()
            self.client.subscribe(b"autohome/comando")
            print("MQTT Conectado!")
        except Exception as e:
            print(f"Erro ao conectar no MQTT: {e}")

    #Publlicação
    def publish(self, dados):
        try:
            message = ujson.dumps(dados)
            print(f"Publicando no tópico '{self.topic}': {message}")
            self.client.publish(self.topic, message)
        except Exception as e:
            print(f"Erro ao publicar MQTT: {e}")
            gc.collect()
            self.connectMQTT()

    def set_callback(self, funcao_callback):
        self.client.set_callback(funcao_callback)
        
    def check_msg(self):
        self.client.check_msg()

class ConexaoWifi:
    def connectWifi(self):
        print("Connecting to WiFi", end="")
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        sta_if.connect('Wokwi-GUEST', '')

        while not sta_if.isconnected():
            print(".", end="")
            time.sleep(0.1)
        print("Connected!")

def html(dados):
    
    html = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Home</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>Monitoramento</h1>
        <div class="card">
            <p>Temperatura: <b>{dados["temperatura"]} &deg;C</b></p>
            <p>Umidade: <b>{dados["umidade"]} %</b></p>
            <p>Nivel de Gas: <b>{dados["gas"]} %</b></p>
            <p>Iluminacao: <b>{dados["iluminacao"]}</b></p>
        </div>
    </body>
    </html>
    """
    return html

wifi = ConexaoWifi()
wifi.connectWifi()

sensor = Sensor()
reles = Relays()
display = Display()

mqtt = MQTT(
  MQTT_CLIENT_ID="micropython-home",
  MQTT_BROKER="9c401a8e1d2c400ea04310884e277b03.s1.eu.hivemq.cloud",
  MQTT_USER="UserGabriel",
  MQTT_PASSWORD="SehaCuster1",
  topic="autohome"
)
mqtt.set_callback(reles.processar_comando)
mqtt.connectMQTT()

porta = 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', porta))
s.listen(5)
s.settimeout(0.5)
sta_if = network.WLAN(network.STA_IF)
try:
    ip = sta_if.ifconfig()[0]
except Exception:
    ip = '0.0.0.0'
print(f"http://localhost:8181")

ultimo_envio_mqtt = 0 
intervalo_mqtt = 5000

intervalo_sensores = 4000
ultimo_leitura = time.ticks_ms()

dados_atuais = sensor.leitura()

while True:
    try:
        try:
            mqtt.check_msg() 
        except OSError as e:
            print(f"Erro ao checar MQTT: {e}")

        conn, addr = s.accept()
        conn.settimeout(2.0)
        
        try:
            request = conn.recv(4096).decode('utf-8')
            
            if 'GET /favicon.ico' in request:
                conn.sendall("HTTP/1.1 404 Not Found\r\n\r\n".encode('utf-8'))
            elif request:
                pagina = html(dados_atuais)
                resposta = "HTTP/1.1 200 OK\r\n"
                resposta += "Content-Type: text/html; charset=utf-8\r\n"
                resposta += f"Content-Length: {len(pagina)}\r\n"
                resposta += "Connection: close\r\n\r\n"
                resposta += pagina
                conn.sendall(resposta.encode('utf-8'))
        
        except OSError as e:
            print(f"Erro no processamento da requisição: {e}")
        finally:
            time.sleep(0.1)
            try:
                conn.close()
            except:
                pass

    except OSError as e:
        pass #evitar spam de log por timeout
    except Exception as e:
        print(f"Erro inesperado no servidor web: {repr(e)}")

    timer = time.ticks_ms()
    
    if time.ticks_diff(timer, ultimo_leitura) > intervalo_sensores:
        dados_atuais = sensor.leitura()
        reles.automacao(dados_atuais)
        display.atualizar_tela(dados_atuais)
        ultimo_leitura = timer
    
    if time.ticks_diff(timer, ultimo_envio_mqtt) > intervalo_mqtt:
        mqtt.publish({
            "umidade" : dados_atuais["umidade"],
            "temperatura" : dados_atuais["temperatura"],
            "gas": dados_atuais["gas"],
            "iluminacao": dados_atuais["iluminacao"],
            "movimento": dados_atuais["movimento"]
        })
        
        ultimo_envio_mqtt = timer