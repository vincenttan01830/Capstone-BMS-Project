import paho.mqtt.client as mqtt
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
import threading
from get_climate_data import fetch_climate_data  # Import the climate data function

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_BASE = "zigbee2mqtt/#"  # Subscribe to all topics under zigbee2mqtt

DEVICES_FILE = "devices.json"  # File to save the devices' data

# OpenWeatherMap settings
API_KEY = "446e884fa8fcaf1e943c89605dac07e5"  # Replace with your OpenWeatherMap API key
LAT = 1.38  # Replace with your latitude
LON = 103.85  # Replace with your longitude

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

# Initialize dictionaries to store data for each device and climate
devices_data = load_devices()
climate_data = []
current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
current_month = datetime.now().month
last_save_time = datetime.now()

# Ensure all loaded devices have the necessary keys
for device_name, device_info in devices_data.items():
    if 'hourly' not in device_info:
        device_info['hourly'] = []
    if 'csv_file' not in device_info:
        device_info['csv_file'] = get_csv_filename(device_info['device_number'])

def save_hourly_average(device_name, final_save=False):
    global devices_data, current_hour, current_month, climate_data
    print(f"Saving hourly average for {device_name}...")
    device_data = devices_data[device_name]
    # Filter out None values before calculating averages
    hourly_temps = [x['temperature'] for x in device_data['hourly'] if x['temperature'] is not None]
    hourly_hums = [x['humidity'] for x in device_data['hourly'] if x['humidity'] is not None]
    
    if not hourly_temps and not hourly_hums:
        print(f"No data to save for {device_name} in the current hour. Skipping save.")
        return  # Skip save if no data for the current hour

    if hourly_temps:
        avg_temperature = round(sum(hourly_temps) / len(hourly_temps), 2)
    else:
        avg_temperature = None  # No data for this hour
    
    if hourly_hums:
        avg_humidity = round(sum(hourly_hums) / len(hourly_hums), 2)
    else:
        avg_humidity = None  # No data for this hour

    if climate_data:
        climate_temps = [x['temperature'] for x in climate_data if x['temperature'] is not None]
        climate_hums = [x['humidity'] for x in climate_data if x['humidity'] is not None]
        if climate_temps:
            avg_climate_temperature = round(sum(climate_temps) / len(climate_temps), 2)
        else:
            avg_climate_temperature = None  # No climate data for this hour
        
        if climate_hums:
            avg_climate_humidity = round(sum(climate_hums) / len(climate_hums), 2)
        else:
            avg_climate_humidity = None  # No climate data for this hour
    else:
        avg_climate_temperature = None  # No climate data for this hour
        avg_climate_humidity = None  # No climate data for this hour

    formatted_timestamp = current_hour.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+08:00'
    df = pd.DataFrame([[formatted_timestamp, avg_temperature, avg_humidity, avg_climate_temperature, avg_climate_humidity]], 
                      columns=["time", "device_temperature", "device_humidity", "climate_temperature", "climate_humidity"])

    # Generate the current CSV file name
    current_csv_file = device_data['csv_file']
    print(f"Current CSV file: {current_csv_file}")

    # Check if the month has changed
    if datetime.now().month != current_month:
        current_csv_file = get_csv_filename(device_data['device_number'])
        device_data['csv_file'] = current_csv_file
        current_month = datetime.now().month

    # Update the existing hour's entry instead of adding a new one
    if os.path.exists(current_csv_file):
        print(f"CSV file {current_csv_file} exists. Updating entry if necessary.")
        existing_df = pd.read_csv(current_csv_file)
        if not existing_df[existing_df['time'] == formatted_timestamp].empty:
            print(f"Entry for {formatted_timestamp} exists. Updating entry.")
            existing_entry = existing_df[existing_df['time'] == formatted_timestamp].iloc[0]
            # Update the existing average values
            if avg_temperature is not None and existing_entry['device_temperature'] is not None:
                new_avg_temperature = round((existing_entry['device_temperature'] * len(hourly_temps) + avg_temperature) / (len(hourly_temps) + 1), 2)
            else:
                new_avg_temperature = avg_temperature
            
            if avg_humidity is not None and existing_entry['device_humidity'] is not None:
                new_avg_humidity = round((existing_entry['device_humidity'] * len(hourly_hums) + avg_humidity) / (len(hourly_hums) + 1), 2)
            else:
                new_avg_humidity = avg_humidity
            
            existing_df.loc[existing_df['time'] == formatted_timestamp, 
                            ['device_temperature', 'device_humidity', 'climate_temperature', 'climate_humidity']] = [new_avg_temperature or existing_entry['device_temperature'],
                                                                                                                   new_avg_humidity or existing_entry['device_humidity'],
                                                                                                                   avg_climate_temperature or existing_entry['climate_temperature'],
                                                                                                                   avg_climate_humidity or existing_entry['climate_humidity']]
            existing_df.to_csv(current_csv_file, index=False)
        else:
            print(f"Adding new entry for {formatted_timestamp}.")
            df.to_csv(current_csv_file, mode='a', header=False, index=False)
    else:
        print(f"CSV file {current_csv_file} does not exist. Creating new file and adding entry.")
        df.to_csv(current_csv_file, mode='a', header=not os.path.exists(current_csv_file), index=False)

    print(f"Hourly average temperature and humidity data saved to {current_csv_file} for device {device_name}")
    device_data['hourly'].clear()  # Clear the hourly data after saving

def save_all_devices(final_save=False, force_save=False):
    global devices_data, last_save_time, climate_data
    now = datetime.now()
    if (now - last_save_time).seconds < 3600 and not final_save and not force_save:
        print("Skipping save: Less than an hour since last save and not final save or force save.")
        return  # Avoid multiple saves within the same hour unless forced

    print("Saving data for all devices...")
    print(f"Current devices_data: {devices_data}")
    for device_name in devices_data.keys():
        print(f"Saving data for device {device_name}...")
        save_hourly_average(device_name, final_save)
    save_devices(devices_data)  # Save devices data to the JSON file after saving all hourly averages
    climate_data.clear()  # Clear climate data after saving
    last_save_time = now
    print("Data saved successfully.")

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
    
    # Check if the topic is a device topic (not the bridge)
    if device_name != 'bridge':
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

                print(f"Device {device_data['device_number']} is responding")

                # Check if the timestamp is past the current hour
                while timestamp >= current_hour + timedelta(hours=1):
                    save_all_devices(force_save=True)  # Save the data for all devices for the current hour
                    current_hour += timedelta(hours=1)  # Move to the next hour

                # Append the current temperature and humidity to the hourly data list
                device_data['hourly'].append({'temperature': temperature, 'humidity': humidity})
        except Exception as e:
            print(f"Error parsing message from {device_name}: {e}")

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
        seconds_to_next_hour = (60 - now.minute) * 60 - now.second
        time.sleep(seconds_to_next_hour)
        save_all_devices(force_save=True)  # Force save to ensure data is saved at the hour mark

# Start the hourly saver in a separate thread
saver_thread = threading.Thread(target=hourly_saver)
saver_thread.daemon = True  # Ensure the thread will close when the main program exits
saver_thread.start()

# Fetch climate data every 3 minutes
def climate_fetcher():
    global climate_data
    while True:
        climate_temperature, climate_humidity = fetch_climate_data(API_KEY, LAT, LON)
        if climate_temperature is not None and climate_humidity is not None:
            climate_data.append({'temperature': climate_temperature, 'humidity': climate_humidity})
            print(f"Successfully fetched climate data: Temperature={climate_temperature}, Humidity={climate_humidity}")
        else:
            print("Error fetching climate data")
        time.sleep(180)  # Fetch climate data every 3 minutes (180 seconds)

# Start the climate fetcher in a separate thread
climate_thread = threading.Thread(target=climate_fetcher)
climate_thread.daemon = True  # Ensure the thread will close when the main program exits
climate_thread.start()

# Function to fetch and save climate data when Enter is pressed
def fetch_and_save():
    global climate_data
    print("Fetching climate data...")
    climate_temperature, climate_humidity = fetch_climate_data(API_KEY, LAT, LON)
    if climate_temperature is not None and climate_humidity is not None:
        climate_data.append({'temperature': climate_temperature, 'humidity': climate_humidity})
        print(f"Successfully fetched climate data: Temperature={climate_temperature}, Humidity={climate_humidity}")
    else:
        print("Error fetching climate data")
    print("Saving data for all devices after fetching climate data...")
    save_all_devices(force_save=True)
    print("Manual save completed.")

# Keep the main thread running to handle MQTT messages
try:
    while True:
        if input() == "":
            fetch_and_save()
except KeyboardInterrupt:
    print("\nExiting program...")
    shutdown()
