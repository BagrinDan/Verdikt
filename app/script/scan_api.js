console.log('SCAN SCRIPT LOADED');


function showMessage(message, type) {
    if (typeof message === 'object') {
        message = JSON.stringify(message);
    }
    const block = document.getElementById(type); 
    if (block) {
        block.innerText = message;
        block.style.display = 'block';
    }
}

function markStepWorking(stepName) {
    const stepEl = document.querySelector(`.step[data-step="${stepName}"]`);
    if (stepEl) {
        stepEl.classList.remove('error'); 
        stepEl.classList.add('active');
    }
}

function markStepError(stepName) {
    const stepEl = document.querySelector(`.step[data-step="${stepName}"]`);
    if (stepEl) {
        stepEl.classList.remove('active');
        stepEl.classList.add('error');
    }
}

function markStepCompleted(stepName) {
    const stepEl = document.querySelector(`.step[data-step="${stepName}"]`);
    if (stepEl) {
        stepEl.classList.remove('active'); 
        stepEl.classList.add('completed');  
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const analyzeForm = document.getElementById('analyzeForm');
    if (!analyzeForm) return;

    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const errorAlert = document.getElementById('error-alert');
        const successAlert = document.getElementById('success-alert');

        if (errorAlert) {
            errorAlert.style.display = 'none';
            errorAlert.innerText = '';
        }
        if (successAlert) {
            successAlert.style.display = 'none';
            successAlert.innerText = '';
        }
        
        document.querySelectorAll('.step').forEach(el => {
            el.classList.remove('completed', 'active');
        });

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

            if (!response.ok) {
                try {
                    const errorData = await response.json();
                    showMessage(errorData.detail || errorData.message || `Server error (${response.status})`, "error-alert");
                } catch {
                    showMessage(`Server error (${response.status})`, "error-alert");
                }
                return;
            }

            // === ЧТЕНИЕ ПОТОКА (STREAMING) ===
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = ''; 

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split('\n');
                
                buffer = lines.pop(); 

                for (let line of lines) {
                    if (line.trim() === '') continue; 
                    
                    try {
                        const data = JSON.parse(line);
                        console.log("Получено событие с сервера:", data);

                        if (data.status === "error") {
                            if (data.step) {
                                markStepError(data.step); 
                            }
                            showMessage(data.message, "error-alert");
                            return; 
                        }

                        if (data.step) {
                            if (data.status === "active") {
                                markStepWorking(data.step);
                            } else if (data.status === "completed") {
                                markStepCompleted(data.step);
                            } 
                        }

                        if (data.status === "success") {
                            showMessage(data.message || 'Scaning complete :)', "success-alert");
                        }

                    } catch (parseErr) {
                        console.error("Ошибка парсинга JSON:", line, parseErr);
                    }
                }
            }
        } catch (err) {
            console.error('Network Error:', err);
            showMessage('Network error or server is unreachable.', "error-alert");
        }
    });
});