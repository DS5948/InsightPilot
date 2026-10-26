
import pandas as pd

from analytics import (
    calculate_total_revenue,
    calculate_total_profit,
    revenue_by_month,
    revenue_by_region,
    revenue_by_product,
)


def test_sample_sales_analytics():
    df = pd.DataFrame({
        "month": pd.to_datetime([
            "2026-01", "2026-01", "2026-02",
            "2026-02", "2026-03", "2026-03",
        ]),
        "region": [
            "North", "South", "North",
            "South", "North", "South",
        ],
        "product": [
            "Laptop", "Phone", "Laptop",
            "Phone", "Laptop", "Phone",
        ],
        "revenue": [12000, 9000, 10000, 11000, 8000, 13000],
        "cost": [8000, 6000, 7000, 7000, 5500, 8000],
    })

    assert calculate_total_revenue(df) == 63000
    assert calculate_total_profit(df) == 21500

    monthly = revenue_by_month(df)
    assert monthly["revenue"].tolist() == [21000, 21000, 21000]

    regional = revenue_by_region(df)
    assert regional["region"].tolist() == ["South", "North"]
    assert regional["revenue"].tolist() == [33000, 30000]

    products = revenue_by_product(df)
    assert products["product"].tolist() == ["Phone", "Laptop"]
    assert products["revenue"].tolist() == [33000, 30000]

    print("All analytics checks passed!")


if __name__ == "__main__":
    test_sample_sales_analytics()
