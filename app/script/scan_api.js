console.log('SCRIPT VERSION 2 LOADED');

document.addEventListener('DOMContentLoaded', () => {

    const analyzeForm = document.getElementById('analyzeForm');
    if (!analyzeForm) return;

    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const payload = {
            repo_url: document.getElementById('repo_url').value,
            branch: document.getElementById('branch_name').value || null,
            language: document.getElementById('language').value
        };

        try {
            const response = await fetch('/analyze/repo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (!response.ok) {
                console.error('Validation/Server Error:', data);
                alert(`Error: ${JSON.stringify(data.detail)}`);
                return;
            }

            console.log('Success:', data);
        } catch (err) {
            console.error('Network Error:', err);
        }
    });
});