import paho.mqtt.client as mqtt
import tensorflow as tf
import numpy as np
import json
import logging
import joblib
import pandas as pd
from datetime import datetime, timedelta
import time
from get_climate_data import fetch_climate_data  # Import the climate data fetching function

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load your trained model and scaler
model = tf.keras.models.load_model('lstm_model_with_external_variables.h5')
scaler = joblib.load('scaler.pkl')

# Manually set the threshold for now
best_threshold = 0.35

# Define the feature names used during scaling
feature_names = ['device_temperature', 'device_humidity', 'climate_temperature', 'climate_humidity', 'hour_of_day']

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_BASE = "zigbee2mqtt/#"  # Subscribe to all topics under zigbee2mqtt

# OpenWeatherMap settings
API_KEY = "446e884fa8fcaf1e943c89605dac07e5" 
LAT = 1.38  
LON = 103.85  

# Global variables to cache weather data
cached_climate_temp = None
cached_climate_humidity = None
last_weather_update = datetime.min

def fetch_and_cache_climate_data():
    global cached_climate_temp, cached_climate_humidity, last_weather_update
    now = datetime.now()
    if now - last_weather_update > timedelta(minutes=10):
        climate_temp, climate_humidity = fetch_climate_data(API_KEY, LAT, LON)
        if climate_temp is not None and climate_humidity is not None:
            cached_climate_temp = round(climate_temp, 2)
            cached_climate_humidity = round(climate_humidity / 100, 2) 
            last_weather_update = now
            logging.info("Weather data updated")
        else:
            logging.error("Failed to fetch climate data")
    return cached_climate_temp, cached_climate_humidity

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(MQTT_TOPIC_BASE)
    else:
        logging.info(f"Failed to connect with result code {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.info("Unexpected disconnection. Attempting to reconnect...")
        while True:
            try:
                client.reconnect()
                logging.info("Reconnected to MQTT broker.")
                break
            except Exception as e:
                logging.info(f"Reconnection failed: {e}")
                time.sleep(5) 

def on_message(client, userdata, msg):
    global feature_names
    if "bridge/logging" not in msg.topic:
        logging.info(f"Received message on {msg.topic}")
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            
            if 'temperature' in data and 'humidity' in data:
                # Extract device temperature and humidity
                device_temp = round(data['temperature'], 2)
                device_humidity = round(data['humidity'] / 100, 2) 
                
                # Fetch cached climate data
                climate_temp, climate_humidity = fetch_and_cache_climate_data()
                
                if climate_temp is None or climate_humidity is None:
                    logging.error("Using last known climate data as fallback.")
                    climate_temp = cached_climate_temp
                    climate_humidity = cached_climate_humidity
                
                hour_of_day = datetime.now().hour

                # Create input data with proper feature names
                input_data = pd.DataFrame([[device_temp, device_humidity, climate_temp, climate_humidity, hour_of_day]], columns=feature_names)
                input_data_scaled = scaler.transform(input_data)
                input_data_scaled = input_data_scaled.reshape((1, 1, input_data_scaled.shape[1]))

                # Perform anomaly detection
                prediction = model.predict(input_data_scaled)
                loss = np.mean(np.abs(prediction - input_data_scaled))

                logging.info(f"Calculated loss: {loss}")
                is_anomaly = loss > best_threshold

                if is_anomaly:
                    logging.info(f"Anomaly detected: {is_anomaly}, Loss: {loss}")
                else:
                    logging.info("Ping: No anomaly detected")

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
        except KeyError as e:
            logging.error(f"Missing expected data in JSON: {e}")

# Initialize MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Function to handle shutdown
def shutdown():
    client.loop_stop()
    client.disconnect()
    logging.info("Shutdown complete")

# Try connecting to the MQTT broker
connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        connected = True
    except Exception as e:
        logging.info(f"Connection failed: {e}")
        time.sleep(5) 

# Start the MQTT loop
client.loop_start()

# Keep the main thread running to handle MQTT messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("\nExiting program...")
    shutdown()
