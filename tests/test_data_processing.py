import pandas as pd
import pytest

from data_processing import (
    aggregate_daily_transactions,
    aggregate_geography,
    clean_transactions,
)


@pytest.fixture
def sample_transactions():
    return pd.DataFrame(
        {
            "transaction_id": ["A", "B", "B", "C", "D"],
            "transaction_datetime": [
                "2026-01-01 10:00:00",
                "2026-01-01 11:00:00",
                "2026-01-01 11:00:00",
                "invalid",
                "2026-01-02 12:00:00",
            ],
            "transaction_amount": ["10.50", "20", "20", "5", "-1"],
            "is_fraud": [0, 1, 1, 0, 0],
            "merchant_country": ["USA", "USA", "USA", "UK", None],
            "merchant_category": ["Retail", "Dining", "Dining", "Retail", None],
        }
    )


def test_clean_transactions_drops_invalid_and_duplicate_rows(sample_transactions):
    cleaned = clean_transactions(sample_transactions)

    assert cleaned["transaction_id"].tolist() == ["A", "B"]
    assert cleaned["transaction_amount"].tolist() == [10.5, 20.0]
    assert cleaned["is_fraud"].tolist() == [0, 1]
    assert pd.api.types.is_datetime64_any_dtype(cleaned["transaction_datetime"])
    assert cleaned.loc[1, "transaction_date"] == pd.Timestamp("2026-01-01")


def test_clean_transactions_fills_missing_categories_and_does_not_mutate_input():
    raw = pd.DataFrame(
        {
            "transaction_id": ["A"],
            "transaction_datetime": ["2026-01-01"],
            "transaction_amount": [1],
            "is_fraud": [0],
            "merchant_country": [None],
            "merchant_category": [""],
        }
    )

    cleaned = clean_transactions(raw)

    assert cleaned.loc[0, "merchant_country"] == "Unknown"
    assert cleaned.loc[0, "merchant_category"] == "Unknown"
    assert pd.isna(raw.loc[0, "merchant_country"])


def test_clean_transactions_requires_dashboard_columns():
    with pytest.raises(ValueError, match="merchant_category"):
        clean_transactions(pd.DataFrame({"transaction_id": ["A"]}))


def test_aggregations_report_daily_and_country_fraud_metrics(sample_transactions):
    cleaned = clean_transactions(sample_transactions)

    daily = aggregate_daily_transactions(cleaned)
    geography = aggregate_geography(cleaned)

    assert daily.loc[0, "transaction_count"] == 2
    assert daily.loc[0, "fraud_count"] == 1
    assert daily.loc[0, "fraud_rate"] == 0.5
    assert geography.loc[0, "merchant_country"] == "USA"
    assert geography.loc[0, "transaction_count"] == 2
    assert geography.loc[0, "fraud_rate"] == 0.5
