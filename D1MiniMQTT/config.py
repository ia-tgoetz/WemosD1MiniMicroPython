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