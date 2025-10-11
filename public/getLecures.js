    let extractedText = "";
    let sectionCount = 0;

    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const progress = document.getElementById('progress');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');
    const progressStatus = document.getElementById('progressStatus');
    const result = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const textContent = document.getElementById('textContent');
    const rawDataContent = document.getElementById('rawDataContent');
    const sectionCountElement = document.getElementById('sectionCount');

    // --- Reset all UI states ---
    function resetUI() {
        uploadArea.classList.remove('uploading');
        progress.style.display = 'none';
        result.style.display = 'none';
        errorDiv.style.display = 'none';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        sectionCountElement.textContent = '0';
    }

    // --- Handle new file selection ---
    function handleFile(file) {
        resetUI();

        if (!file) return;

        if (file.type !== 'application/pdf') {
            showAlert('❌ Please select a valid PDF file');
            return;
        }

        if (file.size > 100 * 1024 * 1024) {
            showAlert('⚠️ File size must be less than 100MB');
            return;
        }

        uploadPDF(file);
    }

    // --- Upload and process PDF ---
    function uploadPDF(file) {
        const formData = new FormData();
        formData.append('pdf', file);
        progress.style.display = 'block';
        updateProgress(0, "Starting PDF processing...");

        fetch('/get_lectures', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.body) throw new Error("No response body");
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            const readStream = () => reader.read().then(({ done, value }) => {
                if (done) return;
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            handleServerEvent(data, file.name);
                        } catch (e) {
                            console.warn('Non-JSON line:', line);
                        }
                    }
                });

                return readStream();
            });

            return readStream();
        })
        .catch(err => {
            showAlert('🚫 Network error: ' + err.message);
        });
    }

    // --- Handle server-sent events ---
    function handleServerEvent(data, fileName) {
        switch (data.type) {
            case 'progress':
                updateProgress(data.progress,  `${fileName} PDF Processed: ${data.progress}%`);
                break;
            case 'complete':
                if (data.success) displayResults(data, fileName);
                else showAlert(data.error || 'Processing failed');
                break;
            case 'error':
                showAlert(data.error);
                break;
        }
    }

    // --- Update progress bar ---
    function updateProgress(percent, message) {
        progressBar.style.width = percent + '%';
        progressBar.setAttribute('aria-valuenow', percent);
        progressText.textContent = percent + '%';
        progressStatus.textContent = message;
        uploadArea.style.display = 'none';
        if (percent === 100) {
            progressStatus.innerHTML = '<small>Finalizing results...</small>';
            setTimeout(() => {
                uploadArea.style.display = 'block';
            }, 1500);
        }
    }

    // --- Display processed results ---
    function displayResults(data, fileName) {
        progress.style.display = 'none';
        const lectures = JSON.parse(data.lectures);
        sectionCount = Object.keys(lectures).length;

        sectionCountElement.textContent = sectionCount;
        let html = '<h5>Results of ' + fileName + ':</h5><div class="list-group">';
        Object.entries(lectures).forEach(([title, info]) => {
            html += `
                <div class="list-group-item rounded-0">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${title}</h6>
                        <small>Pages ${info.start_page} - ${info.end_page}</small>
                    </div>
                </div>`;
        });
        html += '</div>';

        textContent.innerHTML = html;
        rawDataContent.textContent = data.lectures;
        extractedText = data.lectures;
        result.style.display = 'block';
        showAlert('✅ PDF processed successfully!');
    }

    // --- Custom Alert ---
    function showAlert(message) {
        let alertBox = document.getElementById('customAlert');
        if (!alertBox) {
            alertBox = document.createElement('div');
            alertBox.id = 'customAlert';
            document.body.appendChild(alertBox);
        }

        alertBox.textContent = message;
        alertBox.classList.add('show');

        setTimeout(() => alertBox.classList.remove('show'), 3000);
    }

    // --- Event listeners ---
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        e.preventDefault();
        if (e.target.files.length > 0){
            uploadArea.classList.add('uploading');
            handleFile(e.target.files[0]);
        }
    });

    function copyText() {
        navigator.clipboard.writeText(extractedText)
            .then(() => showAlert('📋 Text copied to clipboard!'))
            .catch(err => showAlert('Failed to copy text: ' + err.message));
    }