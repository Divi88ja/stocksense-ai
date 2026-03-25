# StockSense AI — Architecture Document

## Agent Roles

| Agent | Trigger | Output |
|-------|---------|--------|
| Ingestion Agent | Scheduled (every 15 min / hourly) | Cleaned OHLCV + filing CSVs, vector embeddings |
| Opportunity Radar | New filing event / batch run | Scored Signal objects |
| Chart Pattern Agent | 30-min price update cycle | PatternSignal objects |
| LLM Reasoning Agent | High-confidence signal routed | Plain-English alert with citations |
| Alert Delivery Agent | New LLM alert | Redis pub/sub → WebSocket push |

## Data Flow

```
NSE/BSE prices (yfinance)  ──┐
SEBI filings (scraper)      ──┤──► Ingestion Agent ──► PostgreSQL + ChromaDB
Screener.in (API)           ──┘
                                          │
                          ┌───────────────┴───────────────┐
                          ▼                               ▼
               Opportunity Radar Agent        Chart Pattern Agent
               (anomaly scoring)              (TA-Lib + LSTM)
                          │                               │
                          └───────────────┬───────────────┘
                                          ▼
                               LLM Reasoning Agent
                               (Claude Sonnet + RAG)
                                          │
                               Alert Delivery Agent
                               (Redis → WebSocket)
                                          │
                               Investor Dashboard
                               (React + Recharts)
```

## Error Handling

- All agents wrapped in try/except with loguru logging
- Ingestion failures skip the symbol and continue (no full pipeline crash)
- LLM failures fall back to raw signal summary
- WebSocket disconnects handled gracefully

## Scalability Notes

- Ingestion agent is stateless — can be parallelized with `multiprocessing.Pool`
- ChromaDB can be swapped for Pinecone for production scale
- FastAPI + uvicorn supports async workers for concurrent requests
- Redis pub/sub decouples alert generation from frontend delivery
