import paho.mqtt.client as mqtt
import time
import json
import random
from datetime import datetime

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Define constant device IDs
device_ids = ["0xa4c1383628a7c", "0xb4c13936281d"]

# Function to publish messages
def publish_message(device_name):
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Simulated data
    data = {
        "co2": random.randint(400, 1000),
        "formaldehyd": random.randint(10, 100),
        "humidity": round(random.uniform(30, 60), 1),
        "linkquality": 255,
        "pm25": random.randint(0, 50),
        "temperature": round(random.uniform(20, 30), 1),
        "voc": random.randint(100, 500)
    }
    
    payload = json.dumps(data)
    topic = f"zigbee2mqtt/{device_name}"
    
    # Get the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Print the log message
    print(f"[{timestamp}] info:     z2m:mqtt: MQTT publish: topic '{topic}', payload '{payload}'")
    
    # Publish the message
    client.publish(topic, payload)
    client.disconnect()

# Simulate devices
while True:
    for device_id in device_ids:
        publish_message(device_id)
    time.sleep(5)  # Publish every 5 seconds
