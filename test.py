import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# Load your trained model
model = load_model('lstm_auto.h5')

# Simulate temperature data
base_temp = 25  # Base temperature
temperature_diffs = np.arange(-10, 11, 1)  # Simulate temperature differences from -10 to 10 degrees
device_humidity = 0.5  # Example constant humidity value (50%)
climate_temp = 25  # Example constant climate temperature
climate_humidity = 0.5  # Example constant climate humidity (50%)
hour_of_day = 12  # Example constant hour of the day

# Initialize scaler and model
scaler = MinMaxScaler()

# Fit scaler on a typical data sample (this step is crucial for proper scaling)
scaler.fit(np.array([[base_temp, device_humidity, climate_temp, climate_humidity, hour_of_day]]))

# Store results
results = []

for temp_diff in temperature_diffs:
    device_temp = base_temp + temp_diff
    input_data = np.array([[device_temp, device_humidity, climate_temp, climate_humidity, hour_of_day]])
    input_data_scaled = scaler.transform(input_data)
    input_data_scaled = input_data_scaled.reshape((1, 1, input_data_scaled.shape[1]))
    
    # Calculate loss
    prediction = model.predict(input_data_scaled)
    loss = np.mean(np.abs(prediction - input_data_scaled))
    
    results.append((temp_diff, loss))

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
