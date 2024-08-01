import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import joblib

# Load your trained model and scaler
model = load_model('lstm_model_with_external_variables.h5')
scaler = joblib.load('scaler.pkl')

# Define the feature names used during scaling
feature_names = ['device_temperature', 'device_humidity', 'climate_temperature', 'climate_humidity', 'hour_of_day']

# Function to simulate temperature deviations and calculate loss
def simulate_temp_diff_and_loss(model, scaler, base_temp, temperature_diffs, device_humidity, climate_temp, climate_humidity, hour_of_day):
    results = []
    for temp_diff in temperature_diffs:
        device_temp = base_temp + temp_diff
        input_data = pd.DataFrame([[device_temp, device_humidity, climate_temp, climate_humidity, hour_of_day]], columns=feature_names)
        input_data_scaled = scaler.transform(input_data)
        input_data_scaled = input_data_scaled.reshape((1, 1, input_data_scaled.shape[1]))
        
        # Calculate loss
        prediction = model.predict(input_data_scaled)
        loss = np.mean(np.abs(prediction - input_data_scaled))
        
        results.append((temp_diff, loss))
    return results

# Simulate temperature data
base_temp = 25  # Base temperature
temperature_diffs = np.arange(-10, 11, 1)  # Simulate temperature differences from -10 to 10 degrees
device_humidity = 0.5  # Example constant humidity value (50%)
climate_temp = 25  # Example constant climate temperature
climate_humidity = 0.5  # Example constant climate humidity (50%)
hour_of_day = 12  # Example constant hour of the day

results = simulate_temp_diff_and_loss(model, scaler, base_temp, temperature_diffs, device_humidity, climate_temp, climate_humidity, hour_of_day)

# Convert results to DataFrame for easier plotting
results_df = pd.DataFrame(results, columns=['Temperature Difference', 'Loss'])

# Plot the relationship
plt.figure(figsize=(10, 6))
plt.plot(results_df['Temperature Difference'], results_df['Loss'], marker='o')
plt.title('Temperature Difference vs. Loss')
plt.xlabel('Temperature Difference (°C)')
plt.ylabel('Loss')
plt.grid(True)
plt.show()

# Determine threshold based on acceptable temperature range
acceptable_temp_diff = 5  # Define the acceptable temperature difference
threshold_loss = results_df.loc[results_df['Temperature Difference'].abs() <= acceptable_temp_diff, 'Loss'].max()
print(f"Threshold loss for acceptable temperature difference of {acceptable_temp_diff}°C: {threshold_loss}")
