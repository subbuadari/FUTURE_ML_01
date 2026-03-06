#!/usr/bin/env python3
"""
Sales & Demand Forecasting System
Complete implementation of a business forecasting solution
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import pickle
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta

# Ensure output directories exist
for folder in ['output', 'output/archive', 'models']:
    if not os.path.exists(folder):
        os.makedirs(folder)

warnings.filterwarnings('ignore')

# Set visualization style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 10

print("="*80)
print("SALES & DEMAND FORECASTING SYSTEM")
print("="*80)

# ============================================================================
# 1. LOAD AND EXPLORE DATA
# ============================================================================
print("\n[1/7] Loading and exploring data...")
df = pd.read_csv('data/sales_data.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Aggregate by date
daily_sales = df.groupby('date')['sales'].sum().reset_index()
daily_sales.columns = ['date', 'sales']

print(f"✓ Dataset loaded: {len(daily_sales)} days of sales data")
print(f"  Date range: {daily_sales['date'].min().date()} to {daily_sales['date'].max().date()}")
print(f"  Average daily sales: ${daily_sales['sales'].mean():,.2f}")
print(f"  Min/Max daily sales: ${daily_sales['sales'].min():,.2f} / ${daily_sales['sales'].max():,.2f}")

# ============================================================================
# 2. TIME-SERIES VISUALIZATION
# ============================================================================
print("\n[2/7] Creating time-series visualizations...")

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Full time series
axes[0].plot(daily_sales['date'], daily_sales['sales'], linewidth=2, color='#2E86AB')
axes[0].set_title('Daily Sales Over Time - Full Period', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Date')
axes[0].set_ylabel('Sales ($)')
axes[0].grid(True, alpha=0.3)

# Monthly aggregated sales
monthly_sales = daily_sales.copy()
monthly_sales['year_month'] = monthly_sales['date'].dt.to_period('M')
monthly_agg = monthly_sales.groupby('year_month')['sales'].sum().reset_index()
monthly_agg['year_month'] = monthly_agg['year_month'].astype(str)

axes[1].bar(range(len(monthly_agg)), monthly_agg['sales'], color='#A23B72', alpha=0.8)
axes[1].set_title('Monthly Total Sales - Identifying Seasonality', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Sales ($)')
axes[1].set_xticks(range(0, len(monthly_agg), 3))
axes[1].set_xticklabels(monthly_agg['year_month'][::3], rotation=45)
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('output/01_time_series_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("✓ Time-series visualization saved")

# ============================================================================
# 3. FEATURE ENGINEERING
# ============================================================================
print("\n[3/7] Engineering time-based features...")

df_features = daily_sales.copy()

# Extract time-based features
df_features['day'] = df_features['date'].dt.day
df_features['month'] = df_features['date'].dt.month
df_features['quarter'] = df_features['date'].dt.quarter
df_features['year'] = df_features['date'].dt.year
df_features['day_of_week'] = df_features['date'].dt.dayofweek
df_features['day_of_year'] = df_features['date'].dt.dayofyear
df_features['is_weekend'] = df_features['day_of_week'].isin([5, 6]).astype(int)

# Lag features
df_features['lag_1'] = df_features['sales'].shift(1)
df_features['lag_7'] = df_features['sales'].shift(7)
df_features['lag_30'] = df_features['sales'].shift(30)

# Rolling average features
df_features['rolling_mean_7'] = df_features['sales'].rolling(window=7).mean()
df_features['rolling_mean_30'] = df_features['sales'].rolling(window=30).mean()

# Drop NaN values
df_features = df_features.dropna().reset_index(drop=True)

feature_cols = ['day', 'month', 'quarter', 'year', 'day_of_week', 'day_of_year',
                'is_weekend', 'lag_1', 'lag_7', 'lag_30', 'rolling_mean_7', 'rolling_mean_30']

print(f"✓ Created {len(feature_cols)} features")
print(f"  Available training samples: {len(df_features)}")

# ============================================================================
# 4. TRAIN-TEST SPLIT (TIME-SERIES AWARE)
# ============================================================================
print("\n[4/7] Splitting data for training...")

train_size = int(len(df_features) * 0.70)
val_size = int(len(df_features) * 0.15)

train_data = df_features[:train_size]
val_data = df_features[train_size:train_size+val_size]
test_data = df_features[train_size+val_size:]

X_train = train_data[feature_cols]
y_train = train_data['sales']

X_val = val_data[feature_cols]
y_val = val_data['sales']

X_test = test_data[feature_cols]
y_test = test_data['sales']

print(f"✓ Train set: {len(train_data)} samples (70%)")
print(f"✓ Validation set: {len(val_data)} samples (15%)")
print(f"✓ Test set: {len(test_data)} samples (15%)")

# ============================================================================
# 5. TRAIN MULTIPLE MODELS
# ============================================================================
print("\n[5/7] Training forecasting models...")

models = {}
results = {}

# Linear Regression
print("  • Training Linear Regression...")
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
lr_pred_val = lr_model.predict(X_val)
lr_pred_test = lr_model.predict(X_test)
models['Linear Regression'] = lr_model
results['Linear Regression'] = {'val_pred': lr_pred_val, 'test_pred': lr_pred_test}

# Random Forest
print("  • Training Random Forest...")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
rf_pred_val = rf_model.predict(X_val)
rf_pred_test = rf_model.predict(X_test)
models['Random Forest'] = rf_model
results['Random Forest'] = {'val_pred': rf_pred_val, 'test_pred': rf_pred_test}

# Gradient Boosting
print("  • Training Gradient Boosting...")
gb_model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1,
                                      max_depth=5, random_state=42)
gb_model.fit(X_train, y_train)
gb_pred_val = gb_model.predict(X_val)
gb_pred_test = gb_model.predict(X_test)
models['Gradient Boosting'] = gb_model
results['Gradient Boosting'] = {'val_pred': gb_pred_val, 'test_pred': gb_pred_test}

print("✓ All 3 models trained successfully")

# ============================================================================
# 6. MODEL EVALUATION
# ============================================================================
print("\n[6/7] Evaluating model performance...")

evaluation_results = []

for model_name, model_results in results.items():
    # Validation metrics
    val_mse = mean_squared_error(y_val, model_results['val_pred'])
    val_mae = mean_absolute_error(y_val, model_results['val_pred'])
    val_rmse = np.sqrt(val_mse)
    val_r2 = r2_score(y_val, model_results['val_pred'])

    # Test metrics
    test_mse = mean_squared_error(y_test, model_results['test_pred'])
    test_mae = mean_absolute_error(y_test, model_results['test_pred'])
    test_rmse = np.sqrt(test_mse)
    test_r2 = r2_score(y_test, model_results['test_pred'])

    evaluation_results.append({
        'Model': model_name,
        'Val RMSE': val_rmse,
        'Val MAE': val_mae,
        'Val R²': val_r2,
        'Test RMSE': test_rmse,
        'Test MAE': test_mae,
        'Test R²': test_r2
    })

eval_df = pd.DataFrame(evaluation_results)
best_model_idx = eval_df['Test R²'].idxmax()
best_model_name = eval_df.loc[best_model_idx, 'Model']
best_r2 = eval_df.loc[best_model_idx, 'Test R²']
best_mae = eval_df.loc[best_model_idx, 'Test MAE']

print("\n📊 MODEL EVALUATION RESULTS")
print("-" * 80)
for _, row in eval_df.iterrows():
    m_name = str(row['Model'])
    m_rmse = float(row['Test RMSE'])
    m_mae = float(row['Test MAE'])
    m_r2 = float(row['Test R²'])
    print(f"{m_name:20s} | RMSE: ${m_rmse:8.2f} | MAE: ${m_mae:8.2f} | R²: {m_r2:.4f}")
print("-" * 80)
print(f"🏆 Best Model: {best_model_name} (R² = {best_r2:.4f})")

# Save evaluation results
eval_df.to_csv('output/model_evaluation_results.csv', index=False)

# ============================================================================
# 7. VISUALIZATIONS
# ============================================================================
print("\n[7/7] Creating professional light-themed visualizations...")

# Apply professional light theme styling
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.facecolor'] = '#ffffff'
plt.rcParams['axes.facecolor'] = '#f8fafc'
plt.rcParams['grid.color'] = '#e2e8f0'
plt.rcParams['text.color'] = '#1e293b'
plt.rcParams['axes.labelcolor'] = '#475569'
plt.rcParams['xtick.color'] = '#64748b'
plt.rcParams['ytick.color'] = '#64748b'
plt.rcParams['font.family'] = 'sans-serif'

# Custom colors to match the New Green & White UI theme
PRIMARY_GREEN = '#10b981'
SECONDARY_EMERALD = '#059669'
ACCENT_TEAL = '#0d9488'
LINE_COLORS = [PRIMARY_GREEN, ACCENT_TEAL, '#3b82f6']

# Model comparison visualization
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.patch.set_facecolor('#ffffff')

# Plot 1: All models comparison on test set
ax = axes[0, 0]
test_dates = test_data['date'].values
test_actual = y_test.values

ax.plot(test_dates, test_actual, '-', color='#1e293b', linewidth=3, label='Actual Sales', zorder=3)
for (model_name, model_results), color in zip(results.items(), LINE_COLORS):
    ax.plot(test_dates, model_results['test_pred'], '--', linewidth=2,
            label=model_name, color=color, alpha=0.9)
ax.set_title('Test Set: Actual vs Predicted Sales', fontsize=12, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Sales ($)')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: R² Score comparison
ax = axes[0, 1]
bars = ax.bar(eval_df['Model'], eval_df['Test R²'], color=LINE_COLORS, alpha=0.9)
ax.set_title('R² Score Comparison (Test Set)', fontsize=12, fontweight='bold')
ax.set_ylabel('R² Score')
ax.set_ylim([0, 1.1])
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.3f}',
            ha='center', va='bottom', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

# Plot 3: RMSE comparison
ax = axes[1, 0]
bars = ax.bar(eval_df['Model'], eval_df['Test RMSE'], color=LINE_COLORS, alpha=0.9)
ax.set_title('Root Mean Squared Error (Test Set)', fontsize=12, fontweight='bold')
ax.set_ylabel('RMSE ($)')
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.0f}',
            ha='center', va='bottom', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

# Plot 4: MAE comparison
ax = axes[1, 1]
bars = ax.bar(eval_df['Model'], eval_df['Test MAE'], color=LINE_COLORS, alpha=0.9)
ax.set_title('Mean Absolute Error (Test Set)', fontsize=12, fontweight='bold')
ax.set_ylabel('MAE ($)')
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.0f}',
            ha='center', va='bottom', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('output/02_model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("✓ Model comparison visualization saved")

# ============================================================================
# 8. FUTURE FORECASTING (30 DAYS AHEAD)
# ============================================================================
print("\n[8/8] Generating 30-day sales forecast...")

best_model = models[best_model_name]

# Create forecast period
last_date = daily_sales['date'].max()
future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=30, freq='D')

# Prepare features for forecasting
forecast_features = []

for date in future_dates:
    day = date.day
    month = date.month
    quarter = date.quarter
    year = date.year
    day_of_week = date.dayofweek
    day_of_year = date.dayofyear
    is_weekend = 1 if day_of_week >= 5 else 0

    lag_1 = df_features['sales'].iloc[-1]
    lag_7 = df_features['sales'].iloc[-7]
    lag_30 = df_features['sales'].iloc[-30]

    rolling_mean_7 = df_features['sales'].iloc[-7:].mean()
    rolling_mean_30 = df_features['sales'].iloc[-30:].mean()

    forecast_features.append([day, month, quarter, year, day_of_week, day_of_year,
                              is_weekend, lag_1, lag_7, lag_30, rolling_mean_7, rolling_mean_30])

X_forecast = pd.DataFrame(forecast_features, columns=feature_cols)
forecast_values = best_model.predict(X_forecast)

forecast_df = pd.DataFrame({
    'date': future_dates,
    'forecasted_sales': forecast_values
})

# Weekly aggregation
forecast_df['week'] = forecast_df['date'].dt.to_period('W')
weekly_forecast = forecast_df.groupby('week')['forecasted_sales'].sum().reset_index()
weekly_forecast['week'] = weekly_forecast['week'].astype(str)

# Forecast visualization
fig, axes = plt.subplots(2, 1, figsize=(15, 10))

# Plot 1: Historical + Forecast
ax = axes[0]
recent_data = daily_sales.tail(90)
ax.plot(recent_data['date'], recent_data['sales'], '-', linewidth=2,
        color='#94a3b8', alpha=0.6, label='Historical Sales')
ax.plot(forecast_df['date'], forecast_df['forecasted_sales'], 'o-', linewidth=3,
        markersize=6, label='30-Day Forecast', color=PRIMARY_GREEN)

# Add confidence interval
upper_bound = forecast_df['forecasted_sales'] + best_mae
lower_bound = forecast_df['forecasted_sales'] - best_mae
ax.fill_between(forecast_df['date'], lower_bound, upper_bound, alpha=0.15, color=PRIMARY_GREEN)

ax.set_title(f'Sales Forecast - Next 30 Days (Model: {best_model_name})',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Date', fontsize=11)
ax.set_ylabel('Sales ($)', fontsize=11)
ax.legend(fontsize=11, loc='best')
ax.grid(True, alpha=0.3)

# Plot 2: Weekly forecast
ax = axes[1]
bars = ax.bar(range(len(weekly_forecast)), weekly_forecast['forecasted_sales'],
              color=ACCENT_TEAL, alpha=0.8, edgecolor='none')
ax.set_title('Weekly Total Sales Forecast', fontsize=14, fontweight='bold')
ax.set_xlabel('Week', fontsize=11)
ax.set_ylabel('Sales ($)', fontsize=11)
ax.set_xticks(range(len(weekly_forecast)))
ax.set_xticklabels(weekly_forecast['week'], rotation=45)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height, f'${height:,.0f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('output/03_sales_forecast.png', dpi=300, bbox_inches='tight')
plt.close()
print("✓ Forecast visualization saved")

# ============================================================================
# 9. FEATURE IMPORTANCE & MODEL COEFFICIENTS
# ============================================================================
print("\n[8/8] Visualizing model drivers...")

if best_model_name in ['Random Forest', 'Gradient Boosting'] and hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    title_suffix = " (Gini Importance)"
elif best_model_name == 'Linear Regression' and hasattr(best_model, 'coef_'):
    # Use absolute values of coefficients for Linear Regression
    importances = np.abs(best_model.coef_)
    title_suffix = " (Normalized Coefficients)"
else:
    importances = np.zeros(len(feature_cols))
    title_suffix = ""

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': importances
}).sort_values('importance', ascending=False)

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('#ffffff')
bars = ax.barh(feature_importance['feature'], feature_importance['importance'],
               color=PRIMARY_GREEN, alpha=0.9)
ax.set_title(f'Key Drivers - {best_model_name}{title_suffix}', fontsize=13, fontweight='bold')
ax.set_xlabel('Relative Importance Score', fontsize=11)
ax.invert_yaxis()  # Most important at the top

for bar in bars:
    width = bar.get_width()
    ax.text(width, bar.get_y() + bar.get_height()/2., f'{width:.4f}',
            ha='left', va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('output/04_feature_importance.png', dpi=300, bbox_inches='tight')
plt.close()
print("✓ Feature importance visualization saved")

# ============================================================================
# 10. BUSINESS INSIGHTS & EXPORT
# ============================================================================
print("\n" + "="*80)
print("BUSINESS INSIGHTS & RECOMMENDATIONS")
print("="*80)

historical_avg = daily_sales['sales'].mean()
historical_std = daily_sales['sales'].std()
forecast_avg = forecast_df['forecasted_sales'].mean()
forecast_total = forecast_df['forecasted_sales'].sum()
growth_rate = ((forecast_avg - historical_avg) / historical_avg) * 100

print(f"\n1. FORECAST OVERVIEW")
print(f"   • Historical Average Daily Sales: ${historical_avg:,.2f}")
print(f"   • Forecasted Average Daily Sales (Next 30 Days): ${forecast_avg:,.2f}")
print(f"   • Projected Change: {growth_rate:+.1f}%")
print(f"   • Total Forecasted Sales (30 days): ${forecast_total:,.2f}")

print(f"\n2. MODEL PERFORMANCE")
print(f"   • Selected Model: {best_model_name}")
print(f"   • Model Accuracy (R² Score): {best_r2:.2%}")
print(f"   • Average Prediction Error: ±${best_mae:,.2f}")
print(f"   • Prediction Confidence: {(1 - (best_mae/historical_avg))*100:.1f}%")

max_forecast = forecast_df['forecasted_sales'].max()
min_forecast = forecast_df['forecasted_sales'].min()
max_date = forecast_df[forecast_df['forecasted_sales'] == max_forecast]['date'].values[0]
min_date = forecast_df[forecast_df['forecasted_sales'] == min_forecast]['date'].values[0]

print(f"\n3. KEY TRENDS IDENTIFIED")
print(f"   • Peak Sales Expected: ${max_forecast:,.2f} on {pd.Timestamp(max_date).strftime('%Y-%m-%d')}")
print(f"   • Lowest Sales Expected: ${min_forecast:,.2f} on {pd.Timestamp(min_date).strftime('%Y-%m-%d')}")
print(f"   • Sales Volatility (Std Dev): ${forecast_df['forecasted_sales'].std():,.2f}")

print(f"\n4. BUSINESS RECOMMENDATIONS")
print(f"   ✓ Inventory Planning: Prepare stock for expected demand peak on {pd.Timestamp(max_date).strftime('%Y-%m-%d')}")
print(f"   ✓ Staffing: Allocate more staff during high-sales periods")
print(f"   ✓ Promotions: Consider promotions during low-sales forecast periods")
print(f"   ✓ Cash Flow: Budget for ${forecast_total/30:,.2f} average daily revenue")
print(f"   ✓ Monitoring: Track actual vs. forecasted sales weekly for model improvement")

# ============================================================================
# 11. EXPORT RESULTS
# ============================================================================
print("\n" + "="*80)
print("EXPORTING RESULTS")
print("="*80)

# Save forecast
forecast_export = forecast_df.copy()
forecast_export['date'] = forecast_export['date'].astype(str)
forecast_export.to_csv('output/sales_forecast_30days.csv', index=False)
print("\n✓ Exported: output/sales_forecast_30days.csv")

# Save model
model_path = f"models/{best_model_name.lower().replace(' ', '_')}_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(best_model, f)
print(f"✓ Exported: {model_path}")

# Create summary report
summary = f"""
{'='*80}
SALES & DEMAND FORECASTING - EXECUTIVE SUMMARY
{'='*80}

PROJECT COMPLETION DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DATASET INFORMATION:
  • Total historical data points: {len(daily_sales)} days
  • Time period: {daily_sales['date'].min().date()} to {daily_sales['date'].max().date()}
  • Average daily sales: ${historical_avg:,.2f}
  • Sales range: ${daily_sales['sales'].min():,.2f} to ${daily_sales['sales'].max():,.2f}

MODELS EVALUATED:
  1. Linear Regression - R²: {float(eval_df[eval_df['Model']=='Linear Regression']['Test R²'].iloc[0]):.4f}
  2. Random Forest - R²: {float(eval_df[eval_df['Model']=='Random Forest']['Test R²'].iloc[0]):.4f}
  3. Gradient Boosting - R²: {float(eval_df[eval_df['Model']=='Gradient Boosting']['Test R²'].iloc[0]):.4f}

SELECTED MODEL:
  • Model: {best_model_name}
  • R² Score: {best_r2:.4f} ({best_r2*100:.2f}%)
  • Mean Absolute Error: ${best_mae:,.2f}
  • Prediction Confidence: {(1 - (best_mae/historical_avg))*100:.1f}%

30-DAY FORECAST OUTLOOK:
  • Forecasted average daily sales: ${forecast_avg:,.2f}
  • Total 30-day revenue projection: ${forecast_total:,.2f}
  • Growth vs. historical average: {growth_rate:+.1f}%
  • Peak sales day: {pd.Timestamp(max_date).strftime('%Y-%m-%d')} (${max_forecast:,.2f})
  • Lowest sales day: {pd.Timestamp(min_date).strftime('%Y-%m-%d')} (${min_forecast:,.2f})

KEY BUSINESS DECISIONS:
  1. Use forecasted daily averages for inventory planning
  2. Prepare staffing levels based on high-sales days
  3. Plan promotions for identified low-sales periods
  4. Monitor actual vs. forecasted performance weekly
  5. Update model monthly with new data for continuous improvement

OUTPUT FILES GENERATED:
  ✓ output/01_time_series_analysis.png - Historical sales patterns
  ✓ output/02_model_comparison.png - Model performance comparison
  ✓ output/03_sales_forecast.png - 30-day forecast visualization
  ✓ output/04_feature_importance.png - Key drivers of sales
  ✓ output/sales_forecast_30days.csv - Detailed daily forecast
  ✓ output/model_evaluation_results.csv - Model metrics
  ✓ models/{best_model_name.lower().replace(' ', '_')}_model.pkl - Trained model

NEXT STEPS:
  1. Present visualizations to business stakeholders
  2. Integrate forecast into inventory management system
  3. Review actual vs. forecasted performance weekly
  4. Retrain model monthly with updated data
  5. Monitor forecast accuracy metrics

{'='*80}
"""

with open('output/FORECAST_SUMMARY_REPORT.txt', 'w', encoding='utf-8') as f:
    f.write(summary)

print(f"✓ Exported: output/FORECAST_SUMMARY_REPORT.txt")

print("\n" + "="*80)
print("✅ FORECASTING ANALYSIS COMPLETE!")
print("="*80)
print("\nAll outputs saved to the 'output' folder:")
print("  📊 Visualizations for business presentations")
print("  📈 30-day forecast data")
print("  📋 Executive summary report")
print("\nThe trained model is ready for deployment and can be used for real-time forecasting!")
