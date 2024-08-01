import paho.mqtt.client as mqtt
import json

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
DEVICE_TOPIC = "zigbee2mqtt/0xa4c1383628a7fd0c"  # Replace with your device's topic

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Define the payload with the temperature spike
spike_message = {
    "co2": 359,
    "formaldehyd": 0,
    "humidity": 62.6,
    "linkquality": 255,
    "pm25": 24,
    "temperature": 99,  # Temperature spike to 50 degrees
    "voc": 8
}

# Publish the message to the device topic
client.publish(DEVICE_TOPIC, json.dumps(spike_message))

# Disconnect from the MQTT broker
client.disconnect()

print(f"Injected spike message to {DEVICE_TOPIC}")
