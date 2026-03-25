"""
Opportunity Radar Agent
Scores insider trades and bulk deals, detects anomalies,
and routes high-confidence signals to the LLM reasoning agent.
"""
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class Signal:
    symbol: str
    signal_type: str        # "INSIDER_BUY", "BULK_DEAL", "PROMOTER_BUY"
    strength: str           # "HIGH", "MEDIUM", "LOW"
    score: float            # 0.0 - 1.0
    summary: str
    raw_data: dict
    consecutive_count: Optional[int] = None
    historical_return_avg: Optional[float] = None


def score_insider_trade(row: dict) -> float:
    """
    Score an insider trade based on:
    - Designation weight (Chairman > Director > Employee)
    - Transaction size
    - Consecutive buy streak
    """
    score = 0.0

    designation_weights = {
        "Chairman": 0.4, "MD": 0.35, "CEO": 0.35,
        "CFO": 0.25, "Director": 0.2, "Employee": 0.1
    }
    score += designation_weights.get(row.get("designation", ""), 0.1)

    value_cr = row.get("value_cr", 0)
    if value_cr > 50:
        score += 0.35
    elif value_cr > 20:
        score += 0.25
    elif value_cr > 5:
        score += 0.15
    else:
        score += 0.05

    consecutive = row.get("consecutive_buys", 1)
    score += min(consecutive * 0.08, 0.25)

    return min(score, 1.0)


def score_bulk_deal(row: dict) -> float:
    """Score a bulk/block deal."""
    score = 0.0

    category_weights = {"PROMOTER": 0.4, "FII": 0.3, "MF": 0.25, "OTHER": 0.1}
    score += category_weights.get(row.get("category", "OTHER"), 0.1)

    value_cr = row.get("value_cr", 0)
    if value_cr > 100:
        score += 0.4
    elif value_cr > 50:
        score += 0.3
    elif value_cr > 20:
        score += 0.2
    else:
        score += 0.1

    if row.get("deal_type") == "BUY":
        score += 0.2

    return min(score, 1.0)


def strength_from_score(score: float) -> str:
    if score >= 0.65:
        return "HIGH"
    elif score >= 0.4:
        return "MEDIUM"
    return "LOW"


def detect_signals(
    insider_trades: pd.DataFrame,
    bulk_deals: pd.DataFrame,
    min_score: float = 0.3
) -> list[Signal]:
    """Run the full signal detection pipeline."""
    signals = []

    for _, row in insider_trades.iterrows():
        if row.get("transaction_type") != "BUY":
            continue
        score = score_insider_trade(row.to_dict())
        if score < min_score:
            continue

        consecutive = row.get("consecutive_buys", 1)
        summary = (
            f"{row['person_name']} ({row['designation']}) of {row['symbol']} "
            f"bought ₹{row['value_cr']:.1f} Cr worth of shares"
        )
        if consecutive > 1:
            summary += f" — {consecutive} consecutive insider buys this quarter"

        signals.append(Signal(
            symbol=row["symbol"],
            signal_type="INSIDER_BUY",
            strength=strength_from_score(score),
            score=round(score, 2),
            summary=summary,
            raw_data=row.to_dict(),
            consecutive_count=int(consecutive)
        ))

    for _, row in bulk_deals.iterrows():
        if row.get("deal_type") != "BUY":
            continue
        score = score_bulk_deal(row.to_dict())
        if score < min_score:
            continue

        signals.append(Signal(
            symbol=row["symbol"],
            signal_type="BULK_DEAL",
            strength=strength_from_score(score),
            score=round(score, 2),
            summary=(
                f"{row['client_name']} ({row['category']}) bought "
                f"₹{row['value_cr']:.1f} Cr of {row['symbol']} at ₹{row['price']:.1f}"
            ),
            raw_data=row.to_dict()
        ))

    signals.sort(key=lambda s: s.score, reverse=True)
    logger.info(f"Detected {len(signals)} signals (min_score={min_score})")
    return signals


if __name__ == "__main__":
    insider_df = pd.read_csv("data/processed/insider_trades.csv")
    bulk_df = pd.read_csv("data/processed/bulk_deals.csv")
    signals = detect_signals(insider_df, bulk_df)
    for s in signals:
        print(f"[{s.strength}] {s.symbol} — {s.summary} (score: {s.score})")
