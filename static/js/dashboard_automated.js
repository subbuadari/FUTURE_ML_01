/* ============================================================================
   Dashboard Automated Update Logic
   ============================================================================ */

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const startBtn = document.getElementById('start-update-btn');
const fileDisplay = document.getElementById('file-display');
const progressHub = document.getElementById('progress-hub');
const progressBar = document.getElementById('progress-bar');
const alertZone = document.getElementById('alert-zone');

let selectedFile = null;

// Setup Drag & Drop
if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    startBtn.addEventListener('click', runUpdate);
}

function handleFile(file) {
    if (!file.name.endsWith('.csv')) {
        showAlert('Please upload a CSV file only.', 'error');
        return;
    }
    selectedFile = file;
    fileDisplay.textContent = `✅ Selected: ${file.name}`;
    fileDisplay.classList.remove('hidden');
    startBtn.disabled = false;
    alertZone.innerHTML = '';
}

function updateProgress(percent, step) {
    progressBar.style.width = percent + '%';
    document.querySelectorAll('.update-step').forEach(s => s.classList.remove('active'));
    if (step) {
        const stepEl = document.getElementById(`step-${step}`);
        if (stepEl) stepEl.classList.add('active');
    }
}

async function runUpdate() {
    if (!selectedFile) return;

    startBtn.disabled = true;
    progressHub.style.display = 'block';
    updateProgress(10, 1);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        // Step 1: Upload & Initial Process
        updateProgress(25, 1);
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Server error during processing');
        }

        const data = await response.json();

        // Simulate processing steps for visual feedback
        updateProgress(50, 2);
        await new Promise(r => setTimeout(r, 800));

        updateProgress(75, 3);
        await new Promise(r => setTimeout(r, 1200));

        // Step 4: UI Refresh
        updateProgress(90, 4);
        refreshUI(data);

        updateProgress(100, 4);
        showAlert(`Dashboard successfully updated with ${data.data_append.new_records_added} new records!`, 'success');

        // Mark steps as complete
        document.querySelectorAll('.update-step').forEach(s => s.classList.add('complete'));

    } catch (error) {
        showAlert(error.message, 'error');
        progressHub.style.display = 'none';
        startBtn.disabled = false;
    }
}

function refreshUI(data) {
    // 1. Update Overview Metrics
    if (document.getElementById('m-avg-sales')) {
        document.getElementById('m-avg-sales').textContent = `$${data.forecast.average_daily_sales.toLocaleString()}`;
        document.getElementById('m-total-revenue').textContent = `$${data.forecast.total_30day_revenue.toLocaleString()}`;

        const growthEl = document.getElementById('m-growth');
        const change = data.comparison.change_percent;
        growthEl.textContent = `${change >= 0 ? '+' : ''}${change}%`;

        document.getElementById('m-peak-sales').textContent = `$${data.forecast.peak_sales.toLocaleString()}`;
        document.getElementById('m-accuracy').textContent = `${(data.model_performance.r2_score * 100).toFixed(1)}%`;
        document.getElementById('m-error').textContent = `±$${data.model_performance.mae.toLocaleString()}`;
    }

    // 2. Refresh Chart Images (Add timestamp to bypass cache)
    const t = new Date().getTime();
    ['img-01', 'img-02', 'img-03', 'img-04'].forEach(id => {
        const img = document.getElementById(id);
        if (img) {
            const baseSrc = img.src.split('?')[0];
            img.src = `${baseSrc}?t=${t}`;
        }
    });

    // 3. Update Model Download Links
    const modelName = data.model_performance.model_selected;
    const modelFile = `${modelName.toLowerCase().replace(/ /g, '_')}_model.pkl`;
    const modelPath = `models/${modelFile}`;

    if (document.getElementById('link-model-btn')) {
        document.getElementById('link-model-btn').href = modelPath;
    }
    if (document.getElementById('link-model-file')) {
        document.getElementById('link-model-file').href = modelPath;
    }

    // 4. Scroll to overview to show results
    setTimeout(() => {
        switchTab('overview');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 1500);
}

function showAlert(message, type) {
    alertZone.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}
