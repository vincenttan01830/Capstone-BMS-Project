import paho.mqtt.client as mqtt
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
import threading

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_BASE = "zigbee2mqtt/#"  # Subscribe to all topics under zigbee2mqtt

DEVICES_FILE = "devices.json"  # File to save the devices' data

# Function to generate the CSV filename based on the current date and device number
def get_csv_filename(device_number):
    now = datetime.now()
    return f"device_{device_number}_temperature_data_{now.strftime('%Y-%m')}.csv"

# Function to load devices from the JSON file
def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r') as file:
            return json.load(file)
    return {}

# Function to save devices to the JSON file
def save_devices(devices_data):
    with open(DEVICES_FILE, 'w') as file:
        json.dump(devices_data, file, indent=4)

# Initialize dictionaries to store data for each device
devices_data = load_devices()
current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
current_month = datetime.now().month

# Ensure all loaded devices have the necessary keys
for device_name, device_info in devices_data.items():
    if 'hourly' not in device_info:
        device_info['hourly'] = []
    if 'csv_file' not in device_info:
        device_info['csv_file'] = get_csv_filename(device_info['device_number'])

def save_hourly_average(device_name, final_save=False):
    global devices_data, current_hour, current_month
    device_data = devices_data[device_name]
    if device_data['hourly']:
        avg_temperature = round(sum([x['temperature'] for x in device_data['hourly']]) / len(device_data['hourly']), 2)
        avg_humidity = round(sum([x['humidity'] for x in device_data['hourly']]) / len(device_data['hourly']), 2)
    else:
        avg_temperature = None  # No data for this hour
        avg_humidity = None  # No data for this hour
    
    formatted_timestamp = current_hour.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+08:00'
    df = pd.DataFrame([[formatted_timestamp, avg_temperature, avg_humidity]], columns=["time", "device_temperature", "device_humidity"])

    # Generate the current CSV file name
    current_csv_file = device_data['csv_file']

    # Check if the month has changed
    if datetime.now().month != current_month:
        current_csv_file = get_csv_filename(device_data['device_number'])
        device_data['csv_file'] = current_csv_file
        current_month = datetime.now().month

    # Update the existing hour's entry instead of adding a new one
    if os.path.exists(current_csv_file):
        existing_df = pd.read_csv(current_csv_file)
        if not existing_df[existing_df['time'] == formatted_timestamp].empty:
            existing_entry = existing_df[existing_df['time'] == formatted_timestamp].iloc[0]
            new_avg_temperature = round((existing_entry['device_temperature'] * len(device_data['hourly']) + avg_temperature) / (len(device_data['hourly']) + 1), 2)
            new_avg_humidity = round((existing_entry['device_humidity'] * len(device_data['hourly']) + avg_humidity) / (len(device_data['hourly']) + 1), 2)
            existing_df.loc[existing_df['time'] == formatted_timestamp, ['device_temperature', 'device_humidity']] = [new_avg_temperature, new_avg_humidity]
            existing_df.to_csv(current_csv_file, index=False)
        else:
            df.to_csv(current_csv_file, mode='a', header=False, index=False)
    else:
        df.to_csv(current_csv_file, mode='a', header=not os.path.exists(current_csv_file), index=False)

    print(f"Hourly average temperature and humidity data saved to {current_csv_file} for device {device_name}")

def save_all_devices(final_save=False):
    global devices_data
    for device_name in devices_data.keys():
        save_hourly_average(device_name, final_save)
    save_devices(devices_data)  # Save devices data to the JSON file after saving all hourly averages

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(MQTT_TOPIC_BASE)
    else:
        print(f"Failed to connect with result code {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")
        while True:
            try:
                client.reconnect()
                print("Reconnected to MQTT broker.")
                break
            except Exception as e:
                print(f"Reconnection failed: {e}")
                time.sleep(5)  # Wait before retrying

def on_message(client, userdata, msg):
    global devices_data, current_hour
    payload = msg.payload.decode('utf-8')
    topic = msg.topic.split('/')
    device_name = topic[1]  # Assumes topic format is zigbee2mqtt/<device_name>
    print(f"Message received from {device_name}: {payload}")

    # Parse the payload (assuming it's JSON formatted)
    try:
        data = json.loads(payload)
        if 'temperature' in data and 'humidity' in data:
            # Extract temperature, humidity, and current timestamp
            temperature = round(data['temperature'], 2)
            humidity = round(data['humidity'], 2)
            timestamp = datetime.now()

            # Initialize device data if not already present
            if device_name not in devices_data:
                device_number = len(devices_data) + 1
                devices_data[device_name] = {
                    'device_number': device_number,
                    'hourly': [],
                    'csv_file': get_csv_filename(device_number)
                }
                print(f"Device {device_name} has been added with device number {device_number}")
                save_devices(devices_data)  # Save devices data to the JSON file when a new device is added

            device_data = devices_data[device_name]

            print(f"Device {device_data['device_number']} is responding...")

            # Check if the timestamp is past the current hour
            while timestamp >= current_hour + timedelta(hours=1):
                save_hourly_average(device_name)  # Save the data for the current hour
                device_data['hourly'] = []  # Reset the data for the next hour
                current_hour += timedelta(hours=1)  # Move to the next hour

            # Append the current temperature and humidity to the hourly data list
            device_data['hourly'].append({'temperature': temperature, 'humidity': humidity})
    except Exception as e:
        print(f"Error parsing message: {e}")

client = mqtt.Client(client_id="", clean_session=True, userdata=None, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Function to handle shutdown
def shutdown():
    save_all_devices(final_save=True)
    client.loop_stop()
    client.disconnect()
    print("Shutdown complete")

# Try connecting to the MQTT broker
connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        connected = True
    except Exception as e:
        print(f"Connection failed: {e}")
        time.sleep(5)  # Wait before retrying

# Start the MQTT loop
client.loop_start()

# Timer to save data every hour
def hourly_saver():
    while True:
        now = datetime.now()
        # Calculate time to next hour
        seconds_to_next_hour = ((60 - now.minute - 1) * 60) + (60 - now.second)
        time.sleep(seconds_to_next_hour)
        save_all_devices()

# Start the hourly saver in a separate thread
saver_thread = threading.Thread(target=hourly_saver)
saver_thread.daemon = True  # Ensure the thread will close when the main program exits
saver_thread.start()

# Keep the main thread running to handle MQTT messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting program...")
    shutdown()
