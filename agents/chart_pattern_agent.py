"""
Chart Pattern Agent
Detects technical patterns across NSE stocks using TA-Lib indicators.
Returns ranked watchlist with pattern descriptions and back-test metadata.
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from loguru import logger


@dataclass
class PatternSignal:
    symbol: str
    pattern: str
    description: str
    confidence: float       # 0.0 - 1.0
    current_price: float
    signal_direction: str   # "BULLISH" or "BEARISH"
    backtest_hit_rate: float   # historical success rate
    backtest_avg_return: float # avg % return after pattern
    backtest_samples: int


def detect_rsi_divergence(df: pd.DataFrame) -> bool:
    """Detect bullish RSI divergence (price lower low, RSI higher low)."""
    if len(df) < 30:
        return False
    try:
        close = df["Close"].values
        delta = pd.Series(close).diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))

        price_recent_low = close[-5:].min()
        price_prev_low = close[-20:-10].min()
        rsi_recent_low = rsi.values[-5:].min()
        rsi_prev_low = rsi.values[-20:-10].min()

        return (price_recent_low < price_prev_low) and (rsi_recent_low > rsi_prev_low)
    except Exception:
        return False


def detect_breakout(df: pd.DataFrame, lookback: int = 52) -> bool:
    """Detect price breakout above 52-week resistance."""
    if len(df) < lookback:
        return False
    try:
        recent_close = df["Close"].iloc[-1]
        resistance = df["High"].iloc[-lookback:-1].max()
        avg_volume = df["Volume"].iloc[-20:-1].mean()
        current_volume = df["Volume"].iloc[-1]
        return (recent_close > resistance * 0.99) and (current_volume > avg_volume * 1.3)
    except Exception:
        return False


def detect_golden_cross(df: pd.DataFrame) -> bool:
    """Detect 50-day MA crossing above 200-day MA."""
    if len(df) < 200:
        return False
    try:
        ma50 = df["Close"].rolling(50).mean()
        ma200 = df["Close"].rolling(200).mean()
        return (ma50.iloc[-1] > ma200.iloc[-1]) and (ma50.iloc[-3] <= ma200.iloc[-3])
    except Exception:
        return False


def mock_backtest(pattern: str, symbol: str) -> tuple[float, float, int]:
    """
    Mock back-test results for demo purposes.
    In production: query PostgreSQL for historical pattern occurrences.
    Returns: (hit_rate, avg_return_pct, sample_count)
    """
    backtest_db = {
        "RSI_DIVERGENCE": (0.64, 7.2, 14),
        "BREAKOUT":       (0.71, 9.8, 23),
        "GOLDEN_CROSS":   (0.68, 11.3, 9),
    }
    return backtest_db.get(pattern, (0.55, 5.0, 5))


def scan_stock(symbol: str, df: pd.DataFrame) -> list[PatternSignal]:
    """Run all pattern detectors on a single stock's price data."""
    signals = []
    current_price = df["Close"].iloc[-1] if not df.empty else 0.0

    if detect_breakout(df):
        hit_rate, avg_return, samples = mock_backtest("BREAKOUT", symbol)
        signals.append(PatternSignal(
            symbol=symbol,
            pattern="BREAKOUT",
            description=f"Price breaking above 52-week high with +30% volume surge",
            confidence=0.78,
            current_price=current_price,
            signal_direction="BULLISH",
            backtest_hit_rate=hit_rate,
            backtest_avg_return=avg_return,
            backtest_samples=samples
        ))

    if detect_rsi_divergence(df):
        hit_rate, avg_return, samples = mock_backtest("RSI_DIVERGENCE", symbol)
        signals.append(PatternSignal(
            symbol=symbol,
            pattern="RSI_DIVERGENCE",
            description="Bullish RSI divergence: price made lower low but RSI made higher low",
            confidence=0.65,
            current_price=current_price,
            signal_direction="BULLISH",
            backtest_hit_rate=hit_rate,
            backtest_avg_return=avg_return,
            backtest_samples=samples
        ))

    if detect_golden_cross(df):
        hit_rate, avg_return, samples = mock_backtest("GOLDEN_CROSS", symbol)
        signals.append(PatternSignal(
            symbol=symbol,
            pattern="GOLDEN_CROSS",
            description="50-day MA crossed above 200-day MA (Golden Cross)",
            confidence=0.72,
            current_price=current_price,
            signal_direction="BULLISH",
            backtest_hit_rate=hit_rate,
            backtest_avg_return=avg_return,
            backtest_samples=samples
        ))

    return signals


def run_pattern_scan(prices_csv: str = "data/processed/prices.csv") -> list[PatternSignal]:
    """Scan all stocks in the prices dataset for patterns."""
    try:
        df_all = pd.read_csv(prices_csv)
    except FileNotFoundError:
        logger.error("prices.csv not found — run ingestion_agent.py first")
        return []

    all_signals = []
    for symbol, group in df_all.groupby("symbol"):
        group = group.sort_values("Date").reset_index(drop=True)
        signals = scan_stock(symbol, group)
        all_signals.extend(signals)

    all_signals.sort(key=lambda s: s.confidence, reverse=True)
    logger.info(f"Pattern scan complete: {len(all_signals)} signals found across {df_all['symbol'].nunique()} stocks")
    return all_signals


if __name__ == "__main__":
    signals = run_pattern_scan()
    for s in signals:
        print(f"[{s.signal_direction}] {s.symbol} — {s.pattern}: {s.description}")
        print(f"   Back-test: {s.backtest_hit_rate*100:.0f}% hit rate over {s.backtest_samples} occurrences, avg return +{s.backtest_avg_return:.1f}%\n")
