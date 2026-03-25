# StockSense AI 🇮🇳📈
### ET AI Hackathon 2026 — PS 6: AI for the Indian Investor

**Participant:** Divija Panchal (Individual)

> India has 14 crore+ demat accounts. Most retail investors are flying blind — reacting to tips, missing filings, unable to read technicals. StockSense AI is the intelligence layer that turns raw market data into actionable, plain-English signals.

---

## What it does

StockSense AI is a two-feature multi-agent platform:

### 1. Opportunity Radar
Continuously monitors SEBI filings, bulk/block deal disclosures, insider trades, and management commentary. Surfaces missed signals as prioritized daily alerts with LLM-generated plain-English explanations and source citations.

**Sample alert:**
> "Promoter of Tata Motors bought shares worth ₹12.3 Cr on March 24 — the 3rd consecutive insider buy this quarter. In the previous two similar sequences, the stock rose 9.2% and 11.4% within 30 days. Signal strength: HIGH."

### 2. Chart Pattern Intelligence
Real-time ML-based technical pattern detection across the full NSE 500 universe — breakouts, RSI divergences, MA crossovers, volume-price divergences — with back-tested historical success rates per pattern per stock.

---

## Architecture

```
Data Sources (NSE/BSE, SEBI, screener.in)
        │
        ▼
┌─────────────────────┐
│   Ingestion Agent   │  ← Fetches, cleans, stores OHLCV + filings
└─────────┬───────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
┌──────────┐  ┌───────────────────┐
│ Opportunity│  │ Chart Pattern     │
│  Radar    │  │ Agent (ML/TA-Lib) │
│  Agent    │  └────────┬──────────┘
└─────┬─────┘           │
      └────────┬─────────┘
               ▼
     ┌─────────────────────┐
     │  LLM Reasoning Agent │  ← Claude Sonnet + RAG
     │  (Claude API)        │
     └──────────┬───────────┘
                ▼
     ┌─────────────────────┐
     │  Alert Delivery      │  ← Redis pub/sub → WebSocket
     └──────────┬───────────┘
                ▼
     ┌─────────────────────┐
     │  Investor Dashboard  │  ← React + Recharts
     └─────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data ingestion | `yfinance`, `jugaad-data`, NSE India API, `BeautifulSoup` |
| Signal detection | `TA-Lib`, `pandas-ta`, `scikit-learn`, `PyTorch` (LSTM) |
| LLM reasoning | Claude API (Sonnet), `LangChain` / `LangGraph` |
| Vector storage | `ChromaDB` |
| Database | PostgreSQL (timeseries), Redis (alerts) |
| Backend API | `FastAPI`, WebSocket |
| Frontend | React, Recharts, TailwindCSS |

---

## Project Structure

```
stocksense-ai/
├── agents/
│   ├── ingestion_agent.py       # Data fetching & normalization
│   ├── opportunity_radar.py     # Insider trade & filing anomaly detection
│   ├── chart_pattern_agent.py   # ML-based technical pattern detection
│   ├── llm_reasoning_agent.py   # Claude API + RAG summarization
│   └── alert_delivery_agent.py  # Redis pub/sub alert dispatch
├── ml/
│   ├── pattern_classifier.py    # LSTM pattern classification model
│   ├── train.py                 # Model training script
│   └── backtest/
│       └── backtest_engine.py   # Historical hit rate computation
├── api/
│   ├── main.py                  # FastAPI app entry point
│   ├── routes/
│   │   ├── signals.py           # Signal feed endpoints
│   │   └── chat.py              # Conversational query endpoint
│   └── websocket.py             # Live alert streaming
├── data/
│   ├── raw/                     # Raw fetched data (gitignored)
│   └── processed/               # Cleaned, normalized data
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── SignalFeed.jsx    # Live alert feed
│       │   ├── StockChart.jsx   # Chart with pattern overlays
│       │   └── ChatBox.jsx      # Conversational interface
│       └── index.css
├── scripts/
│   └── seed_data.py             # Seed historical data for demo
├── docs/
│   └── architecture.md          # Detailed architecture notes
├── .env.example
├── requirements.txt
├── package.json
└── README.md
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis

### 1. Clone the repo
```bash
git clone https://github.com/divijapanchal/stocksense-ai.git
cd stocksense-ai
```

### 2. Set up Python environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Fill in your API keys (see .env.example)
```

### 4. Seed historical data
```bash
python scripts/seed_data.py
```

### 5. Start the backend
```bash
uvicorn api.main:app --reload
```

### 6. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to see the dashboard.

---

## Demo

A 3-4 minute demo video is included in the submission covering:
1. Opportunity Radar — live signal card with insider trade alert
2. Chart Pattern Intelligence — breakout detection with back-tested hit rates
3. Chat interface — natural language query ("Why is Tata Motors flagged today?")

---

## Impact

| Metric | Before | After |
|--------|--------|-------|
| Signal discovery time | 2-3 hours manual | < 2 minutes |
| Stocks monitored | ~30 | Full NSE 500 |
| Insider trade alerts | Missed / delayed | Real-time, ranked |
| Retail investor access | Paid advisors only | Free, self-serve |

---

## Submission

- **Hackathon:** ET Gen AI Hackathon 2026 — Phase 2: Build Sprint
- **Problem Statement:** PS 6 — AI for the Indian Investor
- **Platform:** Unstop | Partner: Avataar.ai
- **Participant:** Divija Panchal (Individual)
