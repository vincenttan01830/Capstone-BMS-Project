import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, RepeatVector, TimeDistributed, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Load the dataset
file_path = 'baseline_data.csv'
df = pd.read_csv(file_path, parse_dates=['time'], index_col='time')

# Feature engineering
df['hour_of_day'] = df.index.hour

# Check for missing values and fill if any
df.fillna(method='ffill', inplace=True)

# Normalize the data
scaler = MinMaxScaler()
df[['device_temperature', 'device_humidity', 'climate_temperature', 'climate_humidity', 'hour_of_day']] = scaler.fit_transform(
    df[['device_temperature', 'device_humidity', 'climate_temperature', 'climate_humidity', 'hour_of_day']]
)

# Save the scaler
joblib.dump(scaler, 'scaler.pkl')

# Add synthetic anomalies
def add_synthetic_anomalies(df, anomaly_fraction=0.1, seed=42):
    np.random.seed(seed)
    df_with_anomalies = df.copy()
    num_anomalies = int(len(df) * anomaly_fraction)
    anomaly_indices = np.random.choice(df.index, num_anomalies, replace=False)
    df_with_anomalies.loc[anomaly_indices, 'device_temperature'] += np.random.normal(5, 2, size=num_anomalies)
    df_with_anomalies['label'] = 1
    df_with_anomalies.loc[anomaly_indices, 'label'] = -1
    return df_with_anomalies

# Add synthetic anomalies
df_with_anomalies = add_synthetic_anomalies(df)

# Split the data
train_size = int(len(df_with_anomalies) * 0.8)
train, test = np.split(df_with_anomalies, [train_size])
val_size = int(len(train) * 0.2)
train, val = np.split(train, [len(train) - val_size])

# Function to prepare data and train the model
def train_and_save_model(features, train, val, test):
    X_train = train[features].values.reshape((train.shape[0], 1, len(features)))
    X_val = val[features].values.reshape((val.shape[0], 1, len(features)))
    X_test = test[features].values.reshape((test.shape[0], 1, len(features)))

    model = Sequential([
        LSTM(64, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True),
        Dropout(0.2),
        LSTM(32, activation='relu', return_sequences=False),
        RepeatVector(X_train.shape[1]),
        LSTM(32, activation='relu', return_sequences=True),
        Dropout(0.2),
        LSTM(16, activation='relu', return_sequences=True),
        TimeDistributed(Dense(X_train.shape[2]))
    ])

    optimizer = Adam(learning_rate=0.0005)
    model.compile(optimizer=optimizer, loss='mse')

    early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    history = model.fit(X_train, X_train, epochs=20, batch_size=64, validation_data=(X_val, X_val), callbacks=[early_stopping])

    # Save the model
    model.save('lstm_model_with_external_variables.h5')

    return model, history

# Train and save the model with external variables
features_with_external = ['device_temperature', 'device_humidity', 'climate_temperature', 'climate_humidity', 'hour_of_day']
model_with_external, history_with_external = train_and_save_model(features_with_external, train, val, test)

# Print the model summary
print(model_with_external.summary())
