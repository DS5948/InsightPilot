
import pandas as pd

from database import save_sales_data, load_sales_data, get_revenue_by_region


data = {
    "month": pd.to_datetime([
        "2026-01", "2026-01", "2026-02",
        "2026-02", "2026-03", "2026-03",
    ]),
    "region": ["North", "South", "North", "South", "North", "South"],
    "product": ["Laptop", "Phone", "Laptop", "Phone", "Laptop", "Phone"],
    "revenue": [12000, 9000, 10000, 11000, 8000, 13000],
    "cost": [8000, 6000, 7000, 7000, 5500, 8000],
}

df = pd.DataFrame(data)
df["profit"] = df["revenue"] - df["cost"]

save_sales_data(df)

loaded_df = load_sales_data()
regional_df = get_revenue_by_region()

print("Records loaded:", len(loaded_df))
print("\nRevenue by region:")
print(regional_df)

assert len(loaded_df) == 6
assert loaded_df["revenue"].sum() == 63000

print("\nDatabase test passed!")
