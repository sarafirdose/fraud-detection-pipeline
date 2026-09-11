# Live Demonstration Guide & Evaluation Script

Follow this step-by-step guide to demonstrate the **Real-Time Financial Fraud Detection Pipeline** to an evaluation panel or audience.

---

## 1. Quick Start Demonstration (Docker)

To run the entire pipeline with a single command:

```bash
docker compose up --build
```

Access the components:
- **React Dashboard**: http://localhost:3000
- **FastAPI API Documentation**: http://localhost:8000/docs
- **Kafka Broker**: `localhost:9092`
- **MongoDB**: `localhost:27017`

---

## 2. Step-by-Step Local Demonstration (Without Docker)

### Step 1: Start MongoDB & Kafka
Ensure MongoDB is running on port 27017 and Kafka is running on port 9092.

### Step 2: Train the ML Model
```bash
python ml/train.py
```
*Expected Output*: Trains XGBoost classifier with imbalance weighting, displays Precision, Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix, and saves `models/fraud_model.joblib`.

### Step 3: Start the Stream Processor
In Terminal 1:
```bash
python -m streaming.stream_processor
```
*Expected Output*: Connects to Kafka topic `transactions` and MongoDB `fraud_detection`. Actively awaits transactions.

### Step 4: Start the FastAPI Backend
In Terminal 2:
```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```
*Expected Output*: FastAPI starts on `http://localhost:8000`, initializes WebSocket worker, and reports healthy connection.

### Step 5: Start the React Dashboard
In Terminal 3:
```bash
cd frontend
npm run dev
```
*Expected Output*: Vite opens `http://localhost:5173`. Open this URL in your browser.

---

## 3. Demonstration Flow for Evaluation Panel

### A. Show the Live Dashboard
1. Open http://localhost:5173 (or http://localhost:3000 if using Docker).
2. Point out the top header:
   - **Live Stream**: STREAMING (WebSocket connected)
   - **Kafka**: ONLINE
   - **MongoDB**: CONNECTED
   - **ML Engine**: ACTIVE

### B. Start Transaction Streaming
1. In the **Stream Controller** panel, click **Start**.
2. Watch the **Live Transaction Stream** table:
   - Transactions immediately begin arriving in real time.
   - Show the masked account IDs (e.g., `C1***8492`, `M9***2910`).
   - Show the sub-millisecond ML processing latency and risk score bar.
3. Adjust the **Speed Slider** from 5 TPS to 20 TPS and observe the throughput increase.

### C. Show Real-Time Fraud Interception
1. As high-risk PaySim transactions pass through, they are flagged in real time.
2. Watch the **Active Fraud Alerts** panel update instantly.
3. Click on any alert or transaction to open the **Deep Forensic Investigation Modal**:
   - Point out the **ML Risk Verdict** (CRITICAL / HIGH / MEDIUM / LOW).
   - Point out the **Identified Anomaly Factors** (e.g. "Complete origin account balance drain", "Large transaction amount exceeding threshold", "High-risk transaction type: TRANSFER").
   - Point out the **PaySim Double-Entry Ledger Analysis** showing initial balance, amount sent, final balance, and mathematical balance delta error.

### D. Demonstrate "Inject Demo Fraud"
1. In the Stream Controller, select `TRANSFER (Account Drain)` and click **INJECT DEMO FRAUD**.
2. Explain to the panel:
   > *"This button does NOT insert fake data into the UI. It sends an intentionally suspicious transaction event to Kafka's `transactions` topic. The streaming processor picks it up, extracts the 18 PaySim features, runs the XGBoost model, scores the anomaly, updates MongoDB, and pushes the alert through the WebSocket to our dashboard."*
3. Observe the `DEMO` badge transaction flash with `CRITICAL (98%)` risk and immediately appear in the **Active Fraud Alerts** panel.

### E. Show Analytics & ML Model Diagnostics
1. Click the **Fraud Analytics & Trends** tab:
   - Show the Donut chart (Fraud vs Normal class distribution).
   - Show the Area chart (Transaction volume and fraud rate over time).
   - Show the Risk Tier Distribution and Transaction Type Breakdown.
2. Click the **ML Model Diagnostics** tab:
   - Explain the Confusion Matrix (Low False Negatives on imbalanced classes).
   - Explain the High Recall (Fraud Sensitivity), ROC-AUC, and PR-AUC.
   - Show the learned Feature Importance rankings (`errorBalanceOrig`, `log_amount`, etc.).

### F. Show In-Page Prometheus & Grafana Telemetry
1. Click **Prometheus** in the top navbar:
   - Shows the live in-page parsed metric registry from `GET /metrics` (throughput, latency, error rates).
2. Click **Grafana** in the top navbar:
   - Shows the visual SOC telemetry modal with real-time latency area charts and service health indicators.
