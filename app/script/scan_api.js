console.log('SCAN SCRIPT LOADED');

document.addEventListener('DOMContentLoaded', () => {

    const analyzeForm = document.getElementById('analyzeForm');
    if (!analyzeForm) return;

    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const errorAlert = document.getElementById('error-alert');
        const successAlert = document.getElementById('success-alert');

        errorAlert.style.display = 'none';
        successAlert.style.display = 'none';

        errorAlert.innerText = '';
        successAlert.innerText = '';

        document.querySelectorAll('.step').forEach(el => el.classList.remove('completed'));

        try {
            const payload = {
                repo_url: document.getElementById('repo_url').value,
                branch: document.getElementById('branch_name').value || "main",
                language: document.getElementById('language').value
            };

            const response = await fetch('/static_analyze/scaning', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const message =
                    data?.message ??
                    data?.detail?.message ??                                   
                    (typeof data?.detail === 'string' ? data.detail : null) ??
                    `Server error (${response.status})`;
                showMessage(message, "error-alert");
            } else {
                const message =
                    data?.message ??
                    data?.detail?.message ??                                   
                    (typeof data?.detail === 'string' ? data.detail : null) ??
                    `Scan status: (${response.status})`;
                showMessage(message, "success-alert");
            } 

            console.log('Scanning complete:', data);
        } catch (err) {
            console.error('Network Error:', err);
            showMessage('Network error or server is unreachable.');
        }
    });
});

function showMessage(message, type) {
    const errorBlock = document.getElementById(type); 
    errorBlock.innerText = message;
    errorBlock.style.display = 'block';
}

