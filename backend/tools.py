
import pandas as pd

from analytics import (
    calculate_total_revenue,
    calculate_total_profit,
    revenue_by_month,
    revenue_by_region,
    revenue_by_product,
    revenue_by_product_month,
)


def get_sales_summary(df: pd.DataFrame) -> dict:
    """Return the overall sales and profit summary."""
    return {
        "total_revenue": float(calculate_total_revenue(df)),
        "total_profit": float(calculate_total_profit(df)),
        "total_records": len(df),
    }


def get_regional_performance(df: pd.DataFrame) -> list[dict]:
    """Return revenue totals grouped by region."""
    result = revenue_by_region(df)

    return result.to_dict(orient="records")


def get_product_performance(df: pd.DataFrame) -> list[dict]:
    """Return revenue totals grouped by product."""
    result = revenue_by_product(df)

    return result.to_dict(orient="records")


def get_monthly_performance(df: pd.DataFrame) -> list[dict]:
    """Return monthly revenue totals."""
    result = revenue_by_month(df)

    # Convert dates to strings for easy JSON serialization.
    result["month"] = result["month"].dt.strftime("%Y-%m")

    return result.to_dict(orient="records")


def get_product_monthly_performance(df: pd.DataFrame) -> list[dict]:
    result = revenue_by_product_month(df)

    result["month"] = result["month"].dt.strftime("%Y-%m")

    return result.to_dict(orient="records")
