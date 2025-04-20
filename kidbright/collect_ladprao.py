from machine import Pin
from machine import Pin,I2C,ADC,UART
import time,math,network,json,dht

from umqtt.robust import MQTTClient
from config import (
    WIFI_SSID, WIFI_PASS,
    MQTT_BROKER, MQTT_USER, MQTT_PASS
)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)
while not wlan.isconnected():
    time.sleep(0.5)
mqtt = MQTTClient(client_id="",
                  server=MQTT_BROKER,
                  user=MQTT_USER,
                  password=MQTT_PASS)
mqtt.connect()
# Initialize the DHT11 sensor on Pin 5
dht_sensor = dht.DHT11(Pin(32, Pin.IN, Pin.PULL_UP))

def read_sensor():
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        print("Sensor data read successfully.")
        return temp, hum
    except Exception as e:
        print("Failed to read sensor data:", e)
        return None, None

# Main loop
while True:
    temperature, humidity = read_sensor()
    if temperature is not None and humidity is not None:
        print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
    else:
        print("Failed to read sensor data. Retrying...")
    data = {
        'latitude':13.7993271,
        'longitude':100.6258821,
        'temperature':temperature,
        'humiduty':humidity}
    mqtt.publish('b6610545545/kidbright',json.dumps(data))
    print("Data published:", data)
    time.sleep(600)