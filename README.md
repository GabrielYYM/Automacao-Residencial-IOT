
Automação Residencial IOT — Documentação Técnica
===============================================

Descrição
---------
Projeto de automação residencial baseado em ESP32 e MicroPython, utilizando um display OLED SSD1306 para exibição de informações e controle de funcionalidades do sistema.

Objetivo
--------
Fornecer um firmware simples para exibir informações no display e controlar funcionalidades de automação via ESP32.

Conteúdo do repositório
-----------------------
- `main.py` — código principal que roda no dispositivo.
- `ssd1306.mpy` — biblioteca do display SSD1306 (pré-empacotada para MicroPython).
- `flows.json` — arquivo de configuração/fluxos (uso do projeto).
- `esp32/` — arquivos específicos do hardware e configuração (diagramas, Wokwi, etc.).
- `docs/` — documentação complementar e diagramas.

Requisitos de hardware
----------------------
- Placa ESP32.
- Display OLED SSD1306 (I2C).
- Cabos e fonte de alimentação adequada (3.3V).

Ligação (exemplo comum para ESP32)
---------------------------------
- VCC -> 3V3
- GND -> GND
- SDA -> GPIO21
- SCL -> GPIO22

Observação: ajuste os pinos I2C no código se necessário.

Pré-requisitos de software
--------------------------
- MicroPython instalado na ESP32.
- `mpremote` (ou outra ferramenta compatível) para transferir arquivos e acessar o REPL.

Procedimento de atualização / deploy
-----------------------------------
1. Conecte ao dispositivo (exemplo usando servidor RFC2217 local na porta 4000):

```bash
python -m mpremote connect port:rfc2217://localhost:4000 cp ssd1306.mpy :ssd1306.mpy
python -m mpremote connect port:rfc2217://localhost:4000 cp main.py :main.py
# Pressione CTRL+D no REPL para reiniciar e aplicar as mudanças
```

2. Verifique o console/REPL para mensagens de inicialização.

Execução
--------
Ao reiniciar, a placa executará `main.py` automaticamente (se presente na raíz do dispositivo).

Referências e diagramas
----------------------
- Ver a pasta `esp32/` para diagramas e configuração de simulação (Wokwi).

Contato
-------
Para dúvidas ou contribuições, abra uma issue neste repositório.

Automação Residencial IoT
ESP32 • MicroPython • OLED SSD1306
