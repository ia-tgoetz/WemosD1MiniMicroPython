# config.py
ID = 0 # Change this for each device (0-254) to set unique static IP and client ID
WIFI_SSID = "{your_WIFI_SSID}"
WIFI_PASS = "{your_WIFI_PASS}"
NETWORK_PREFIX = "10.10.1." # Change this to match your network's IP scheme (e.g., 192.168.1.)

# Static IP Settings (IP, Subnet, Gateway, DNS)
STATIC_IP="{0}{1}".format(NETWORK_PREFIX, 19+ID)
SUBNET_MASK="{your_SUBNET_MASK}" #ex. 255.255.255.0
GATEWAY="{your_GATEWAY}" #ex. 192.168.1.1
DNS="{your_DNS}" # 8.8.8.8 (Google) and/or 192.168.1.1
IP_CONFIG = (STATIC_IP, SUBNET_MASK, GATEWAY, DNS)

MQTT_BROKER = "{your_MQTT_BROKER_IP}" 
MQTT_PORT = "{your_MQTT_PORT}" #ex. 1883 is the default
CLIENT_ID = "{your_CLIENT_ID}" #ex. needs to be unique
