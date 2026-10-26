
import pandas as pd

from tools import (
    get_sales_summary,
    get_regional_performance,
    get_product_performance,
    get_monthly_performance,
)


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

df["profit"] = df["revenue"] - df["cost"]


summary = get_sales_summary(df)
assert summary["total_revenue"] == 63000
assert summary["total_profit"] == 21500
assert summary["total_records"] == 6

regions = get_regional_performance(df)
assert regions[0]["region"] == "South"
assert regions[0]["revenue"] == 33000

products = get_product_performance(df)
assert products[0]["product"] == "Phone"
assert products[0]["revenue"] == 33000

months = get_monthly_performance(df)
assert len(months) == 3
assert months[0]["month"] == "2026-01"
assert months[0]["revenue"] == 21000

print("All analysis tool tests passed!")
print("\nSales summary:", summary)
print("Regional performance:", regions)
