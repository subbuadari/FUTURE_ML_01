# 📈 Sales Demand Forecaster: AI-Powered Analytics Hub
License: MIT Python Flask scikit-learn pandas

A premium, enterprise-ready Machine Learning solution that analyzes historical data, engineers time-based features, and automatically predicts future sales and demand.

## 📸 Preview
| Dashboard | Sales Trends | 30-Day Forecast |
|---|---|---|
| Upload CSV, trigger training and auto-evaluate models | View historical sales, rolling averages, and season trends | Generate 30-day confidence intervals & KPIs for business |

## 🚀 Features
- **📤 Automated Smart Upload** — Upload `sales_data.csv` to instantly update records and trigger retraining
- **🧠 Triple-Threat ML Engine** — Automatically trains and evaluates Linear Regression, Random Forest, and Gradient Boosting models
- **🏆 Dynamic Model Selection** — The system auto-selects the highest performing model based on R² and RMSE
- **📅 Time-Series Feature Engineering** — Extracts time, lag, seasonal, and rolling average features
- **📊 Visual Analytics** — Generates business-ready visualizations (trends, model comparison, feature importance, forecasts)
- **🔍 30-Day Forecasting** — Generates actionable 30-day forecast with confidence intervals
- **📥 Export Reports** — Download `.csv` forecast data, evaluation metrics, and executive summaries
- **👑 Direct Model Download** — Download the winning trained `.pkl` models directly from the dashboard

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| **Backend** | Python 3.7+, Flask |
| **ML & Data** | scikit-learn, pandas, numpy |
| **Frontend** | HTML5, Vanilla JS, CSS3 (Emerald UI) |
| **Visualizations**| Matplotlib, Seaborn |

## 📦 Project Assets (Dataset & Models)

> [!IMPORTANT]  
> **Download Requirement:** To keep this repository lightweight and fast, large binary files (trained models) and datasets are stored externally on Google Drive.  
> 
> **[🔗 Download Project Assets (Google Drive)](https://drive.google.com/drive/folders/1xBmeOIZK7kehjpPJpcDX4_HXlAGvWZte?usp=sharing)**

Place the downloaded `sales_data.csv` inside the `data/` folder, and the `.pkl` files inside the `models/` folder.

## 📋 CSV Format
Your upload CSV should follow this structure (`sales_data.csv`):

```csv
date,store,item,sales
2021-01-01,1,1,15
2021-01-02,1,1,18
```

*(Note: The system automatically handles missing values and aggregates across stores/items)*

## 🚦 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/subbuadari/FUTURE_ML_01.git
cd FUTURE_ML_01
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Verify external assets**
Ensure `sales_data.csv` is inside the `data/` folder and models in `models/`.

5. **Run the Application**

*To launch the beautiful Web Dashboard:*
```bash
python app.py
```
*Open in browser:* `http://127.0.0.1:5000`

*To trigger the pure Script Pipeline:*
```bash
python sales_forecasting_analysis.py
```

## 📖 How It Works
```text
Upload CSV (sales_data.csv)
     │
     ▼
Data Preprocessing (Aggregations, Missing Values)
     │
     ├──► Feature Engineering (Lag, Rolling Avg, Seasonal, Time-based)
     │
     ├──► Train Models (Linear Reg, Random Forest, Gradient Boosting)
     │
     ├──► Evaluate & Auto-Select Best Model (Highest R² & lowest RMSE)
     │
     └──► Generate 30-Day Forecast & Confidence Intervals
              │
              ▼
    Visual Dashboard & Executive Reports
```

## 📁 Project Structure
```text
FUTURE_ML_01/
├── app.py                          # Flask application & Hub API
├── sales_forecasting_analysis.py   # Main ML pipeline logic
├── create_dataset.py               # Synthetic dataset generator
├── DASHBOARD.html                  # Main Web UI (Emerald Theme)
├── SYSTEM_OVERVIEW.html            # Stakeholder overview page
├── data/                           # [External] sales_data.csv
├── models/                         # [External] Trained .pkl models
├── static/                         # CSS & JS assets
├── templates/                      # Flask HTML templates
├── notebooks/                      # Interactive Jupyter notebooks
├── requirements.txt                # Python dependencies
└── .gitignore                      # Git exclusion rules
```

## ⚖️ License
This project is licensed under the MIT License — see the LICENSE file for details.

## 🏆 Internship Attribution & Above-and-Beyond Features

> **FutureIntern Machine Learning Track — Task 1: Sales & Demand Forecasting**  
> Submitted as part of the FutureIntern ML Internship Program.

While the core internship task required a basic forecasting model in a notebook, this project was engineered as a **complete, enterprise-grade ML product**:

| 🎯 What They Asked For | 🚀 What We Actually Built |
|---|---|
| Apply basic regression or time-series forecasting. | **Triple-Threat Dynamic Auto-Selecting Engine:** Automatically trains Linear Regression, Random Forest, & Gradient Boosting, and auto-selects the winner based on live R² scores! |
| Clear visualizations of predictions. | **Beautiful Web Dashboard:** A full-stack Flask app with an Emerald UI frontend for a highly interactive, real-world store owner experience. |
| Clean data & engineer time-based features. | **Automated Retraining Pipeline:** Users upload a new `sales_data.csv` in the browser, and the backend cleans it, engineers rolling averages, and retrains all models instantly. |
| A short explanation of the forecast and business plans. | **Automated Executive Summaries:** Code automatically generates actionable, plain-English business reports to hand straight to management. |

## 🙋‍♂️ Author
**Subbu Adari**  
GitHub: [@subbuadari](https://github.com/subbuadari)
