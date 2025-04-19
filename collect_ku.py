from machine import Pin
import dht
import time
import network
import json
from umqtt.robust import MQTTClient
from config import WIFI_SSID, WIFI_PASS, MQTT_BROKER, MQTT_USER, MQTT_PASS
import _thread

# Initialize the DHT11 sensor on Pin 32
dht_sensor = dht.DHT11(Pin(32, Pin.IN, Pin.PULL_UP))

led_wifi = Pin(2, Pin.OUT)
led_wifi.value(1)  # turn the red led off
led_iot = Pin(12, Pin.OUT)
led_iot.value(1)   # turn the green led off


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)
while not wlan.isconnected():
    time.sleep(0.5)
led_wifi.value(0)  # turn the red led on


mqtt = MQTTClient(client_id="",
                  server=MQTT_BROKER,
                  user=MQTT_USER,
                  password=MQTT_PASS)
mqtt.connect()
led_iot.value(0)   # turn the green led on

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

while True:
    temperature, humidity = read_sensor()
    
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "lat": 13.8460934,
        "lon": 100.5686036
        
    }
    if temperature is not None and humidity is not None:
        print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
    else:
        print("Failed to read sensor data. Retrying...")
    
    # Wait for  600 seconds before the next reading
    mqtt.publish("b6610545863/kidbright", json.dumps(data))
    time.sleep(600) 