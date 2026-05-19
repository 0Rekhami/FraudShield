import joblib
import numpy as np
import os
from functools import wraps
from datetime import datetime
from typing import Optional

MERCHANT_TYPES = ["online_retail", "restaurant", "transfer", "crypto", "travel", "retail"]
COUNTRIES = ["BD", "CA", "IT", "PH", "US", "VN", "MA", "RO", "ES", "DE", "GB"]

def log_prediction(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start = datetime.now()
        result = func(self, *args, **kwargs)
        elapsed = (datetime.now() - start).total_seconds() * 1000
        label = "FRAUD" if result["is_fraud"] else "LEGIT"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {label} | score={result['fraud_score']:.4f} | {elapsed:.1f}ms")
        return result
    return wrapper

def validate_transaction(func):
    @wraps(func)
    def wrapper(self, data: dict):
        required = ["amount", "hour", "merchant_type", "country", "tx_per_hour", "is_new_device", "distance_km"]
        for field in required:
            if field not in data:
                raise ValueError(f"Champ manquant: {field}")
        if not (0 <= data["hour"] <= 23):
            raise ValueError("Heure invalide (0-23)")
        if data["amount"] <= 0:
            raise ValueError("Montant doit être positif")
        if data["merchant_type"] not in MERCHANT_TYPES:
            raise ValueError(f"merchant_type invalide. Options: {MERCHANT_TYPES}")
        return func(self, data)
    return wrapper

class FraudDetector:
    def __init__(
        self,
        model_path: str = "model/model(1).pkl",
        scaler_path: str = "model/scaler(2).pkl",
        encoder_country_path: str = "model/encoder_country(1).pkl",
        encoder_merchant_path: str = "model/encoder_merchant(1).pkl"
    ):
        self.model = self._load(model_path)
        self.scaler = self._load(scaler_path)
        self.encoder_country = self._load(encoder_country_path)
        self.encoder_merchant = self._load(encoder_merchant_path)

        self.prediction_count = 0
        self.fraud_count = 0

    def _load(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fichier introuvable: {path}")
        return joblib.load(path)

    def _encode(self, data: dict) -> np.ndarray:
        merchant_enc = self.merchant_map.get(data["merchant_type"], -1)
        country_enc = self.country_map.get(data["country"], -1)
        features = np.array([[
            data["amount"],
            data["hour"],
            merchant_enc,
            country_enc,
            data["tx_per_hour"],
            data["is_new_device"],
            data["distance_km"]
        ]])
        if self.scaler:
            features = self.scaler.transform(features)
        return features

    @validate_transaction
    @log_prediction
    def predict(self, data: dict) -> dict:
        features = self._encode(data)
        prediction = int(self.model.predict(features)[0])
        proba = self.model.predict_proba(features)[0]
        fraud_score = float(proba[1])
        self.prediction_count += 1
        if prediction == 1:
            self.fraud_count += 1
        risk_level = "HIGH" if fraud_score > 0.75 else "MEDIUM" if fraud_score > 0.4 else "LOW"
        return {
            "is_fraud": bool(prediction),
            "fraud_score": round(fraud_score, 4),
            "legit_score": round(float(proba[0]), 4),
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
            "total_predictions": self.prediction_count,
            "fraud_rate": round(self.fraud_count / self.prediction_count, 4) if self.prediction_count > 0 else 0
        }

    def stats(self) -> dict:
        return {
            "total_predictions": self.prediction_count,
            "fraud_detected": self.fraud_count,
            "fraud_rate": round(self.fraud_count / self.prediction_count, 4) if self.prediction_count > 0 else 0,
            "model_type": type(self.model).__name__
        }
