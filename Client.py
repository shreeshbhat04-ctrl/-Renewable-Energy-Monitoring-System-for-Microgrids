//Establishes connection b/w Blynk & Ml server
# predict_client.py
import requests
import argparse

API_URL = "http://127.0.0.1:8000/predict"

parser = argparse.ArgumentParser()
parser.add_argument("--voltage", type=float, default=400.0)
parser.add_argument("--current", type=float, default=55.0)
parser.add_argument("--power", type=float, default=None)  # if not given computed
parser.add_argument("--temp", type=float, default=30.0)
args = parser.parse_args()

avg_voltage = args.voltage
power = args.power if args.power is not None else avg_voltage * args.current / 1000.0

payload = {
    "Voltage": float(avg_voltage),
    "Current": float(args.current),
    "Power": float(power),
    "Battery_Temperature": float(args.temp)
}

print("Sending payload:", payload)
resp = requests.post(API_URL, json=payload, timeout=5)
if resp.status_code == 200:
    print("Response:", resp.json())
else:
    print("Error:", resp.status_code, resp.text)
