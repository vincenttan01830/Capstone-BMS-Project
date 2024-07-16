import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Load the dataset
file_path = 'baseline_data.csv'
data = pd.read_csv(file_path)

# Ensure the dataset is clean and structured correctly
# (Additional data cleaning steps can be added here if necessary)

# Define features (X) and target (y)
X = data[['climate_temperature', 'climate_humidity', 'device_humidity']]
y = data['device_temperature']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Data preparation completed successfully.")

# Initialize the model
model = LinearRegression()

# Train the model
model.fit(X_train, y_train)

# Predict on the test set
y_pred = model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Model Evaluation:\nMean Squared Error: {mse}\nR-squared: {r2}")

# Calculate residuals (difference between actual and predicted values)
residuals = np.abs(y_test - y_pred)

# Define a threshold for anomalies (e.g., residuals greater than a certain value)
threshold = 1.0  # Adjust this value based on your criteria

# Identify anomalies
anomalies = residuals > threshold
anomalous_data = X_test[anomalies]

print("Anomalous data points:\n", anomalous_data)

# Save the anomalies to a CSV file
anomalous_data.to_csv('anomalous_data.csv', index=False)
print("Anomalous data points saved successfully.")
