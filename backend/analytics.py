
import pandas as pd


def calculate_total_revenue(df):
    """Return the sum of all sales revenue."""
    return df["revenue"].sum()


def calculate_total_profit(df):
    """Return the sum of revenue minus cost."""
    return (df["revenue"] - df["cost"]).sum()


def revenue_by_month(df):
    """Return total revenue grouped by month."""
    return (
        df.groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )


def revenue_by_region(df):
    """Return total revenue grouped by region."""
    return (
        df.groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )


def revenue_by_product(df):
    """Return total revenue grouped by product."""
    return (
        df.groupby("product", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )


def revenue_by_product_month(df):
    """
    Calculate revenue for each product in each month.
    """
    result = (
        df.groupby(["month", "product"], as_index=False)["revenue"]
        .sum()
        .sort_values(["month", "product"])
    )

    return result
