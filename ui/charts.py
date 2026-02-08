import plotly.express as px
import plotly.graph_objects as go


def plot_income_vs_expenses(df):
    """
    df must contain:
    Year, Total Income, Total Expenses
    """
    fig = px.line(
        df,
        x="Year",
        y=["Total Income", "Total Expenses"],
        markers=True,
        title="Income vs Expenses Over Time"
    )
    fig.update_layout(
        yaxis_title="Amount (₹)",
        xaxis_title="Year"
    )
    return fig


def plot_yearly_income_breakup(df):
    """
    Stacked bar chart for income sources
    """
    fig = px.bar(
        df,
        x="Year",
        y="Amount",
        color="Source",
        title="Yearly Income & SWP Gain/Loss Breakdown",
        barmode="relative"
    )
    fig.update_layout(
        yaxis_title="Amount (₹)",
        xaxis_title="Year"
    )
    return fig


def plot_pie_expenses(df, title):
    """
    df: columns -> Label, Value
    """
    fig = px.pie(
        df,
        names="Label",
        values="Value",
        title=title
    )
    return fig

def plot_corpus_comparison(scenario_data: dict):
    """
    scenario_data = {
        "Baseline": df1,
        "High Inflation": df2,
        ...
    }
    Each df must have: Year, LocalSWPBalancePostWithdrawal
    """
    fig = go.Figure()

    for label, df in scenario_data.items():
        fig.add_trace(go.Scatter(
            x=df["Year"],
            y=df["LocalSWPBalancePostWithdrawal"],
            mode="lines",
            name=label
        ))

    fig.update_layout(
        title="Corpus Trajectory Comparison",
        xaxis_title="Year",
        yaxis_title="Corpus Value (₹)"
    )
    return fig
