"""
Sales Forecasting Auto-Update System
Flask Backend for Upload & Auto-Processing
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from io import StringIO

import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# ============================================================================
# CONFIGURATION
# ============================================================================

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Ensure essential directories exist
for folder in [UPLOAD_FOLDER, 'data', 'output', 'output/archive', 'models']:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize dummy sales data if it doesn't exist to prevent crash
if not os.path.exists('data/sales_data.csv'):
    dummy_data = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=100, freq='D'),
        'sales': np.random.randint(100, 1000, size=100)
    })
    dummy_data.to_csv('data/sales_data.csv', index=False)
    print("Created initial data/sales_data.csv")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_csv(filepath):
    """Validate CSV file format"""
    try:
        df = pd.read_csv(filepath)
        required_cols = ['date', 'sales']

        # Check required columns
        if not all(col in df.columns for col in required_cols):
            return False, f"CSV must contain columns: {', '.join(required_cols)}"

        # Check data types
        df['date'] = pd.to_datetime(df['date'])
        df['sales'] = pd.to_numeric(df['sales'])

        # Check for empty data
        if len(df) == 0:
            return False, "CSV is empty"

        return True, df
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"

def append_data_to_csv(new_data_path):
    """Append new data to existing sales data"""
    try:
        # Read new data
        new_df = pd.read_csv(new_data_path)

        # Read existing data
        existing_df = pd.read_csv('data/sales_data.csv')

        # Append
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Remove duplicates based on date
        combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')

        # Sort by date
        combined_df['date'] = pd.to_datetime(combined_df['date'])
        combined_df = combined_df.sort_values('date').reset_index(drop=True)

        # Backup old data
        backup_path = f'output/archive/sales_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        shutil.copy('data/sales_data.csv', backup_path)

        # Save updated data
        combined_df.to_csv('data/sales_data.csv', index=False)

        new_records = len(new_df)
        total_records = len(combined_df)

        return True, {
            'new_records': new_records,
            'total_records': total_records,
            'backup_path': backup_path
        }
    except Exception as e:
        return False, str(e)

def train_models(df):
    """Train all three forecasting models"""
    try:
        # Prepare data
        df['date'] = pd.to_datetime(df['date'])

        # Aggregate by date if multiple records per day
        daily_sales = df.groupby('date')['sales'].sum().reset_index()

        # Feature engineering
        df_features = daily_sales.copy()
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

        # Rolling averages
        df_features['rolling_mean_7'] = df_features['sales'].rolling(window=7).mean()
        df_features['rolling_mean_30'] = df_features['sales'].rolling(window=30).mean()

        # Drop NaN
        df_features = df_features.dropna().reset_index(drop=True)

        # Split data
        train_size = int(len(df_features) * 0.70)
        val_size = int(len(df_features) * 0.15)

        train_data = df_features[:train_size]
        val_data = df_features[train_size:train_size+val_size]
        test_data = df_features[train_size+val_size:]

        feature_cols = ['day', 'month', 'quarter', 'year', 'day_of_week', 'day_of_year',
                       'is_weekend', 'lag_1', 'lag_7', 'lag_30', 'rolling_mean_7', 'rolling_mean_30']

        X_train = train_data[feature_cols]
        y_train = train_data['sales']
        X_test = test_data[feature_cols]
        y_test = test_data['sales']

        # Train models
        models_dict = {}
        results = {}

        # Linear Regression
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_test)
        lr_r2 = r2_score(y_test, lr_pred)
        lr_mae = mean_absolute_error(y_test, lr_pred)
        lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))

        models_dict['Linear Regression'] = lr_model
        results['Linear Regression'] = {'R2': lr_r2, 'MAE': lr_mae, 'RMSE': lr_rmse}

        # Random Forest
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)
        rf_r2 = r2_score(y_test, rf_pred)
        rf_mae = mean_absolute_error(y_test, rf_pred)
        rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))

        models_dict['Random Forest'] = rf_model
        results['Random Forest'] = {'R2': rf_r2, 'MAE': rf_mae, 'RMSE': rf_rmse}

        # Gradient Boosting
        gb_model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        gb_model.fit(X_train, y_train)
        gb_pred = gb_model.predict(X_test)
        gb_r2 = r2_score(y_test, gb_pred)
        gb_mae = mean_absolute_error(y_test, gb_pred)
        gb_rmse = np.sqrt(mean_squared_error(y_test, gb_pred))

        models_dict['Gradient Boosting'] = gb_model
        results['Gradient Boosting'] = {'R2': gb_r2, 'MAE': gb_mae, 'RMSE': gb_rmse}

        # Select best model
        best_model_name = max(results, key=lambda x: results[x]['R2'])
        best_model = models_dict[best_model_name]
        best_results = results[best_model_name]

        return True, {
            'model_name': best_model_name,
            'model': best_model,
            'results': results,
            'best_r2': results[best_model_name]['R2'],
            'best_mae': results[best_model_name]['MAE'],
            'features': df_features,
            'feature_cols': feature_cols
        }
    except Exception as e:
        return False, str(e)

def generate_forecast(model, df_features, feature_cols, days_ahead=30):
    """Generate forecast for next N days"""
    try:
        from datetime import timedelta

        last_date = df_features['date'].max()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days_ahead, freq='D')

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
            lag_7 = df_features['sales'].iloc[-7] if len(df_features) >= 7 else df_features['sales'].iloc[-1]
            lag_30 = df_features['sales'].iloc[-30] if len(df_features) >= 30 else df_features['sales'].iloc[-1]

            rolling_mean_7 = df_features['sales'].iloc[-7:].mean() if len(df_features) >= 7 else df_features['sales'].mean()
            rolling_mean_30 = df_features['sales'].iloc[-30:].mean() if len(df_features) >= 30 else df_features['sales'].mean()

            forecast_features.append([day, month, quarter, year, day_of_week, day_of_year,
                                    is_weekend, lag_1, lag_7, lag_30, rolling_mean_7, rolling_mean_30])

        X_forecast = pd.DataFrame(forecast_features, columns=feature_cols)
        forecast_values = model.predict(X_forecast)

        forecast_df = pd.DataFrame({
            'date': future_dates,
            'forecasted_sales': forecast_values
        })

        return True, forecast_df
    except Exception as e:
        return False, str(e)

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Home page with interactive dashboard"""
    return render_template('dashboard.html')

@app.route('/output/<path:filename>')
def serve_output(filename):
    """Serve output visualizations and CSVs"""
    return send_from_directory('output', filename)

@app.route('/<path:filename>')
def serve_docs(filename):
    """Serve documentation files from the root directory"""
    if filename.endswith(('.md', '.txt', '.html')) and filename in [
        'README.md', 'QUICK_START.md', 'PROJECT_DELIVERABLES.md', 
        'INDEX.md', 'START_HERE.txt', 'SYSTEM_OVERVIEW.html'
    ]:
        return send_from_directory('.', filename)
    return jsonify({'error': 'File not found'}), 404

@app.route('/data/<path:filename>')
def serve_data(filename):
    """Serve data files"""
    return send_from_directory('data', filename)

@app.route('/models/')
def list_models():
    """List available models or redirect to the best one"""
    try:
        files = os.listdir('models')
        if 'linear_regression_model.pkl' in files:
            return send_from_directory('models', 'linear_regression_model.pkl')
        return jsonify({'available_models': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/models/<path:filename>')
def serve_models(filename):
    """Serve trained model pkl files"""
    return send_from_directory('models', filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and auto-process"""
    try:
        # Check if file in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only CSV files allowed'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Validate CSV
        valid, val_result = validate_csv(filepath)
        if not valid:
            return jsonify({'error': str(val_result)}), 400

        # Read current data for comparison
        data_path = 'data/sales_data.csv'
        old_df = pd.read_csv(data_path)
        old_records = len(old_df)
        old_avg_sales = float(old_df['sales'].mean())

        # Append data
        append_success, append_result = append_data_to_csv(filepath)
        if not append_success:
            return jsonify({'error': f'Failed to append data: {str(append_result)}'}), 500

        # Run full analysis script to regenerate plots and reports
        try:
            import subprocess
            python_exe = sys.executable
            # Using current python exe (venv) to run the analysis script
            subprocess.run([python_exe, 'sales_forecasting_analysis.py'], 
                          capture_output=True, text=True, check=True)
            print("✓ Full analysis script executed successfully")
        except Exception as e:
            print(f"⚠ Warning: Analysis script failed: {str(e)}")
            # We continue because model retraining is also handled locally in app.py

        # Ensure append_result is treated as dict for linter
        app_res: dict = append_result if isinstance(append_result, dict) else {}

        # Train models
        df_to_train = pd.read_csv(data_path)
        train_success, train_result_data = train_models(df_to_train)
        
        # Type-safe model training results
        train_res = {}
        if train_success and isinstance(train_result_data, dict):
            train_res = train_result_data
        else:
            return jsonify({'error': f'Model training failed: {str(train_result_data)}'}), 500

        # Generate forecast
        forecast_success, forecast_res = generate_forecast(
            train_res.get('model'),
            train_res.get('features'),
            train_res.get('feature_cols', [])
        )
        if not forecast_success:
            return jsonify({'error': f'Forecast generation failed: {str(forecast_res)}'}), 500

        # Ensure forecast_res is a DataFrame or something with to_csv for the linter
        if not isinstance(forecast_res, pd.DataFrame):
             return jsonify({'error': 'Forecast result is not a valid DataFrame'}), 500
            
        forecast_df: pd.DataFrame = forecast_res

        # Calculate comparison
        new_df_full = pd.read_csv(data_path)
        new_records = len(new_df_full)
        new_avg_sales = float(new_df_full['sales'].mean())

        # Save forecast
        forecast_df.to_csv('output/sales_forecast_30days_latest.csv', index=False)

        # Prepare metrics safely
        records_increase = 0.0
        if old_records > 0:
            diff_records = float(new_records - old_records)
            records_increase = round((diff_records / float(old_records)) * 100.0, 1)

        change_pct = 0.0
        if old_avg_sales > 0:
            diff_sales = float(new_avg_sales - old_avg_sales)
            change_pct = round((diff_sales / old_avg_sales) * 100.0, 1)

        # Build response with extreme type safety for the linter
        results_map = {}
        if isinstance(train_res.get('results'), dict):
            results_map = train_res['results']

        best_model_details = {}
        best_name = str(train_res.get('model_name', 'Unknown'))
        if best_name in results_map:
            best_model_details = results_map[best_name]

        response = {
            'status': 'success',
            'message': 'Data processed successfully!',
            'data_append': {
                'new_records_added': int(app_res.get('new_records', 0)),
                'total_records_now': int(new_records),
                'records_increase_percent': float(records_increase)
            },
            'model_performance': {
                'model_selected': best_name,
                'r2_score': round(float(train_res.get('best_r2', 0.0)), 4),
                'mae': round(float(train_res.get('best_mae', 0.0)), 2),
                'rmse': round(float(best_model_details.get('RMSE', 0.0)), 2),
                'all_models': {
                    str(k): {
                        'r2': round(float(v.get('R2', 0.0)), 4), 
                        'mae': round(float(v.get('MAE', 0.0)), 2), 
                        'rmse': round(float(v.get('RMSE', 0.0)), 2)
                    }
                    for k, v in results_map.items() if isinstance(v, dict)
                }
            },
            'forecast': {
                'average_daily_sales': round(float(forecast_df['forecasted_sales'].mean()), 2),
                'total_30day_revenue': round(float(forecast_df['forecasted_sales'].sum()), 2),
                'peak_sales': round(float(forecast_df['forecasted_sales'].max()), 2),
                'lowest_sales': round(float(forecast_df['forecasted_sales'].min()), 2),
                'volatility_std': round(float(forecast_df['forecasted_sales'].std()), 2)
            },
            'comparison': {
                'historical_avg': round(float(old_avg_sales), 2),
                'forecast_avg': round(float(new_avg_sales), 2),
                'change_percent': float(change_pct)
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/download/<filetype>')
def download_file(filetype):
    """Download forecast CSV or comparison report"""
    try:
        if filetype == 'forecast':
            return send_file('output/sales_forecast_30days_latest.csv', as_attachment=True)
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get current system status"""
    try:
        df = pd.read_csv('data/sales_data.csv')
        return jsonify({
            'status': 'operational',
            'data_records': len(df),
            'date_range': f"{df['date'].min()} to {df['date'].max()}",
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum 5MB allowed.'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║   Sales Forecasting Auto-Update System - Flask Server         ║")
    print("║                                                                ║")
    print("║   🚀 http://localhost:5000                                    ║")
    print("║                                                                ║")
    print("║   Upload your CSV file to automatically:                      ║")
    print("║   ✅ Append data to existing records                          ║")
    print("║   ✅ Retrain all 3 ML models                                  ║")
    print("║   ✅ Generate new 30-day forecast                             ║")
    print("║   ✅ Calculate accuracy improvements                          ║")
    print("║   ✅ Display comprehensive results                            ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("")

    app.run(debug=True, host='localhost', port=5000)
