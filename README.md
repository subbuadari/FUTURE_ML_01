# Sales & Demand Forecasting System

A complete machine learning solution for predicting future sales and demand based on historical business data.

## 📋 Project Overview

This project implements an end-to-end sales forecasting system that:
- Analyzes 3 years of historical sales data (2021-2023)
- Extracts and engineers time-based features
- Trains multiple forecasting models (Linear Regression, Random Forest, Gradient Boosting)
- Evaluates model performance on hold-out test sets
- Generates actionable 30-day sales forecasts
- Provides business-ready visualizations and insights

## 🎯 Key Features

✅ **Data Preparation**
- Handles missing values and outliers
- Aggregates sales across multiple stores and product categories
- Performs proper time-series train-test split

✅ **Feature Engineering**
- Time-based features (day, month, quarter, year, day of week)
- Lag features (previous day, week, month sales)
- Rolling averages (7-day and 30-day)
- Seasonality indicators

✅ **Model Training**
- Linear Regression - baseline model
- Random Forest - captures non-linear patterns
- Gradient Boosting - optimal performance model

✅ **Evaluation Metrics**
- R² Score - explains variance explained by model
- RMSE - penalizes large errors
- MAE - mean absolute prediction error

✅ **Forecasting & Visualization**
- 30-day sales forecast with confidence intervals
- Time-series plots showing trends and seasonality
- Model comparison visualizations
- Feature importance analysis
- Business-friendly executive summary

## 📁 Project Structure

```
ML/
├── data/                          # Historical sales dataset
├── notebooks/                     # Jupyter notebook with analysis
├── models/                        # Saved trained model
├── output/                        # Results and visualizations
├── static/                        # Frontend assets (CSS/JS)
├── templates/                     # HTML templates for Web Dashboard
├── app.py                          # Flask Web Dashboard & API
├── sales_forecasting_analysis.py   # Main analysis script
├── create_dataset.py               # Dataset generation script
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🌐 Web Dashboard & Automated Update Hub

The system features a high-performance Flask-based dashboard that automates the entire ML lifecycle:

### Core Automated Workflow:
- **Smart Data Upload**: Upload a new CSV to automatically append data, backup old databases, and trigger a full system refresh.
- **Auto-Retraining Pipeline**: The system automatically retrains all 3 ML models on every update.
- **Dynamic Model Selection**: Best-performing model is automatically selected for forecast generation.
- **Direct Model Downloads**: Trained `.pkl` models are now directly downloadable from the dashboard.

### Running the Dashboard:
```bash
python app.py
```
Access the hub at `http://localhost:5000`.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify the dataset exists:**
```bash
# Check if sales_data.csv is in the data folder
ls data/sales_data.csv
```

### Running the Analysis

**Execute the complete forecasting pipeline:**
```bash
python sales_forecasting_analysis.py
```

This will:
1. Load and explore the sales data
2. Create visualizations of historical trends
3. Engineer time-based features
4. Train three different forecasting models
5. Evaluate model performance
6. Generate 30-day sales forecast
7. Save all outputs (visualizations, data, report)

**Or use the Jupyter notebook for interactive analysis:**
```bash
jupyter notebook notebooks/sales_forecasting.ipynb
```

## 📊 Understanding the Results

### Model Evaluation
The system evaluates three models:

| Metric | Description |
|--------|-------------|
| **R² Score** | How much variance the model explains (0-1, higher is better) |
| **RMSE** | Root Mean Squared Error - average prediction error in dollars |
| **MAE** | Mean Absolute Error - average absolute prediction error |

### Output Files

1. **01_time_series_analysis.png**
   - Shows daily sales over time
   - Reveals trends and seasonality patterns
   - Helps identify peak sales periods

2. **02_model_comparison.png**
   - Compares actual vs. predicted sales on test set
   - Shows R², RMSE, and MAE for all three models
   - Helps select the best model

3. **03_sales_forecast.png**
   - 30-day forecast with confidence intervals
   - Weekly breakdown of projected sales
   - Ready for business presentations

4. **04_feature_importance.png**
   - Shows which features drive sales predictions
   - Helps understand what factors are most important
   - (Available for Random Forest and Gradient Boosting)

5. **sales_forecast_30days.csv**
   - Detailed daily forecast data
   - Can be imported to Excel or business dashboards

6. **model_evaluation_results.csv**
   - Complete evaluation metrics for all models
   - Useful for documentation and review

7. **FORECAST_SUMMARY_REPORT.txt**
   - Executive summary for stakeholders
   - Key insights and recommendations
   - Next steps for implementation

## 💡 Business Insights

### What the Forecast Tells You

**Historical Patterns:**
- Average daily sales over the past 3 years
- Seasonal trends (which periods are typically higher/lower)
- Day-of-week effects (weekends vs. weekdays)

**30-Day Forecast:**
- Expected daily sales for the next month
- Peak sales opportunities
- Low-sales periods for planning promotions
- Confidence intervals for planning buffer stock

### How to Use Forecasts

**Inventory Planning:**
- Prepare extra stock for forecasted peak sales days
- Reduce stock for periods with lower expected demand
- Optimize warehouse space allocation

**Staffing:**
- Schedule more staff on high-sales forecast days
- Plan maintenance or training during low-sales periods
- Improve labor cost efficiency

**Financial Planning:**
- Budget revenue based on 30-day forecast
- Plan promotions during low-sales periods
- Optimize marketing spend timing

**Marketing & Promotions:**
- Time promotions to boost sales during identified low periods
- Capitalize on natural high-sales periods
- Test new strategies during stable periods

## 📈 Model Performance Interpretation

**R² Score 0.85+**: Excellent model - explains 85%+ of sales variation
**R² Score 0.70-0.85**: Good model - reliable for business decisions
**R² Score 0.50-0.70**: Fair model - consider combining with domain expertise
**R² Score <0.50**: Poor model - needs improvement before deployment

The Mean Absolute Error (MAE) shows the average dollar amount by which predictions might be off, helping you understand the confidence level needed for your decisions.

## 🔄 Continuous Improvement

### Monthly Retraining Process

1. **Collect new sales data** from the past month
2. **Run the analysis script** to retrain models
3. **Compare new R² scores** with previous month
4. **Review forecast accuracy** against actual results
5. **Update business strategies** based on findings

### Monitoring Forecast Accuracy

Track these metrics weekly:
- **Forecast vs. Actual**: How close were predictions?
- **Error Trends**: Are certain days/products harder to predict?
- **Seasonal Changes**: Are patterns shifting?

## 🛠️ Technical Details

### Feature Engineering Process

**Time-based Features:**
- Day of month (1-31)
- Month (1-12)
- Quarter (1-4)
- Year
- Day of week (0-6, Monday-Sunday)
- Day of year (1-365)
- Is weekend (binary)

**Lag Features:**
- Previous day's sales
- Previous week's sales (7 days ago)
- Previous month's sales (30 days ago)

**Rolling Averages:**
- 7-day moving average
- 30-day moving average

### Model Selection Criteria

The system automatically selects the best model based on:
1. **Highest R² Score** on test set (primary metric)
2. **Lowest RMSE** (secondary consideration)
3. **Lowest MAE** (for practical business error bounds)

## ⚠️ Limitations & Assumptions

1. **Historical data is representative**: Past patterns continue into the future
2. **No major market disruptions**: Assumes normal business conditions
3. **Regular seasonality**: Sales patterns repeat annually
4. **Feature relationships remain stable**: Relationships between features and sales don't drastically change
5. **No external events**: Model doesn't account for holidays, promotions, or competitor actions

For major business changes or external events, consider:
- Manual adjustment of forecasts
- Adding external features (holidays, marketing spend, competitor actions)
- More frequent model retraining

## 📞 Support & Issues

If you encounter issues:

1. **Check data format**: Ensure sales_data.csv has required columns (date, sales)
2. **Verify date format**: Dates should be in YYYY-MM-DD format
3. **Check for missing values**: The system handles some missing data but not all scenarios
4. **Review Python version**: Requires Python 3.7+

## 📚 Further Learning

### Recommended Reading
- Time Series Forecasting: https://en.wikipedia.org/wiki/Time_series
- Seasonality in forecasting: https://en.wikipedia.org/wiki/Seasonality
- Scikit-learn documentation: https://scikit-learn.org/stable/

### Advanced Techniques
- ARIMA/SARIMA models for pure time-series approaches
- LSTM neural networks for complex patterns
- Prophet (Facebook) for built-in seasonality handling
- MultiStep forecasting for longer-term predictions

## 📝 License & Attribution

This project is provided as an educational tool for machine learning and business analytics.

---

**Ready to forecast your sales? Run `python sales_forecasting_analysis.py` to get started!**
