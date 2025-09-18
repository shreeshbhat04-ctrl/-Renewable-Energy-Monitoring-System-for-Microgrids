# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import joblib
import numpy as np
import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "models/rf_model.joblib"
model = None

def generate_synthetic(n_samples=5000, seed=42):
    np.random.seed(seed)
    voltage = np.random.normal(400, 10, n_samples)
    current = np.random.normal(55, 10, n_samples)
    power = voltage * current / 1000.0
    temperature = np.random.normal(30, 5, n_samples)
    status = np.where(
        (voltage < 390) | (voltage > 410) |
        (temperature > 37) | (current > 70),
        "Unstable", "Stable"
    )
    df = pd.DataFrame({
        "Voltage": voltage,
        "Current": current,
        "Power": power,
        "Battery_Temperature": temperature,
        "Grid_Status": status
    })
    return df

def train_and_save_model(from_csv_path=None):
    if from_csv_path and os.path.exists(from_csv_path):
        df = pd.read_csv(from_csv_path)
        label_col = None
        for c in ["Grid_Status", "Status", "label", "target"]:
            if c in df.columns:
                label_col = c
                break
        if label_col is None:
            raise RuntimeError("CSV found but no label column. Expect Grid_Status / Status / label / target.")
    else:
        df = generate_synthetic()
        label_col = "Grid_Status"

    X = df[["Voltage", "Current", "Power", "Battery_Temperature"]]
    y = df[label_col]

    model_local = RandomForestClassifier(n_estimators=100, random_state=42)
    model_local.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model_local, MODEL_PATH)
    return model_local

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    if not os.path.exists(MODEL_PATH):
        print("No model file found — training model at startup...")
        model = train_and_save_model()  # uses synthetic if no CSV
        print("Model trained and saved.")
    else:
        model = joblib.load(MODEL_PATH)
        print("Loaded model from disk.")
    yield
    print("Shutting down...")

app = FastAPI(title="Microgrid Stability API", version="1.0", lifespan=lifespan)

class PredictRequest(BaseModel):
    Voltage: float
    Current: float
    Power: float
    Battery_Temperature: float

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

@app.post("/predict")
def predict(request: PredictRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    features = pd.DataFrame([[
        request.Voltage,
        request.Current,
        request.Power,
        request.Battery_Temperature
    ]], columns=["Voltage", "Current", "Power", "Battery_Temperature"])

    pred = model.predict(features)[0]
    probs = model.predict_proba(features)[0]
    prob_map = {cls: float(probs[i]) for i, cls in enumerate(model.classes_)}

    return {
        "predicted_grid_status": pred,
        "probability_stable": prob_map.get("Stable", 0.0),
        "probability_unstable": prob_map.get("Unstable", 0.0),
        "input_data": {
            "Voltage": request.Voltage,
            "Current": request.Current,
            "Power": request.Power,
            "Battery_Temperature": request.Battery_Temperature
        }
    }

# Optional retrain endpoint
@app.post("/retrain")
def retrain(use_csv: bool = False):
    """
    Trigger retraining from dataset.csv if use_csv=True and file exists,
    otherwise trains with synthetic data.
    """
    global model
    model = train_and_save_model(from_csv_path="dataset.csv" if use_csv else None)
    return {"status": "retrained", "model_path": MODEL_PATH}