"""Loading, cleaning, and aggregation helpers for transaction data."""

from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "transaction_id",
    "transaction_datetime",
    "transaction_amount",
    "is_fraud",
    "merchant_country",
    "merchant_category",
}


def clean_transactions(data: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned transaction frame without mutating the input."""
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    cleaned = data.copy()
    cleaned["transaction_datetime"] = pd.to_datetime(
        cleaned["transaction_datetime"], errors="coerce"
    )
    cleaned["transaction_amount"] = pd.to_numeric(
        cleaned["transaction_amount"], errors="coerce"
    )
    cleaned["is_fraud"] = pd.to_numeric(cleaned["is_fraud"], errors="coerce")

    valid_rows = (
        cleaned["transaction_id"].notna()
        & cleaned["transaction_datetime"].notna()
        & cleaned["transaction_amount"].notna()
        & np.isfinite(cleaned["transaction_amount"])
        & cleaned["transaction_amount"].ge(0)
        & cleaned["is_fraud"].isin([0, 1])
    )
    cleaned = cleaned.loc[valid_rows].copy()
    cleaned["transaction_id"] = cleaned["transaction_id"].astype(str).str.strip()
    cleaned = cleaned.loc[cleaned["transaction_id"].ne("")]
    cleaned = cleaned.drop_duplicates(subset="transaction_id", keep="first")
    cleaned["is_fraud"] = cleaned["is_fraud"].astype("int8")

    for column in ("merchant_country", "merchant_category"):
        cleaned[column] = (
            cleaned[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .replace("", "Unknown")
        )

    cleaned["transaction_date"] = cleaned["transaction_datetime"].dt.normalize()
    return cleaned.reset_index(drop=True)


def load_transactions(path: str | Path) -> pd.DataFrame:
    """Read a CSV and return its cleaned transactions."""
    return clean_transactions(pd.read_csv(path, low_memory=False))


def aggregate_daily_transactions(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transaction volume, fraud, and amount by calendar date."""
    daily = (
        data.groupby("transaction_date", as_index=False)
        .agg(
            transaction_count=("transaction_id", "count"),
            fraud_count=("is_fraud", "sum"),
            total_amount=("transaction_amount", "sum"),
        )
        .sort_values("transaction_date")
    )
    daily["fraud_rate"] = daily["fraud_count"].div(daily["transaction_count"])
    return daily


def aggregate_geography(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transaction volume and fraud metrics by merchant country."""
    geography = (
        data.groupby("merchant_country", as_index=False)
        .agg(
            transaction_count=("transaction_id", "count"),
            fraud_count=("is_fraud", "sum"),
            total_amount=("transaction_amount", "sum"),
        )
        .sort_values("transaction_count", ascending=False)
    )
    geography["fraud_rate"] = geography["fraud_count"].div(
        geography["transaction_count"]
    )
    return geography
