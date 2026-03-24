const API_BASE = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('content-file');
    const fileNameDisplay = document.getElementById('file-name');
    const form = document.getElementById('upload-form');
    
    // File Picker
    dropZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', () => {
        if(fileInput.files.length > 0) {
            fileNameDisplay.textContent = `Selected File: ${fileInput.files[0].name}`;
            fileNameDisplay.style.display = 'block';
        }
    });
    
    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if(e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileNameDisplay.textContent = `Selected File: ${fileInput.files[0].name}`;
            fileNameDisplay.style.display = 'block';
        }
    });
    
    // Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const textContent = document.getElementById('content-text').value;
        const file = fileInput.files[0];
        
        if (!textContent.trim() && !file) {
            showToast('Please provide text or a file to process.', true);
            return;
        }

        const formData = new FormData();
        if (textContent.trim()) {
            formData.append('text', textContent);
        }
        if (file) {
            formData.append('file', file);
        }

        document.getElementById('submit-btn').hidden = true;
        document.getElementById('loading-spinner').hidden = false;

        try {
            const res = await fetch(`${API_BASE}/upload_content`, {
                method: 'POST',
                body: formData
            });
            
            const data = await res.json();
            
            if (res.ok) {
                showToast(`Success! ${data.generated || 0} flashcards were created.`);
                document.getElementById('content-text').value = '';
                fileInput.value = '';
                fileNameDisplay.style.display = 'none';
                
                // Redirect to dashboard or edit
                setTimeout(() => {
                    window.location.href = "dashboard.html";
                }, 2000);
            } else {
                showToast(`Error: ${data.error}`, true);
            }
        } catch (error) {
            console.error("Upload error:", error);
            showToast('An error occurred while uploading. Backend might not be hooked up yet!', true);
        } finally {
            document.getElementById('submit-btn').hidden = false;
            document.getElementById('loading-spinner').hidden = true;
        }
    });
});

function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.backgroundColor = isError ? 'var(--danger)' : '#10b981';
    toast.classList.add('show');
    setTimeout(() => { toast.classList.remove('show'); }, 3000);
}
