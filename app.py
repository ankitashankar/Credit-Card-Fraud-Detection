"""Interactive Streamlit dashboard for the supplied transaction dataset."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from data_processing import (
    aggregate_daily_transactions,
    aggregate_geography,
    load_transactions,
)


DATA_PATH = Path(__file__).resolve().parent / "credit_card_fraud_detection_2026.csv"
COUNTRY_ISO3 = {
    "Australia": "AUS",
    "Brazil": "BRA",
    "Canada": "CAN",
    "China": "CHN",
    "France": "FRA",
    "Germany": "DEU",
    "India": "IND",
    "Italy": "ITA",
    "Japan": "JPN",
    "Mexico": "MEX",
    "Netherlands": "NLD",
    "Nigeria": "NGA",
    "Romania": "ROU",
    "Russia": "RUS",
    "South Africa": "ZAF",
    "South Korea": "KOR",
    "Spain": "ESP",
    "UAE": "ARE",
    "UK": "GBR",
    "USA": "USA",
}


@st.cache_data(show_spinner="Loading and cleaning transaction data...")
def get_data(csv_path: str) -> pd.DataFrame:
    return load_transactions(csv_path)


st.set_page_config(
    page_title="Credit Card Fraud Analytics 2",
    page_icon="💳",
    layout="wide",
)
st.title("Credit Card Fraud Analytics 2")
st.caption(
    "Explore transaction activity, fraud patterns, merchant geography, "
    "and customer credit scores."
)

if not DATA_PATH.is_file():
    st.error(f"Dataset not found: {DATA_PATH}")
    st.stop()

try:
    transactions = get_data(str(DATA_PATH))
except (OSError, pd.errors.ParserError, ValueError) as error:
    st.error(f"Could not load the transaction dataset: {error}")
    st.stop()

if transactions.empty:
    st.warning("The dataset contains no valid transactions after cleaning.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    min_date = transactions["transaction_date"].min().date()
    max_date = transactions["transaction_date"].max().date()
    selected_dates = st.date_input(
        "Transaction date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    categories = sorted(transactions["merchant_category"].unique().tolist())
    selected_categories = st.multiselect(
        "Merchant categories", categories, default=categories
    )
    countries = sorted(transactions["merchant_country"].unique().tolist())
    selected_countries = st.multiselect(
        "Merchant countries", countries, default=countries
    )
    fraud_filter = st.selectbox(
        "Transaction type", ["All", "Fraudulent", "Legitimate"]
    )

filtered = transactions
if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2 and all(selected_dates):
        start_date, end_date = selected_dates
        filtered = filtered.loc[
            filtered["transaction_date"].between(
                pd.Timestamp(start_date), pd.Timestamp(end_date)
            )
        ]
elif selected_dates is not None:
    filtered = filtered.loc[
        filtered["transaction_date"].dt.date.eq(pd.Timestamp(selected_dates).date())
    ]
if selected_categories:
    filtered = filtered.loc[
        filtered["merchant_category"].isin(selected_categories)
    ]
else:
    filtered = filtered.iloc[0:0]
if selected_countries:
    filtered = filtered.loc[filtered["merchant_country"].isin(selected_countries)]
else:
    filtered = filtered.iloc[0:0]
if fraud_filter == "Fraudulent":
    filtered = filtered.loc[filtered["is_fraud"].eq(1)]
elif fraud_filter == "Legitimate":
    filtered = filtered.loc[filtered["is_fraud"].eq(0)]

if filtered.empty:
    st.info("No transactions match the selected filters.")
    st.stop()

total_transactions = len(filtered)
fraud_count = int(filtered["is_fraud"].sum())
fraud_rate = fraud_count / total_transactions
total_amount = filtered["transaction_amount"].sum()
average_amount = filtered["transaction_amount"].mean()

metric_columns = st.columns(4)
metric_columns[0].metric("Transactions", f"{total_transactions:,}")
metric_columns[1].metric("Fraud rate", f"{fraud_rate:.2%}")
metric_columns[2].metric("Transaction volume", f"${total_amount:,.2f}")
metric_columns[3].metric("Average transaction", f"${average_amount:,.2f}")

amount_chart, map_chart = st.columns(2)
with amount_chart:
    st.subheader("Transaction amount distribution")
    fig = px.histogram(
        filtered,
        x="transaction_amount",
        color=filtered["is_fraud"].map({0: "Legitimate", 1: "Fraud"}),
        nbins=50,
        barmode="overlay",
        opacity=0.75,
        labels={"color": "Transaction type", "transaction_amount": "Amount ($)"},
        color_discrete_map={"Legitimate": "#4c78a8", "Fraud": "#e45756"},
    )
    st.plotly_chart(fig, width="stretch")

with map_chart:
    st.subheader("Geographic transaction density")
    geography = aggregate_geography(filtered)
    geography["iso3"] = geography["merchant_country"].map(COUNTRY_ISO3)
    mapped = geography.dropna(subset=["iso3"])
    if mapped.empty:
        st.info("No recognized merchant countries are available for the map.")
    else:
        fig = px.choropleth(
            mapped,
            locations="iso3",
            locationmode="ISO-3",
            color="transaction_count",
            hover_name="merchant_country",
            hover_data={
                "transaction_count": ":,",
                "fraud_count": ":,",
                "fraud_rate": ":.2%",
                "iso3": False,
            },
            color_continuous_scale="Blues",
            labels={"transaction_count": "Transactions"},
        )
        fig.update_geos(showcoastlines=True, showcountries=True)
        st.plotly_chart(fig, width="stretch")

trend_chart, score_chart = st.columns(2)
with trend_chart:
    st.subheader("Daily fraud rate")
    daily = aggregate_daily_transactions(filtered)
    daily["fraud_rate_percent"] = daily["fraud_rate"] * 100
    fig = px.line(
        daily,
        x="transaction_date",
        y="fraud_rate_percent",
        markers=True,
        labels={
            "transaction_date": "Date",
            "fraud_rate_percent": "Fraud rate (%)",
        },
    )
    st.plotly_chart(fig, width="stretch")

with score_chart:
    st.subheader("Fraud rate by credit score")
    if "credit_score" not in filtered.columns:
        st.info("Credit score is not available in this dataset.")
    else:
        scored = filtered.copy()
        scored["credit_score"] = pd.to_numeric(
            scored["credit_score"], errors="coerce"
        )
        scored = scored.dropna(subset=["credit_score"])
        if scored.empty:
            st.info("No valid credit scores are available for the selected filters.")
        else:
            scored["credit_score_band"] = pd.cut(
                scored["credit_score"],
                bins=[0, 579, 669, 739, 799, float("inf")],
                labels=["Poor", "Fair", "Good", "Very good", "Excellent"],
                include_lowest=True,
            )
            score_summary = (
                scored.groupby("credit_score_band", observed=False)
                .agg(
                    transaction_count=("transaction_id", "count"),
                    fraud_rate=("is_fraud", "mean"),
                )
                .reset_index()
            )
            score_summary["fraud_rate_percent"] = score_summary["fraud_rate"] * 100
            fig = px.bar(
                score_summary,
                x="credit_score_band",
                y="fraud_rate_percent",
                hover_data={"transaction_count": ":,"},
                labels={
                    "credit_score_band": "Credit score band",
                    "fraud_rate_percent": "Fraud rate (%)",
                },
                color="fraud_rate_percent",
                color_continuous_scale="Reds",
            )
            st.plotly_chart(fig, width="stretch")

with st.expander("View filtered transaction data"):
    st.dataframe(filtered, width="stretch", hide_index=True)