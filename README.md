# 🛡️ FraudShield — Real-Time Financial Fraud Detection System

> A full-stack machine learning system that detects fraudulent financial transactions in real time, powered by a trained Random Forest model, a FastAPI REST backend, and an interactive web dashboard.

---

## 📁 Project Structure

```
FraudShield/
├── model/
│   ├── detector.py                # FraudDetector class (preprocessing + inference)
│   ├── fraud_dataset(1).csv       # Labeled transaction dataset
│   ├── model(1).pkl               # Trained Random Forest classifier
│   ├── scaler(2).pkl              # StandardScaler for numeric features
│   ├── encoder_country(1).pkl     # LabelEncoder for the `country` feature
│   └── encoder_merchant(1).pkl    # LabelEncoder for the `merchant_type` feature
├── static/
│   ├── index.html                 # Single-page web application
│   ├── style.css                  # Dark-theme stylesheet
│   └── app.js                     # Frontend logic (API calls, charts, simulation)
├── main.py                        # FastAPI application entry point
├── requirements.txt               # Pinned Python dependencies
└── .gitignore
```

---

## ⚙️ Features

- 🔍 **Real-time fraud scoring** — each transaction is analyzed in under 50 ms
- 📊 **3-tier risk classification** — LOW / MEDIUM / HIGH based on fraud probability
- 🚨 **Automatic fraud alerting** — background alert dispatched on detected fraud
- 📋 **Transaction history** — last 50 analyzed transactions tracked in-session
- 📈 **Live statistics** — fraud rate, alert count, risk distribution bar chart
- 🔌 **Graceful degradation** — local heuristic simulation when API is offline

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/0Rekhami/FraudShield.git
cd FraudShield
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open the dashboard

Go to [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Score a transaction and return fraud probability + risk level |
| `GET` | `/health` | Check API and model status |
| `GET` | `/stats` | Session statistics and recent fraud alerts |
| `GET` | `/merchant-types` | List allowed merchant types and country codes |
| `GET` | `/` | Serve the web dashboard |

### Example — POST `/predict`

**Request:**
```json
{
  "amount": 850.00,
  "hour": 2,
  "merchant_type": "crypto",
  "country": "MA",
  "tx_per_hour": 7,
  "is_new_device": 1,
  "distance_km": 320.5
}
```

**Response:**
```json
{
  "transaction_id": "TX-20250518143201123456",
  "is_fraud": true,
  "fraud_score": 0.8921,
  "legit_score": 0.1079,
  "risk_level": "HIGH",
  "timestamp": "2025-05-18T14:32:01.123456",
  "alert_sent": true
}
```

---

## 🧠 Machine Learning Pipeline

| Step | Tool | Details |
|------|------|---------|
| Categorical encoding | `LabelEncoder` | `merchant_type` and `country` → integer codes |
| Numerical scaling | `StandardScaler` | All 7 features normalized to zero mean / unit variance |
| Classification | `RandomForestClassifier` | Trained with `class_weight='balanced'` to handle class imbalance |
| Serialization | `joblib` | Model + 3 preprocessing artifacts saved as `.pkl` files |

**Input features:** `amount`, `hour`, `merchant_type`, `country`, `tx_per_hour`, `is_new_device`, `distance_km`

**Decision thresholds:**

| Fraud score | `is_fraud` | `risk_level` |
|-------------|------------|--------------|
| > 0.75 | ✅ True | 🔴 HIGH |
| 0.50 – 0.75 | ✅ True | 🟠 MEDIUM |
| 0.40 – 0.50 | ❌ False | 🟠 MEDIUM |
| ≤ 0.40 | ❌ False | 🟢 LOW |

---

## 🗂️ Dataset

The dataset (`fraud_dataset(1).csv`) contains labeled financial transactions with 7 input features and a binary `is_fraud` target variable. It covers 11 countries and 6 merchant categories.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| ML model | scikit-learn (Random Forest) |
| API backend | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Serialization | joblib + numpy |
| Frontend | HTML / CSS / JavaScript (no framework) |
| Fonts | Syne + DM Mono (Google Fonts) |

---

## 📦 Requirements

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
scikit-learn==1.5.2
joblib==1.4.2
numpy==1.26.4
python-multipart==0.0.12
```

> ⚠️ The `scikit-learn` version must match the version used to train the model. Using a different version may cause deserialization errors when loading the `.pkl` files.

---

## 👥 Authors

| Name | GitHub |
|------|--------|
| **Rekhami Abdessamad** |
| **Fatima Tildi** |
| **Ichraq Majid** |

---
