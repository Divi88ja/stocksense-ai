"""
LLM Reasoning Agent
Uses Claude API to generate plain-English signal summaries
with historical context and source citations.
"""
import os
import anthropic
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


SYSTEM_PROMPT = """You are StockSense AI, an intelligent signal analyst for Indian retail investors.

Your job is to take raw market signal data (insider trades, bulk deals, chart patterns) and generate
a clear, actionable alert in plain English.

Your response must follow this exact structure:
- SIGNAL SUMMARY (1-2 sentences, plain English)
- WHY IT MATTERS (2-3 sentences explaining significance)
- HISTORICAL CONTEXT (what happened in similar past situations for this stock)
- RISK FACTORS (1-2 honest cautions)
- SIGNAL STRENGTH: HIGH / MEDIUM / LOW
- SUGGESTED WATCHLIST ACTION: Add to watchlist / Monitor closely / Low priority

Always be honest. Never make guarantees. Always mention that this is not financial advice.
Keep the tone confident but balanced. Write for a first-time investor who is intelligent but not a finance expert.
"""


def generate_signal_alert(signal_data: dict, historical_context: str = "") -> str:
    """
    Generate a plain-English alert for a detected signal.
    
    Args:
        signal_data: dict with keys: symbol, signal_type, summary, score, raw_data
        historical_context: optional string with past price behaviour context
    
    Returns:
        Formatted alert string
    """
    user_message = f"""
Generate a signal alert for the following market event:

SIGNAL TYPE: {signal_data.get('signal_type')}
STOCK: {signal_data.get('symbol')}
RAW SIGNAL: {signal_data.get('summary')}
SCORE: {signal_data.get('score')} out of 1.0

HISTORICAL CONTEXT PROVIDED:
{historical_context if historical_context else "No historical context available. Use general knowledge about this type of signal."}

Generate the alert now.
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        alert_text = response.content[0].text
        logger.info(f"Generated alert for {signal_data.get('symbol')}")
        return alert_text

    except Exception as e:
        logger.error(f"LLM reasoning failed: {e}")
        return f"Signal detected: {signal_data.get('summary')} (LLM summary unavailable)"


def answer_investor_question(question: str, context_signals: list[dict]) -> str:
    """
    Answer a natural language question from an investor
    using the current signal context.
    
    Args:
        question: investor's question (e.g. "Why is Tata Motors flagged today?")
        context_signals: list of current signal dicts for relevant stocks
    
    Returns:
        Plain-English answer
    """
    context_str = "\n".join([
        f"- {s.get('symbol')}: {s.get('summary')} (score: {s.get('score')})"
        for s in context_signals
    ])

    user_message = f"""
An investor is asking: "{question}"

Current signals in the system:
{context_str if context_str else "No signals currently active."}

Answer their question clearly and helpfully. Reference specific signals where relevant.
Always end with a reminder that this is not financial advice.
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    except Exception as e:
        logger.error(f"Chat response failed: {e}")
        return "Sorry, I couldn't process your question right now. Please try again."


if __name__ == "__main__":
    sample_signal = {
        "symbol": "TATAMOTORS",
        "signal_type": "INSIDER_BUY",
        "summary": "Chairman N. Chandrasekaran bought ₹9.48 Cr of TATAMOTORS — 3rd consecutive insider buy this quarter",
        "score": 0.82
    }

    historical = "In Q2 2023 (similar 3-buy streak), TATAMOTORS rose 9.2% in 30 days. In Q4 2022, it rose 11.4%."

    alert = generate_signal_alert(sample_signal, historical)
    print("\n=== GENERATED ALERT ===")
    print(alert)
