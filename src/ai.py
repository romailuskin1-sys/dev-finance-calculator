from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd

from google import genai


def build_cfo_prompt(
    inputs: Dict[str, Any],
    metrics: Dict[str, Any],
    df: pd.DataFrame,
    head_rows: int = 12,
    tail_rows: int = 12,
) -> str:
    """
    Build a CFO-style prompt using model inputs, computed metrics,
    and a short cashflow preview (head/tail).
    """
    cols = [
        "month",
        "revenue",
        "land_cost",
        "hard_cost",
        "soft_cost",
        "contingency",
        "net_cf_before_finance",
        "cum_cf_before_finance",
        "interest",
        "debt_draw",
        "equity_draw",
        "debt_repay",
        "debt_outstanding",
        "cash_balance",
    ]
    existing_cols = [c for c in cols if c in df.columns]
    preview_head = df[existing_cols].head(head_rows).to_csv(index=False)
    preview_tail = df[existing_cols].tail(tail_rows).to_csv(index=False)

    payload = {
        "inputs": inputs,
        "metrics": metrics,
        "notes": {
            "cashflow_preview": f"head({head_rows}) and tail({tail_rows}) rows only",
            "currency": "EUR",
            "time_unit": "month",
        },
    }

    prompt = f"""
You are the CFO of a real-estate development company.

Your task: review this specific project like an investment committee memo.
Be concise, numeric, and practical. Do NOT repeat the input data back.

Return format (use these exact headings):
1) Verdict (Invest / Rework / Reject) + 1-sentence reason
2) Key risks (max 6 bullets)
3) What to verify (max 6 bullets)
4) Sensitivity guidance (which 2-3 assumptions matter most and why)
5) Action plan (max 5 bullets, concrete next steps)

Data (JSON):
{json.dumps(payload, ensure_ascii=False)}

Cashflow preview (CSV) - first rows:
{preview_head}

Cashflow preview (CSV) - last rows:
{preview_tail}
""".strip()

    return prompt


def run_cfo_review(
    prompt: str,
    api_key: str,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.2,
) -> str:
    """
    Call Gemini and return the CFO review text.
    """
    if not api_key:
        raise ValueError("Missing Gemini API key")

    client = genai.Client(api_key=api_key)

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={"temperature": temperature},
    )
    return resp.text or ""
