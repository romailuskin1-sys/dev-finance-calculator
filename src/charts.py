import plotly.express as px

def fig_cum_cf(df, payback_month=None):
    fig = px.line(
        df,
        x="month",
        y="cum_cf_before_finance",
        title="Cumulative Cash Flow (Project, before financing)",
        labels={"month": "Month", "cum_cf_before_finance": "Cumulative CF (€)"},
    )
    fig.add_hline(y=0)

    if payback_month is not None:
        fig.add_vline(x=payback_month)
    return fig


def fig_debt(df):
    fig = px.line(
        df,
        x="month",
        y="debt_outstanding",
        title="Debt Outstanding",
        labels={"month": "Month", "debt_outstanding": "Debt (€)"},
    )
    return fig


def fig_cash(df):
    """
    Cash balance over time.
    Requires columns: month, cash_balance
    """
    fig = px.line(
        df,
        x="month",
        y="cash_balance",
        title="Cash Balance",
        labels={"month": "Month", "cash_balance": "Cash (€)"},
    )
    return fig


def fig_revenue_vs_costs(df):
    tmp = df.copy()
    tmp["monthly_costs"] = tmp["land_cost"] + tmp["hard_cost"] + tmp["soft_cost"] + tmp["contingency"]

    long = tmp.melt(
        id_vars=["month"],
        value_vars=["revenue", "monthly_costs"],
        var_name="series",
        value_name="amount",
    )

    fig = px.line(
        long,
        x="month",
        y="amount",
        color="series",
        title="Revenue vs Monthly Costs",
        labels={"month": "Month", "amount": "€", "series": ""},
    )
    fig.add_hline(y=0)
    return fig
