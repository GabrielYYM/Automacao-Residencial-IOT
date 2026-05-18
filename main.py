from machine import Pin, ADC
from umqtt.simple import MQTTClient
import dht
import ujson
import time
import network
import socket

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
    def controle_lampada(self, estado):
        self.lampada.value(estado)
        
    def controle_tranca(self, estado):
        self.tranca.value(estado)

    def controlar_ar(self, estado):
        self.ar.value(estado)
        
    def controlar_umidificador(self, estado):
        self.umidificador.value(estado)

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
        if dados["iluminacao"] in ["Escuro", "Dia Nublado"] and dados["movimento"] == 1:
            self.lampada.value(1)
        else:
            self.lampada.value(0)

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

    #Publlicação
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
        sta_if.connect('Wokwi-GUEST', '')

        while not sta_if.isconnected():
            print(".", end="")
            time.sleep(0.1)
        print("Connected!")

def gerar_html(dados):
    # Transforma o 1 ou 0 do sensor PIR em texto legível
    movimento_texto = "Detectado" if dados["movimento"] == 1 else "Sem movimento"
    
    # Criamos o HTML já injetando as variáveis em tempo real
    html = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Painel da Estufa</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; }}
            .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; text-align: left; }}
            h1 {{ color: #2c3e50; }}
            p {{ font-size: 18px; color: #34495e; }}
            .valor {{ font-weight: bold; color: #2980b9; }}
        </style>
    </head>
    <body>
        <h1>Monitoramento da Estufa</h1>
        <div class="card">
            <p>Temperatura: <span class="valor">{dados["temperatura"]} &deg;C</span></p>
            <p>Umidade: <span class="valor">{dados["umidade"]} %</span></p>
            <p>Nivel de Gas: <span class="valor">{dados["gas"]} %</span></p>
            <p>Iluminacao: <span class="valor">{dados["iluminacao"]}</span></p>
            <p>Movimento: <span class="valor">{movimento_texto}</span></p>
        </div>
        <br>
        <button onclick="location.reload();" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">Atualizar Dados</button>
    </body>
    </html>
    """
    return html

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

sensor = Sensor()
reles = Relays()

porta = 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', porta))
s.listen(5)
s.settimeout(0.2)
print("http://localhost:8181")

ultimo_envio_mqtt = 0 
intervalo = 3000
dados_atuais = sensor.leitura()

while True:
    
    try:
        conn, addr = s.accept()
        conn.settimeout(2.0)

        request = conn.recv(4096).decode('utf-8') 

        if 'GET /favicon.ico' in request:
            conn.sendall("HTTP/1.1 404 Not Found\r\n\r\n".encode('utf-8'))
            conn.close()
        elif request:
            pagina = gerar_html(dados_atuais)
            resposta = "HTTP/1.1 200 OK\r\n"
            resposta += "Content-Type: text/html; charset=utf-8\r\n"
            resposta += f"Content-Length: {len(pagina)}\r\n"
            resposta += "Connection: close\r\n\r\n"
            resposta += pagina
            conn.sendall(resposta.encode('utf-8'))
            time.sleep(0.1) 
            conn.close()
            
    except OSError:
        pass
    except Exception as e:
        print(f"Erro no servidor web: {e}")
        try:
            conn.close()
        except:
            pass

    agora = time.ticks_ms()
    
    if time.ticks_diff(agora, ultimo_envio_mqtt) > intervalo:
        dados_atuais = sensor.leitura()
        reles.automacao(dados_atuais)
        
        mqtt.publish({
            "umidade" : dados_atuais["umidade"],
            "temperatura" : dados_atuais["temperatura"],
            "gas": dados_atuais["gas"],
            "iluminacao": dados_atuais["iluminacao"],
            "movimento": dados_atuais["movimento"]
        })
        
        ultimo_envio_mqtt = agora