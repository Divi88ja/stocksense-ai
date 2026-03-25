"""
StockSense AI — FastAPI Backend
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
from loguru import logger

from agents.ingestion_agent import fetch_bulk_deals, fetch_insider_trades
from agents.opportunity_radar import detect_signals
from agents.chart_pattern_agent import run_pattern_scan
from agents.llm_reasoning_agent import generate_signal_alert, answer_investor_question

app = FastAPI(title="StockSense AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {"status": "StockSense AI is running"}


@app.get("/api/signals")
def get_signals():
    """Return all current opportunity radar signals."""
    try:
        insider_df = fetch_insider_trades()
        bulk_df = fetch_bulk_deals()
        signals = detect_signals(insider_df, bulk_df, min_score=0.3)

        result = []
        for s in signals:
            result.append({
                "symbol": s.symbol,
                "signal_type": s.signal_type,
                "strength": s.strength,
                "score": s.score,
                "summary": s.summary,
                "consecutive_count": s.consecutive_count,
            })
        return {"signals": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        return {"signals": [], "count": 0, "error": str(e)}


@app.get("/api/signals/{symbol}/alert")
def get_signal_alert(symbol: str):
    """Get LLM-generated alert for a specific symbol."""
    try:
        insider_df = fetch_insider_trades()
        bulk_df = fetch_bulk_deals()
        signals = detect_signals(insider_df, bulk_df, min_score=0.0)

        match = next((s for s in signals if s.symbol.upper() == symbol.upper()), None)
        if not match:
            return {"error": f"No signal found for {symbol}"}

        signal_dict = {
            "symbol": match.symbol,
            "signal_type": match.signal_type,
            "summary": match.summary,
            "score": match.score,
        }
        alert = generate_signal_alert(signal_dict)
        return {"symbol": symbol, "alert": alert}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/patterns")
def get_patterns():
    """Return chart pattern signals across NSE 500."""
    try:
        signals = run_pattern_scan()
        result = [
            {
                "symbol": s.symbol,
                "pattern": s.pattern,
                "description": s.description,
                "confidence": s.confidence,
                "current_price": s.current_price,
                "signal_direction": s.signal_direction,
                "backtest_hit_rate": s.backtest_hit_rate,
                "backtest_avg_return": s.backtest_avg_return,
                "backtest_samples": s.backtest_samples,
            }
            for s in signals
        ]
        return {"patterns": result, "count": len(result)}
    except Exception as e:
        return {"patterns": [], "count": 0, "error": str(e)}


@app.post("/api/chat")
def chat(request: ChatRequest):
    """Answer investor questions using current signal context."""
    try:
        insider_df = fetch_insider_trades()
        bulk_df = fetch_bulk_deals()
        signals = detect_signals(insider_df, bulk_df, min_score=0.3)
        context = [{"symbol": s.symbol, "summary": s.summary, "score": s.score} for s in signals]
        answer = answer_investor_question(request.question, context)
        return {"question": request.question, "answer": answer}
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Stream live alerts over WebSocket."""
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            insider_df = fetch_insider_trades()
            bulk_df = fetch_bulk_deals()
            signals = detect_signals(insider_df, bulk_df, min_score=0.5)
            if signals:
                top = signals[0]
                await websocket.send_text(json.dumps({
                    "type": "NEW_SIGNAL",
                    "symbol": top.symbol,
                    "strength": top.strength,
                    "summary": top.summary,
                    "score": top.score,
                }))
            await asyncio.sleep(60)
    except Exception:
        logger.info("WebSocket client disconnected")
