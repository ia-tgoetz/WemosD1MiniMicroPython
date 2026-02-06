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