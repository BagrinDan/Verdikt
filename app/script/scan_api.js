console.log('SCAN SCRIPT LOADED');

document.addEventListener('DOMContentLoaded', () => {

    const analyzeForm = document.getElementById('analyzeForm');
    if (!analyzeForm) return;

    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        try {
            const payload = {
                repo_url: document.getElementById('repo_url').value,
                branch: document.getElementById('branch_name').value || "main",
                language: document.getElementById('language').value
            };

            const response = await fetch('/static_analyze/codeql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const message =
                    data?.message ??
                    data?.detail?.message ??                                   // <- добавить
                    (typeof data?.detail === 'string' ? data.detail : null) ??
                    `Server error (${response.status})`;
                showError(message);
            }

            console.log('Scanning complete:', data);
        } catch (err) {
            console.error('Network Error:', err);
            showError('Network error or server is unreachable.');
        }
    });
});

function showError(message) {
    const errorBlock = document.getElementById('error-alert'); 
    errorBlock.innerText = message;
    errorBlock.style.display = 'block';
}