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