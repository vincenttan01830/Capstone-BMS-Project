import pandas as pd
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Load datasets
device_temp_data = pd.read_csv('generate_data/device_1_temperature_data_2024-07.csv')
filtered_data = pd.read_csv('generate_data/generated_data.csv')

# Create a feature for the temperature difference
device_temp_data['temp_difference'] = device_temp_data['climate_temperature'] - device_temp_data['device_temperature']
filtered_data['temp_difference'] = filtered_data['climate_temperature'] - filtered_data['device_temperature']

# Prepare the data for modeling
X = device_temp_data[['device_temperature', 'climate_temperature', 'climate_humidity', 'temp_difference']]
y = device_temp_data['device_humidity']

# Standardize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Build the neural network model
model = Sequential([
    Dense(64, activation='relu', input_shape=(X_scaled.shape[1],)),
    Dense(32, activation='relu'),
    Dense(1)
])

# Compile the model
model.compile(optimizer='adam', loss='mse')

# Train the model
model.fit(X_scaled, y, epochs=100, batch_size=32, validation_split=0.2)

# Standardize the features for the filtered data
filtered_data_features = filtered_data[['device_temperature', 'climate_temperature', 'climate_humidity', 'temp_difference']]
filtered_data_scaled = scaler.transform(filtered_data_features)

# Predict device humidity
filtered_data['device_humidity'] = model.predict(filtered_data_scaled).flatten()

# Scale predictions to be in the range 0 to 1
filtered_data['device_humidity'] /= 100

# Round to 2 decimal places
filtered_data['device_humidity'] = filtered_data['device_humidity'].round(2)

# Save the updated filtered data with predicted device humidity
filtered_data.to_csv('generate_data/filtered_device_climate_data_with_corrected_humidity.csv', index=False)

print("Prediction and file saving completed successfully.")
