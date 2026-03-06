/* ============================================================================
   Sales Forecasting Auto-Update System - JavaScript Logic
   ============================================================================ */

let selectedFile = null;
let processingProgress = 0;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    loadSystemStatus();
    setupUploadArea();
});

// ============================================================================
// LOAD SYSTEM STATUS
// ============================================================================

function loadSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'operational') {
                document.getElementById('recordCount').textContent = data.data_records + ' records';
                document.getElementById('lastUpdate').textContent = data.last_update;
            }
        })
        .catch(error => console.error('Error loading status:', error));
}

// ============================================================================
// UPLOAD AREA SETUP
// ============================================================================

function setupUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Click to select
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag over
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    // Drop
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

// ============================================================================
// FILE SELECTION HANDLER
// ============================================================================

function handleFileSelection(file) {
    // Validate file type
    if (!file.name.endsWith('.csv')) {
        showError('Only CSV files are allowed');
        return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
        showError('File is too large. Maximum 5MB allowed.');
        return;
    }

    selectedFile = file;

    // Show file info
    document.getElementById('fileInfo').style.display = 'flex';
    document.getElementById('fileName').textContent = '✅ ' + file.name;
    document.getElementById('processBtn').style.display = 'block';
}

// ============================================================================
// PROCESS FILE
// ============================================================================

function processFile() {
    if (!selectedFile) {
        showError('No file selected');
        return;
    }

    // Hide upload section
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';

    // Show processing section
    document.getElementById('processingSection').style.display = 'block';

    // Reset progress
    processingProgress = 0;
    updateProgress(0);

    // Create FormData
    const formData = new FormData();
    formData.append('file', selectedFile);

    // Step 1: Validating
    updateStep('step1', 'processing', 'Validating File', 25);

    // Send to server
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => Promise.reject(data));
        }
        return response.json();
    })
    .then(data => {
        // Step 2: Appended
        updateStep('step1', 'complete', 'File Validated', 25);
        updateStep('step2', 'processing', `Appending ${data.data_append.new_records_added} Records`, 50);
        updateProgress(50);

        // Simulate step 2 completion
        setTimeout(() => {
            updateStep('step2', 'complete', `Appended ${data.data_append.new_records_added} Records`, 50);
            updateStep('step3', 'processing', 'Training Models', 75);
            updateProgress(75);

            // Simulate step 3 completion
            setTimeout(() => {
                updateStep('step3', 'complete', 'Models Trained', 75);
                updateStep('step4', 'processing', 'Generating Forecast', 100);
                updateProgress(100);

                // Simulate step 4 completion
                setTimeout(() => {
                    updateStep('step4', 'complete', 'Forecast Generated', 100);
                    displayResults(data);
                }, 1000);
            }, 1500);
        }, 1000);
    })
    .catch(error => {
        showError(error.error || 'An error occurred during processing');
    });
}

// ============================================================================
// UPDATE PROGRESS
// ============================================================================

function updateProgress(percent) {
    processingProgress = percent;
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = percent + '%';
}

function updateStep(stepId, status, label, progress) {
    const step = document.getElementById(stepId);
    const statusEl = step.querySelector('.step-status');

    step.classList.remove('active', 'complete');

    if (status === 'processing') {
        step.classList.add('active');
        statusEl.textContent = '⏳ ' + label;
    } else if (status === 'complete') {
        step.classList.add('complete');
        statusEl.textContent = '✅ ' + label;
    } else {
        statusEl.textContent = '';
    }

    updateProgress(progress);
}

// ============================================================================
// DISPLAY RESULTS
// ============================================================================

function displayResults(data) {
    // Hide processing section
    document.getElementById('processingSection').style.display = 'none';

    // Show results section
    document.getElementById('resultsSection').style.display = 'block';

    // Data Statistics
    document.getElementById('newRecords').textContent = data.data_append.new_records_added;
    document.getElementById('totalRecords').textContent = data.data_append.total_records_now;
    document.getElementById('dataGrowth').textContent = '+' + data.data_append.records_increase_percent + '%';

    // Model Performance
    document.getElementById('modelName').textContent = data.model_performance.model_selected;
    document.getElementById('r2Score').textContent = (data.model_performance.r2_score * 100).toFixed(2) + '%';
    document.getElementById('maeScore').textContent = '$' + data.model_performance.mae.toLocaleString();

    // Forecast Overview
    document.getElementById('avgDaily').textContent = '$' + data.forecast.average_daily_sales.toLocaleString();
    document.getElementById('total30Day').textContent = '$' + data.forecast.total_30day_revenue.toLocaleString();
    document.getElementById('peakSales').textContent = '$' + data.forecast.peak_sales.toLocaleString();

    // Comparison
    document.getElementById('historyAvg').textContent = '$' + data.comparison.historical_avg.toLocaleString();
    document.getElementById('forecastAvg').textContent = '$' + data.comparison.forecast_avg.toLocaleString();
    const changeSymbol = data.comparison.change_percent >= 0 ? '+' : '';
    document.getElementById('changePercent').textContent = changeSymbol + data.comparison.change_percent.toFixed(1) + '%';

    // Models Comparison Table
    displayModelsTable(data.model_performance.all_models);

    // Scroll to results
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 500);
}

function displayModelsTable(models) {
    let htmlContent = '';

    Object.keys(models).forEach(modelName => {
        const model = models[modelName];
        htmlContent += `
            <div class="table-row">
                <div><strong>${modelName}</strong></div>
                <div>${(model.r2 * 100).toFixed(2)}%</div>
                <div>$${model.mae.toLocaleString()}</div>
                <div>$${model.rmse.toLocaleString()}</div>
            </div>
        `;
    });

    document.getElementById('modelsTableBody').innerHTML = htmlContent;
}

// ============================================================================
// DOWNLOAD FORECAST
// ============================================================================

function downloadForecast() {
    // In a real scenario, create and download a file
    // For now, show a message
    const link = document.createElement('a');
    link.href = '/api/download/forecast';
    link.download = 'sales_forecast_30days.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ============================================================================
// RESET / START OVER
// ============================================================================

function resetUpload() {
    // Hide all sections
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';

    // Reset file
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('processBtn').style.display = 'none';

    // Reload status
    loadSystemStatus();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

function showError(message) {
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'block';
    document.getElementById('errorMessage').textContent = message;

    // Reset file
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('processBtn').style.display = 'none';
}
