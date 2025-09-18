# -Renewable-Energy-Monitoring-System-for-Microgrids
The growing incorporation of renewable energy sources into microgrids creates increased forecasting, load balancing, and efficiency challenges because of their intermittent nature. Conventional energy management systems tend to be non-scalable and predictive, which results in power distribution inefficiencies and cost inefficiencies. 
## -Key Features
- **Live Sensing**  
  - PZEM-004T: AC voltage, current, and power.  
  - DHT11: Ambient temperature & humidity.  
- **Predictive Analytics**  
  - FastAPI server with KNN/ML model predicts grid status (*Stable* / *Unstable*).  
  - Weather API (e.g., OpenWeatherMap) supplies forecast data to enhance model accuracy.  
- **Multi-Hop Connectivity**  
  - Optional **LoRa SX1278** modules enable long-range, low-power communication between remote microgrids and a central ESP8266 gateway.  
- **Automated Control**  
  - ESP8266 triggers relays to balance loads or isolate faults.  
- **Cloud Dashboard**  
  - Blynk app provides mobile/desktop real-time visualization, weather info, and manual override.  
-**Communication module (LoRa)**: Each microgrid relay channel uses Arduino + SX1278 to gather sensor data and send it via LoRa.
- **Gateway**: ESP8266 receives LoRa packets, posts JSON to FastAPI, and updates Blynk.
- **Backend**: FastAPI merges sensor data with **Weather API** forecasts before running the ML prediction in that way providing the most optimised output.
- 
| Component          | Purpose |

|--------------------|--------|

**Transmitter side**

| ESP8266 (NodeMCU)  | Wi-Fi gateway and relay controller |

|LoRa sensor module  | Transmitter data controlling       |

| 4-Channel Relay    | Load control                       |

**Reciever side**

| PZEM-004T v3       | AC voltage/current/power sensing   |

| DHT11              | Temperature & humidity             |

|Arduino Uno         | Takes the data and send it Nodemcu |

| LoRa SX1278 (433 MHz) | Long-range RF link              |

| 4-Channel Relay       |       Load control              |

| Power supply & wiring | Stable DC source                |

##  Project setup ##

### Hardware Setup
- Connect **LoRa nodes** to Arduino (SPI: NSS=D10, MOSI=D11, MISO=D12, SCK=D13, DIO0=D2, RST=D9).
- Gateway ESP8266 also connects to LoRa SX1278 with similar SPI pins.
- Wire PZEM-004T and DHT11/BMP280 as per schematic.
- Relays on ESP8266: D1 and D2 (active LOW).

### Backend (FastAPI + ML + Weather)
```bash
git clone https://github.com/<your-user>/<repo>.git
cd backend
pip install -r requirements.txt
export WEATHER_API_KEY=<your_openweather_api_key>
uvicorn main:app --host 0.0.0.0 --port 8000

** block diagram**

                 [Weather API]
                       |
                       v
           +---------------------------+
           |    FastAPI + ML Server    |
           +---------------------------+
                ^                 |
                |                 v
           +-----------------------------+
           |   ESP8266 Gateway & Relay   |
           |  (Wi-Fi + LoRa Receiver)    |
           +-----------------------------+
                  |      |                ^
                  |      |                |
          Relay-1 |      | Relay-2        |
        (Main  Grid) (Renewable Control)  |
                  ^                       |
    ----------------------------------------------
    |                                          |
[LoRa Node 1]                             [LoRa Node 2]
                                               |
                                          [Arduino Uno]
                                               |
                                   [PZEM-004T  +  DHT Sensor]
