from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
from datetime import datetime
from model.detector import FraudDetector

app = FastAPI(
    title="FraudShield API",
    description="API de détection de fraude",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = FraudDetector(
    model_path="model/model(1).pkl",
    scaler_path="model/scaler(2).pkl"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class Transaction(BaseModel):
    amount:        float = Field(..., gt=0,       description="Montant")
    hour:          int   = Field(..., ge=0, le=23, description="Heure 0-23")
    merchant_type: str   = Field(...,             description="Type de marchand")
    country:       str   = Field(...,             description="Code pays")
    tx_per_hour:   int   = Field(..., ge=0,       description="Tx par heure")
    is_new_device: int   = Field(..., ge=0, le=1, description="Nouvel appareil 0/1")
    distance_km:   float = Field(..., ge=0,       description="Distance km")
    transaction_id: Optional[str] = None

class PredictionResult(BaseModel):
    transaction_id: Optional[str]
    is_fraud:       bool
    fraud_score:    float
    legit_score:    float
    risk_level:     str
    timestamp:      str
    alert_sent:     bool

alert_log = []

async def send_fraud_alert(transaction_id: str, fraud_score: float, amount: float, country: str):
    await asyncio.sleep(0.1)
    alert = {
        "type": "FRAUD_ALERT",
        "transaction_id": transaction_id,
        "fraud_score": fraud_score,
        "amount": amount,
        "country": country,
        "timestamp": datetime.now().isoformat(),
        "message": f"Transaction suspecte! Score: {fraud_score:.2%}"
    }
    alert_log.append(alert)
    print(f"\n{'='*52}")
    print(f"  ALERTE FRAUDE — {transaction_id}")
    print(f"  Score: {fraud_score:.2%} | Montant: {amount:.2f} | Pays: {country}")
    print(f"{'='*52}\n")

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("static/index.html")

@app.post("/predict", response_model=PredictionResult, tags=["ML"])
async def predict_fraud(transaction: Transaction, background_tasks: BackgroundTasks):
    try:
        data = transaction.model_dump(exclude={"transaction_id"})
        result = detector.predict(data)
        tx_id = transaction.transaction_id or f"TX-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        alert_sent = False
        if result["is_fraud"] and result["fraud_score"] > 0.5:
            background_tasks.add_task(send_fraud_alert, tx_id, result["fraud_score"], transaction.amount, transaction.country)
            alert_sent = True
        return PredictionResult(
            transaction_id=tx_id,
            is_fraud=result["is_fraud"],
            fraud_score=result["fraud_score"],
            legit_score=result["legit_score"],
            risk_level=result["risk_level"],
            timestamp=result["timestamp"],
            alert_sent=alert_sent
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/stats", tags=["Monitoring"])
def get_stats():
    return {"model_stats": detector.stats(), "recent_alerts": alert_log[-10:], "total_alerts": len(alert_log)}

@app.get("/health", tags=["Monitoring"])
def health_check():
    return {"status": "healthy", "model_loaded": detector.model is not None, "model_type": type(detector.model).__name__, "timestamp": datetime.now().isoformat()}

@app.get("/merchant-types", tags=["Reference"])
def get_merchant_types():
    from model.detector import MERCHANT_TYPES, COUNTRIES
    return {"merchant_types": MERCHANT_TYPES, "countries": COUNTRIES}
