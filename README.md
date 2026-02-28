# Development Finance Calculator

## Overview

This project is an interactive Streamlit dashboard that models a real-estate development deal on a monthly timeline. I built it to feel like a lightweight decision-support tool a finance analyst could use for quick screening, scenario testing, and liquidity checks. Instead of a static spreadsheet, it recalculates immediately when assumptions change, so you can see how profitability and risk respond to different prices, costs, timelines, and financing terms.

## Features

- **Monthly cash-flow modeling** with realistic S-curve construction spend
- **Debt/equity financing** and liquidity simulation
- **AI CFO Review** via the Gemini API to generate a short investment-committee style risk memo

## Project Structure

### `app.py`
The Streamlit entry point that handles the user interface. It defines the sidebar controls, builds the inputs dictionary, calls the finance model to generate the cashflow table, calls the metrics function to compute KPIs, and renders the results. It also wires up the “AI CFO Review” button, which builds a prompt from the model outputs and displays the returned memo.

### `src/model.py`
Contains the deterministic finance model and KPI calculations. The `cashflow(inputs)` function builds a monthly table with revenue, land cost, construction costs (S-curve), soft costs, contingency, and the resulting cash flow before financing. It then simulates financing with equity draws, debt draws, interest, and repayment, producing a complete “after financing” view of liquidity. This file also includes `compute_metrics(df, inputs)`, which calculates project-level profitability and risk indicators, including NPV (discounted monthly cash flows), annualized IRR, ROI, payback month, peak cash need, maximum debt outstanding, total interest, equity invested, and ending cash balance.

### `src/charts.py`
Contains the Plotly chart functions. Each function takes the cashflow dataframe and returns a Plotly figure for Streamlit to display. The main charts are cumulative cash flow (with the payback point), debt outstanding over time, cash balance over time, and an optional revenue vs monthly costs chart.

### `src/ai.py`
Handles the Gemini API integration. It builds a CFO-style prompt using the current input assumptions, computed metrics, and a short preview of the cashflow and sends it to Gemini via the Google GenAI SDK.

### `src/init.py`
Exists to make the `src` folder importable as a Python package, allowing clean imports like `from src.model import cashflow`.

## Design Choices and Trade-offs

A major design decision was to use a monthly timeline and a simplified S-curve rather than a detailed construction schedule. Monthly periods are a good balance between realism and complexity: they capture liquidity stress and interest accumulation without requiring an overly detailed schedule. The 20/60/20 S-curve is intentionally simple but produces more realistic cost timing than flat spending.

Another choice was to include financing and repayment rather than only computing unlevered project metrics. In development deals, “peak cash need” and “maximum debt” are often as important as IRR. Adding debt/equity draws, interest, and repayment makes the model more realistic and creates a more informative dashboard.

For AI integration, I chose a CFO memo style rather than a general chat. The goal is to generate a consistent decision-ready review (verdict, risks, what to verify, and actions) instead of open-ended conversation. The app remains fully functional without AI; the AI review is optional and does not affect calculations.

## Running the Project

1. Install dependencies from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

2. Run the app:
    ```bash
    streamlit run app.py
    ```

3. Enter your **Gemini API key** in the sidebar to use the “AI CFO Review”.
