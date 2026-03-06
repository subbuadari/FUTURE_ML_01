import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Generate date range (3 years of daily sales data)
start_date = datetime(2021, 1, 1)
end_date = datetime(2023, 12, 31)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')

# Create base dataframe
data = pd.DataFrame({
    'date': date_range,
    'day_of_week': date_range.dayofweek,
    'month': date_range.month,
    'quarter': date_range.quarter,
    'day_of_year': date_range.dayofyear
})

# Generate realistic sales data with multiple components
n_rows = len(data)

# Trend: Gradually increasing sales over time
trend = np.linspace(5000, 8000, n_rows)

# Seasonality: Higher sales in Q4 (holiday season), lower in Q1
seasonality = 1500 * np.sin((data['day_of_year'] - 80) * 2 * np.pi / 365)

# Weekly pattern: Higher sales on weekends (Saturday=5, Sunday=6)
weekly_pattern = np.where((data['day_of_week'] >= 5), 800, 0)

# Random noise
noise = np.random.normal(0, 500, n_rows)

# Combine all components
data['sales'] = trend + seasonality + weekly_pattern + noise
data['sales'] = data['sales'].clip(lower=1000)  # Ensure no negative sales

# Add store/product categories
data['store_id'] = np.random.choice(['Store_A', 'Store_B', 'Store_C'], n_rows, p=[0.5, 0.3, 0.2])
data['product_category'] = np.random.choice(['Electronics', 'Clothing', 'Food'], n_rows, p=[0.4, 0.35, 0.25])

# Adjust sales based on store
store_multipliers = {'Store_A': 1.0, 'Store_B': 0.8, 'Store_C': 1.2}
data['sales'] = data.apply(lambda row: row['sales'] * store_multipliers[row['store_id']], axis=1)

# Round to realistic values
data['sales'] = data['sales'].round(2)

# Reorder columns
data = data[['date', 'store_id', 'product_category', 'sales', 'day_of_week', 'month', 'quarter', 'day_of_year']]

# Save the dataset
data.to_csv('data/sales_data.csv', index=False)

print("✅ Sales dataset created successfully!")
print(f"Dataset shape: {data.shape}")
print(f"Date range: {data['date'].min()} to {data['date'].max()}")
print(f"\nFirst few rows:")
print(data.head(10))
print(f"\nData summary:")
print(data.describe())
