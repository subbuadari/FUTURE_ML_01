"""
Sales Forecasting Auto-Update System
Flask Backend for Upload & Auto-Processing
"""

import os
import sys
import subprocess
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

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Home page with interactive dashboard"""
    try:
        mod_time = os.path.getmtime('data/sales_data.csv')
        last_update = datetime.fromtimestamp(mod_time).strftime('%B %d, %Y')
    except Exception:
        last_update = datetime.now().strftime('%B %d, %Y')
    return render_template('dashboard.html', last_update=last_update)

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

        # Run full analysis script as the single source of truth
        try:
            python_exe = sys.executable
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sales_forecasting_analysis.py')
            # Force UTF-8 encoding for the subprocess environment to prevent Windows 'charmap' errors
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            # Capture as bytes to avoid encoding issues during the run itself
            result = subprocess.run([python_exe, script_path], 
                          capture_output=True, check=True, env=env)
            print("✓ Full analysis script executed successfully")
        except subprocess.CalledProcessError as e:
            try:
                # Decoded manually with 'replace' to ensure it's ASCII-safe for logging
                safe_stdout = e.stdout.decode('utf-8', 'replace').encode('ascii', 'backslashreplace').decode('ascii')
                safe_stderr = e.stderr.decode('utf-8', 'replace').encode('ascii', 'backslashreplace').decode('ascii')
                error_msg = f"Analysis script failed (exit {e.returncode}):\nSTDOUT: {safe_stdout}\nSTDERR: {safe_stderr}"
                print(error_msg)
                return jsonify({'error': error_msg}), 500
            except Exception as inner_e:
                return jsonify({'error': f"Analysis script failed (exit {e.returncode}) and error report failed: {str(inner_e)}"}), 500
        except Exception as e:
            try:
                error_msg = f"Server error during analysis: {str(e)}".encode('ascii', 'backslashreplace').decode('ascii')
                print(error_msg)
                return jsonify({'error': error_msg}), 500
            except:
                return jsonify({'error': "Server error during analysis (and error message construction failed)"}), 500

        # Read results generated by the script
        try:
            # 1. Model Evaluation Results
            eval_df = pd.read_csv('output/model_evaluation_results.csv')
            # 2. Latest Forecast
            forecast_df = pd.read_csv('output/sales_forecast_30days.csv')
            # 3. Final Sales Data for comparison metrics
            new_df_full = pd.read_csv(data_path)
        except Exception as e:
            return jsonify({'error': f'Failed to read analysis results: {str(e)}'}), 500

        # Calculate metrics for response
        new_records = len(new_df_full)
        new_avg_sales = float(new_df_full['sales'].mean())
        
        records_increase = 0.0
        if old_records > 0:
            records_increase = round(((new_records - old_records) / old_records) * 100.0, 1)

        change_pct = 0.0
        if old_avg_sales > 0:
            change_pct = round(((new_avg_sales - old_avg_sales) / old_avg_sales) * 100.0, 1)

        # Get best model from evaluation results
        # Best model is based on Test R2 as per the script logic
        best_model_row = eval_df.iloc[eval_df['Test R²'].idxmax()]
        
        # Build all_models map
        all_models = {}
        for _, row in eval_df.iterrows():
            all_models[str(row['Model'])] = {
                'r2': round(float(row['Test R²']), 4),
                'mae': round(float(row['Test MAE']), 2),
                'rmse': round(float(row['Test RMSE']), 2)
            }

        response = {
            'status': 'success',
            'message': 'Data processed successfully!',
            'data_append': {
                'new_records_added': int(append_result.get('new_records', 0)) if isinstance(append_result, dict) else 0,
                'total_records_now': int(new_records),
                'records_increase_percent': float(records_increase)
            },
            'model_performance': {
                'model_selected': str(best_model_row['Model']),
                'r2_score': round(float(best_model_row['Test R²']), 4),
                'mae': round(float(best_model_row['Test MAE']), 2),
                'rmse': round(float(best_model_row['Test RMSE']), 2),
                'all_models': all_models
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

    app.run(debug=True, host='localhost', port=5000, use_reloader=False)
