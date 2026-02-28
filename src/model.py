import pandas as pd
import numpy as np
import numpy_financial as nf



inputs = {
    "months": 36,
    "start_sales_month": 18,
    "sellable_area_m2": 10000.0,
    "sales_m2_per_month": 400.0,
    "sell_price_per_m2": 3500.0,
    "land_cost": 2_000_000.0,
    "build_cost_per_m2": 1800.0,
    "soft_cost_pct": 0.10,
    "contingency_pct": 0.07,
    "equity_share": 0.40,
    "debt_rate_annual": 0.08,
    "discount_rate_annual": 0.10,
    "downside_mode": False,
    "price_shock_pct": -0.05,
    "cost_shock_pct": 0.10,
    "delay_months": 3,
}

def cashflow(inputs):

    months = int(inputs["months"])
    start_sales_month = int(inputs["start_sales_month"])
    sellable_area_m2 = float(inputs["sellable_area_m2"])
    sales_m2_per_month = float(inputs["sales_m2_per_month"])
    sell_price_per_m2 = float(inputs["sell_price_per_m2"])
    land_cost = float(inputs["land_cost"])
    build_cost_per_m2 = float(inputs["build_cost_per_m2"])
    soft_cost_pct = float(inputs["soft_cost_pct"])
    contingency_pct = float(inputs["contingency_pct"])
    equity_share = float(inputs["equity_share"])
    debt_rate_annual = float(inputs["debt_rate_annual"])
    downside_mode = bool(inputs["downside_mode"])
    price_shock_pct = float(inputs["price_shock_pct"])
    cost_shock_pct = float(inputs["cost_shock_pct"])
    delay_months = int(inputs["delay_months"])

    r_debt_m = (1 + debt_rate_annual)**(1/12) - 1

    if downside_mode:
        months_eff = months + delay_months
        sell_price_per_m2 = sell_price_per_m2 * (1 + price_shock_pct)
        build_cost_per_m2 = build_cost_per_m2 * (1 + cost_shock_pct)
        start_sales_month += delay_months
    else:
        months_eff = months

    cashflow = pd.DataFrame({
        "month": range(1, months_eff+1),
        "revenue": float(0),
        "land_cost": float(0),
        "hard_cost": float(0),
        "soft_cost": float(0),
        "contingency": float(0),
        "net_cf_before_finance": float(0),
        "cum_cf_before_finance": float(0),
        "interest": float(0),
        "debt_draw": float(0),
        "equity_draw": float(0),
        "debt_outstanding": float(0),
        "cash_balance": float(0),
        "debt_repay": float(0),
        "net_cf_after_finance": float(0)
        })

    hard_total = build_cost_per_m2 * sellable_area_m2

    if months_eff < 6:

        cashflow["hard_cost"] = -(hard_total / months_eff)

    else:

        m1 = months_eff // 3
        m2 = months_eff // 3
        m3 = months_eff - m1 - m2

        c1 = -(0.20 * hard_total) / m1
        c2 = -(0.60 * hard_total) / m2
        c3 = -(0.20 * hard_total) / m3

        cashflow.loc[0:m1-1, "hard_cost"] = c1
        cashflow.loc[m1:m1+m2-1, "hard_cost"] = c2
        cashflow.loc[m1+m2:m1+m2+m3-1, "hard_cost"] = c3

    soft_total = hard_total * soft_cost_pct
    cont_total = hard_total * contingency_pct

    w = abs(cashflow["hard_cost"])
    w_sum = w.sum()

    cashflow["soft_cost"] = -(soft_total) * w / w_sum
    cashflow["contingency"] = -(cont_total) * w / w_sum

    cashflow.loc[0, "land_cost"] = -land_cost

    remaining = sellable_area_m2
    for i in range (start_sales_month - 1, months_eff):
        sold = min(sales_m2_per_month, remaining)
        cashflow.loc[i, "revenue"] = sold * sell_price_per_m2
        remaining -= sold
        if remaining<= 0:
            break

    cashflow["net_cf_before_finance"] = cashflow["revenue"] + cashflow["land_cost"] + cashflow["hard_cost"] + cashflow["soft_cost"] + cashflow["contingency"]
    cashflow["cum_cf_before_finance"] = cashflow["net_cf_before_finance"].cumsum()

    debt_outstanding = 0.0
    cash_balance = 0.0

    for i in range(months_eff):
        interest = -debt_outstanding * r_debt_m
        cash_after_ops = cash_balance + cashflow.loc[i, "net_cf_before_finance"] + interest
        if cash_after_ops >= 0:
            debt_draw = 0.0
            equity_draw = 0.0
            if debt_outstanding > 0:
                repay = min(cash_after_ops, debt_outstanding)
                cashflow.loc[i, "debt_repay"] = -repay
                debt_outstanding -= repay
                cash_balance = cash_after_ops - repay
            else:
                cash_balance = cash_after_ops
        else:
            deficit = -cash_after_ops
            equity_draw = deficit * equity_share
            debt_draw = deficit * (1 - equity_share)
            debt_outstanding += debt_draw
            cash_balance = 0.0

        cashflow.loc[i, "interest"] = interest
        cashflow.loc[i, "debt_draw"] = debt_draw
        cashflow.loc[i, "equity_draw"] = equity_draw
        cashflow.loc[i, "debt_outstanding"] = debt_outstanding
        cashflow.loc[i, "cash_balance"] = cash_balance
        cashflow.loc[i, "net_cf_after_finance"] = cashflow.loc[i, "net_cf_before_finance"] + interest + debt_draw + equity_draw + cashflow.loc[i, "debt_repay"]

    eps = 1e-6
    tol = max(1.0, abs(hard_total) * 1e-6)

    assert abs(cashflow["hard_cost"].sum() + hard_total) <= tol, "hard_cost does not sum to -hard_total"
    assert abs(cashflow["soft_cost"].sum() + soft_total) <= tol, "soft_cost does not sum to -soft_total"
    assert abs(cashflow["contingency"].sum() + cont_total) <= tol, "contingency does not sum to -cont_total"
    assert abs(cashflow["land_cost"].sum() + land_cost) <= tol, "land_cost total mismatch"
    assert cashflow.loc[1:, "land_cost"].abs().max() <= eps, "land_cost should be only in month 1"
    sold_area = cashflow["revenue"].sum() / sell_price_per_m2 if sell_price_per_m2 > 0 else 0.0
    assert sold_area <= sellable_area_m2 + 1e-3, "sold area exceeds sellable_area_m2"
    assert cashflow["cash_balance"].min() >= -eps, "cash_balance went negative (financing logic broken)"
    assert cashflow["debt_outstanding"].min() >= -eps, "debt_outstanding went negative"
    assert cashflow["interest"].sum() <= eps, "interest should be <= 0 overall"
    assert cashflow["debt_outstanding"].min() >= -eps, "debt_outstanding went negative after repayment"
    assert cashflow["debt_repay"].max() <= eps, "debt_repay should be <= 0 (repayment is an outflow)"

    return cashflow

def compute_metrics(df, inputs):

    discount_rate_annual = float(inputs["discount_rate_annual"])

    r_disc_m = (1 + discount_rate_annual)**(1/12) - 1

    cf = df["net_cf_before_finance"].values
    npv_project = 0.0
    for i in range(len(cf)):
        npv_project += cf[i] / (1+r_disc_m)**(i+1)

    irr_m = nf.irr(cf)
    if np.isnan(irr_m):
        irr_annual = None
    else:
        irr_annual = (1 + irr_m)**12 - 1

    total_invest = 0.0
    total_profit = float(np.sum(cf))
    for i in cf:
        if i < 0:
            total_invest += abs(i)

    if total_invest == 0:
        roi = None
    else:
        roi = total_profit / total_invest

    payback_month = None
    for i in range(len(df)):
        if df.loc[i,"cum_cf_before_finance"]>=0:
            payback_month = i + 1
            break

    max_debt = df["debt_outstanding"].max()
    total_interest = abs(df["interest"].sum())
    equity_invested = df["equity_draw"].sum()
    ending_cash = df["cash_balance"].iloc[-1]

    project_profit = float(np.sum(cf))
    margin_on_revenue = None
    if df["revenue"].sum() > 0:
        margin_on_revenue = project_profit / df["revenue"].sum()

    peak_cash_need = float(-df["cum_cf_before_finance"].min())

    fins = {
       "npv_project": npv_project,
       "irr_annual": irr_annual,
       "roi": roi,
       "payback_month": payback_month,
       "max_debt": max_debt,
       "total_interest": total_interest,
       "equity_invested": equity_invested,
       "ending_cash": ending_cash,
       "margin_on_revenue": margin_on_revenue,
       "peak_cash_need":peak_cash_need}

    return fins
print(cashflow(inputs))
