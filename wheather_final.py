import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

# -------- Step 1: Build API URL --------
API_KEY = "696f8e98034b2643edce7087c497d50a"  # Replace with your OpenWeatherMap API key
CITY = "Bangalore"  # Change to your city
url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric"

# -------- Step 2: Fetch Data --------
try:
    response = requests.get(url)
    response.raise_for_status()  # Check for HTTP errors
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from API: {e}")
    exit()

# -------- Step 3: Convert JSON to DataFrame --------
if "list" not in data:
    print("Error: 'list' key not found in API response. Please check API key or city name.")
    exit()

rows = []
for entry in data["list"]:
    rows.append({
        "time": entry["dt_txt"],
        "temp": entry["main"]["temp"],
        "humidity": entry["main"]["humidity"],
        "pressure": entry["main"]["pressure"],
        "wind_speed": entry["wind"]["speed"],
        "clouds": entry["clouds"]["all"]
    })

df = pd.DataFrame(rows)

# -------- Step 4: Feature Engineering --------
df["time"] = pd.to_datetime(df["time"])
df["hour"] = df["time"].dt.hour
df["dayofweek"] = df["time"].dt.dayofweek
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

# -------- Step 5: Prepare Training Data --------
features = ["humidity", "pressure", "wind_speed", "clouds", "hour_sin", "hour_cos"]
X = df[features]
y = df["temp"]

# -------- Step 6: Train ML Model --------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Print model performance
print("Model R^2 Score on Test Set:", model.score(X_test, y_test))

# -------- Step 7: Save Model --------
joblib.dump(model, "weather_model.pkl")
print("Model saved as weather_model.pkl")

# -------- Step 8: Load Model and Predict on New Forecast --------
loaded_model = joblib.load("weather_model.pkl")
print("Loaded model successfully.")

# Use the same features for predictions
X_new = df[features]
predictions = loaded_model.predict(X_new)

# Add predicted temperatures to DataFrame
df["predicted_temp"] = predictions

# -------- Step 9: Define Status Based on Future Conditions --------
# Define status based on predicted temperature and humidity
def assign_status(row):
    temp = row["predicted_temp"]
    humidity = row["humidity"]
    if temp > 35 or humidity > 80:
        return "Extreme"
    elif temp > 28 or humidity > 60:
        return "Moderate"
    else:
        return "Mild"

df["status"] = df.apply(assign_status, axis=1)

# -------- Step 10: Display Results --------
print("\nWeather Forecast with Predictions and Status:")
print(df[["time", "temp", "predicted_temp", "humidity", "status"]].head(10))

# -------- Step 11: Save Results to CSV --------
df.to_csv("weather_forecast_with_status.csv", index=False)
print("Results saved to weather_forecast_with_status.csv")