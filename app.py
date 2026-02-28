import streamlit as st
from src.model import cashflow, compute_metrics
from src.charts import fig_cum_cf, fig_debt, fig_cash, fig_revenue_vs_costs
from src.ai import build_cfo_prompt, run_cfo_review



st.set_page_config(page_title="Dev Finance Calculator", layout="wide")
st.title("Development Finance Calculator")

with st.sidebar:
    st.header("AI CFO Review")
    gemini_api_key = st.text_input("Gemini API key", type="password")

    st.header("Project")
    months = st.slider("Project duration (months)", 6, 72, 36)
    start_sales_month = st.slider("Sales start month", 1, months, 18)
    sellable_area_m2 = st.number_input("Sellable area (m²)", min_value=100.0, value=10000.0, step=100.0)
    sales_m2_per_month = st.number_input("Sales speed (m²/month)", min_value=10.0, value=400.0, step=10.0)

    st.header("Revenue")
    sell_price_per_m2 = st.number_input("Sell price (€/m²)", min_value=100.0, value=3500.0, step=50.0)

    st.header("Costs")
    land_cost = st.number_input("Land cost (€)", min_value=0.0, value=2_000_000.0, step=50_000.0)
    build_cost_per_m2 = st.number_input("Build cost (€/m²)", min_value=100.0, value=1800.0, step=50.0)
    soft_cost_pct = st.slider("Soft costs (%)", 0.0, 25.0, 10.0) / 100.0
    contingency_pct = st.slider("Contingency (%)", 0.0, 20.0, 7.0) / 100.0

    st.header("Finance")
    equity_share = st.slider("Equity share of deficit (%)", 0.0, 100.0, 40.0) / 100.0
    debt_rate_annual = st.slider("Debt interest (annual %)", 0.0, 20.0, 8.0) / 100.0

    st.header("Discounting")
    discount_rate_annual = st.slider("Discount rate (annual %)", 0.0, 25.0, 10.0) / 100.0

    st.header("Scenario")
    downside_mode = st.checkbox("Downside mode", value=False)
    price_shock_pct = st.slider("Price shock (%)", -30.0, 0.0, -5.0) / 100.0
    cost_shock_pct = st.slider("Cost shock (%)", 0.0, 30.0, 10.0) / 100.0
    delay_months = st.slider("Delay (months)", 0, 12, 3)

inputs = {
    "months": months,
    "start_sales_month": start_sales_month,
    "sellable_area_m2": sellable_area_m2,
    "sales_m2_per_month": sales_m2_per_month,
    "sell_price_per_m2": sell_price_per_m2,
    "land_cost": land_cost,
    "build_cost_per_m2": build_cost_per_m2,
    "soft_cost_pct": soft_cost_pct,
    "contingency_pct": contingency_pct,
    "equity_share": equity_share,
    "debt_rate_annual": debt_rate_annual,
    "discount_rate_annual": discount_rate_annual,
    "downside_mode": downside_mode,
    "price_shock_pct": price_shock_pct,
    "cost_shock_pct": cost_shock_pct,
    "delay_months": delay_months,
}

df = cashflow(inputs)
metrics = compute_metrics(df, inputs)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Project NPV (€)", f"{metrics['npv_project']:,.0f}")
c2.metric("Project IRR (annual)", "n/a" if metrics["irr_annual"] is None else f"{metrics['irr_annual']*100:.2f}%")
c3.metric("Project ROI", "n/a" if metrics["roi"] is None else f"{metrics['roi']*100:.1f}%")
c4.metric("Payback", "n/a" if metrics["payback_month"] is None else f"{metrics['payback_month']} mo")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Max debt (€)", f"{metrics['max_debt']:,.0f}")
c6.metric("Peak cash need (€)", f"{metrics['peak_cash_need']:,.0f}")
c7.metric("Total interest paid (€)", f"{metrics['total_interest']:,.0f}")
c8.metric("Ending cash (retained, not distributed)", f"{metrics['ending_cash']:,.0f}")

st.plotly_chart(fig_cum_cf(df, metrics["payback_month"]), use_container_width=True)

colA, colB = st.columns(2)
with colA:
    st.plotly_chart(fig_debt(df), use_container_width=True)
with colB:
    st.plotly_chart(fig_cash(df), use_container_width=True)

with st.expander("Revenue vs Costs (optional chart)"):
    st.plotly_chart(fig_revenue_vs_costs(df), use_container_width=True)

with st.expander("Cashflow table"):
    st.dataframe(df, use_container_width=True)

st.subheader("AI CFO Review")

if "cfo_review" not in st.session_state:
    st.session_state.cfo_review = ""

if st.button("Run AI CFO Review"):
    try:
        prompt = build_cfo_prompt(inputs, metrics, df)
        st.session_state.cfo_review = run_cfo_review(
            prompt=prompt,
            api_key=gemini_api_key,
        )
    except Exception as e:
        st.error(f"AI error: {e}")

if st.session_state.cfo_review:
    st.write(st.session_state.cfo_review)
