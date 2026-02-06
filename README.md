# Wemos D1 Mini MicroPython MQTT Heartbeat Project

This repository contains the complete setup guide and source code for a robust ESP8266-based MQTT device. It features a non-blocking execution loop, hardware watchdog protection, dynamic update rates via MQTT subscription, and detailed hardware diagnostics.

---

## 1. Wemos D1 Mini Setup

### Software Requirements
* **Project Folder:** Create a folder on your computer and open it in **VS Code**.
* **MicroPython Firmware:** Download the latest [Generic ESP8266 Firmware](https://micropython.org/download/ESP8266_GENERIC/).
* **Python 3:** Ensure [Python](https://www.python.org/) is installed on your system.
* **Pip Update:** From the VS Code Terminal, update the package manager:
    ```powershell
    python.exe -m pip install --upgrade pip
    ```
* **Flash Tool:** Install `esptool` via the terminal:
    ```powershell
    pip install esptool
    ```
* **Drivers:** Install the [CH340 Driver](https://www.wemos.cc/en/latest/ch340_driver.html) for Wemos USB communication.

---

## 2. Flashing the Firmware

Connect your Wemos D1 Mini and identify the COM port (e.g., COM4). 

### Step A: Erase existing flash
```powershell
esptool --port COM4 erase_flash
```

### Step B: Write new firmware
```powershell
esptool --port COM4 --baud 460800 write_flash --flash_size=detect 0 ESP8266_GENERIC-20251209-v1.27.0.bin   
```

## 3. Project Structure & Libraries

Inside your project folder, create the following files:
* **`config.py`**: Stores your WiFi and MQTT credentials.
* **`boot.py`**: Manages the initial WiFi connection and startup LED blink.
* **`main.py`**: The primary application loop containing the logic.

### Adding the MQTT Library
Run this PowerShell command in the VS Code terminal to create the library folder and download the `umqtt.simple` library automatically:

* The `umqtt` directory needs to be in the same directory as the `.py` files
```powershell
# 1. Create the folder if it doesn't exist
if (!(Test-Path "umqtt")) { mkdir umqtt }

# 2. Download umqtt.robust
$urlRobust = "https://raw.githubusercontent.com/micropython/micropython-lib/master/micropython/umqtt.robust/umqtt/robust.py"
Invoke-RestMethod -Uri $urlRobust | Out-File -FilePath "umqtt\robust.py" -Encoding utf8

# 3. IMPORTANT: robust.py requires simple.py in the same folder
$urlSimple = "https://raw.githubusercontent.com/micropython/micropython-lib/master/micropython/umqtt.simple/umqtt/simple.py"
Invoke-RestMethod -Uri $urlSimple | Out-File -FilePath "umqtt\simple.py" -Encoding utf8
```

## 4. Source Code Implementation

### `config.py`
<details>
<summary>Click to expand <b>config.py</b> source code</summary>

```python
# config.py
WIFI_SSID = "{your_WIFI_SSID}"
WIFI_PASS = "{your_WIFI_PASS}"

# Static IP Settings (IP, Subnet, Gateway, DNS)
STATIC_IP="{your_STATIC_IP}" #ex. 192.168.1.2
SUBNET_MASK="{your_SUBNET_MASK}" #ex. 255.255.255.0
GATEWAY="{your_GATEWAY}" #ex. 192.168.1.1
DNS="{your_DNS}" # 8.8.8.8 (Google) and/or 192.168.1.1

IP_CONFIG = (STATIC_IP, SUBNET_MASK, GATEWAY, DNS)

MQTT_BROKER = "{your_MQTT_BROKER_IP}" 
MQTT_PORT = "{your_MQTT_PORT}" #ex. 1883 is the default
CLIENT_ID = "{your_CLIENT_ID}" #ex. needs to be unique
```
</details>

### `boot.py`
<details>
<summary>Click to expand <b>boot.py</b> source code</summary>

```python
import network
import utime
import config  # Import your new config file
import machine
led = machine.Pin(2, machine.Pin.OUT)

def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to network...')
        sta_if.active(True)
        
        # Pull the tuple directly from config.py
        sta_if.ifconfig(config.IP_CONFIG)
        
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASS)
        
        timeout = 0
        while not sta_if.isconnected() and timeout < 15:
            led.value(not led.value())
            utime.sleep(1)
            timeout += 1
            print(".", end="")
            
    if sta_if.isconnected():
        print('\nConnected! IP:', sta_if.ifconfig()[0])

connect_wifi()
```
</details>

### `main.py`
This script uses a Non-blocking Timer pattern. It checks for new MQTT messages every 10ms, allowing for near-instant updates from Ignition even if the publish rate is set very high.

<details>
<summary>Click to expand <b>main.py</b> source code</summary>

```python
import machine
import utime
import ujson
import network
import os
import gc   # For memory stats
import esp  # For ESP8266 specific stats
import config  # Pulls metadata from config.py
import ubinascii
from umqtt.simple import MQTTClient

# MQTT Topics
TOPIC_PUB = "wemos/{client_id}".format(client_id=config.CLIENT_ID)
TOPIC_SUB_RATE = "wemos/updateRate"

# LED Setup (Pin 2 is D4 on Wemos D1 Mini)
led = machine.Pin(2, machine.Pin.OUT)

# Global variable for dynamic publish rate (in milliseconds)
publish_delay = 2000 

def get_system_info():
    # Gather Filesystem stats (index 2 is total blocks, index 3 is free)
    fs_stat = os.statvfs('/')
    
    # Gather OS stats
    uname = os.uname()
    
    # Collect garbage for accurate memory reading
    gc.collect() 
    
    return {
        "sysname": uname.sysname,
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "uniqueId": ubinascii.hexlify(machine.unique_id()).decode(),
    }

# Callback function to handle incoming MQTT messages
def sub_cb(topic, msg):
    global publish_delay
    print("Received message on {}: {}".format(topic, msg))
    
    # Check if the message is for our updateRate topic
    if topic.decode() == TOPIC_SUB_RATE:
        try:
            # Decode bytes to string and convert to integer
            new_rate = int(msg.decode().strip())
            
            # Safety limits: 100ms to 1 hour (3600000ms)
            if 100 <= new_rate <= 3600000:
                publish_delay = new_rate
                print("Publish rate updated to {}ms".format(publish_delay))
            else:
                print("Rate {}ms out of safe bounds (100-3600000)".format(new_rate))
        except ValueError:
            print("Invalid rate received: Not a number")

def main():
    global publish_delay
    
    # Rapid Startup Blink Test
    print("Running startup blink test...")
    for _ in range(5):
        led.value(1) # ON
        utime.sleep(0.1)
        led.value(0) # OFF
        utime.sleep(0.1)

    # Initialize network to fetch IP
    sta_if = network.WLAN(network.STA_IF)
    
    print("Attempting to connect to MQTT Broker at {}:{}...".format(config.MQTT_BROKER, config.MQTT_PORT))
    
    # Define client and set the callback function
    client = MQTTClient(config.CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT, keepalive=60)
    client.set_callback(sub_cb)
    
    try:
        client.connect()
        client.subscribe(TOPIC_SUB_RATE)
        led.value(1)  # Solid OFF to indicate successful connection
        print("Success: Connected and Subscribed to {}".format(TOPIC_SUB_RATE))
    except Exception as e:
        print("Error: Connection failed:", e)
        utime.sleep(10)
        machine.reset()

    last_publish_time = utime.ticks_ms()
    systemData = get_system_info()
    while True:
        try:
            # 1. ALWAYS check for incoming messages from Ignition
            # This now runs every few milliseconds regardless of publish rate
            client.check_msg()

            # 2. Check if it is time to publish yet
            current_time = utime.ticks_ms()
            
            # Use ticks_diff to safely handle timer wraparound
            if utime.ticks_diff(current_time, last_publish_time) >= publish_delay:
                
                gc.collect()
                uptime_sec = utime.ticks_ms()

                payload = {
                    "client_id": config.CLIENT_ID,
                    "uptime": uptime_sec,
                    "ip": sta_if.ifconfig()[0],
                    "rate": publish_delay,
                    "stats": {
                        "free_ram": gc.mem_free(),
                        "flash_id": esp.flash_id(),
                        "cpu_freq": machine.freq()
                    },
                    "system": systemData
                }

                client.publish(TOPIC_PUB, ujson.dumps(payload))
                
                # Heartbeat flash
                led.value(0)
                utime.sleep_ms(20) # Very brief sleep for visual blip
                led.value(1)
                
                print("Published at {}ms: {}".format(publish_delay, uptime_sec))
                
                # Update the timestamp for the next interval
                last_publish_time = utime.ticks_ms()

            # 3. Small "Yield" to prevent CPU 100% lockup and save power
            utime.sleep_ms(10)

        except Exception as e:
            print("Loop Error: {}".format(e))
            utime.sleep(5)
            machine.reset()

# Start the program
if __name__ == "__main__":
    main()
```
</details>

## 5. Pymakr Deployment

1. **Install Extension**: Add the **Pymakr** extension in VS Code.
2. **Add Project**: Navigate to your project folder in the Pymakr panel.
3. **Connect**: Select your **Wemos D1 Mini** from the device list.
4. **Dev Mode**: Click **"Enter Dev Mode"** to enable auto-sync.
5. **Sync**: Pymakr will upload your files (including the `umqtt/` library folder) to the device.
6. **Reset**: Press the physical **Reset** button on the Wemos D1 Mini to begin.

*** ***For addition devices, change the `STATIC_IP` and `CLIENT_ID` in the `config.py` and repeat Step 5***