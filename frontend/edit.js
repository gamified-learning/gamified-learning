const API_BASE = 'http://127.0.0.1:5000';

let allQuestions = [];
let currentEditingId = null;

document.addEventListener('DOMContentLoaded', fetchAllQuestions);

async function fetchAllQuestions() {
    try {
        const response = await fetch(`${API_BASE}/all_questions`);
        const data = await response.json();
        allQuestions = data.questions || [];
        renderList();
    } catch (error) {
        console.error("Error fetching all questions:", error);
        document.getElementById('questions-list').innerHTML = `
            <p style="color:var(--danger); padding:1rem;">Failed to load questions. Is backend running?</p>
        `;
    }
}

function renderList() {
    const list = document.getElementById('questions-list');
    list.innerHTML = '';
    
    if (allQuestions.length === 0) {
        list.innerHTML = '<p style="color:var(--text-muted); padding:1rem; text-align:center;">No flashcards found.</p>';
        return;
    }
    
    allQuestions.forEach(q => {
        const div = document.createElement('div');
        div.className = `q-item ${currentEditingId === q.id ? 'active' : ''}`;
        div.onclick = () => editQuestion(q.id);
        
        div.innerHTML = `
            <h4>${q.front}</h4>
            <p>${q.back}</p>
        `;
        list.appendChild(div);
    });
}

function openNewForm() {
    currentEditingId = null;
    document.getElementById('form-title').innerText = "Add New Card";
    document.getElementById('q-id').value = "";
    document.getElementById('q-front').value = "";
    document.getElementById('q-back').value = "";
    renderList();
}

function editQuestion(id) {
    const q = allQuestions.find(x => x.id === id);
    if (!q) return;
    
    currentEditingId = id;
    document.getElementById('form-title').innerText = "Edit Flashcard";
    document.getElementById('q-id').value = q.id;
    document.getElementById('q-front').value = q.front;
    document.getElementById('q-back').value = q.back;
    renderList();
}

async function saveQuestion() {
    const idVal = document.getElementById('q-id').value;
    const front = document.getElementById('q-front').value.trim();
    const back = document.getElementById('q-back').value.trim();
    
    if (!front || !back) {
        alert("Both front and back are required!");
        return;
    }
    
    const payload = {
        front: front,
        back: back
    };
    if (idVal) {
        // ID input is string from DOM, parse it back to int
        payload.id = parseInt(idVal, 10);
    }
    
    try {
        const response = await fetch(`${API_BASE}/save_question`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const savedQ = await response.json();
        
        // Update local state
        if (idVal) {
            const index = allQuestions.findIndex(x => x.id === payload.id);
            if (index !== -1) allQuestions[index] = savedQ;
        } else {
            allQuestions.push(savedQ);
        }
        
        showToast();
        openNewForm();
        renderList();
    } catch (error) {
        console.error("Error saving question:", error);
        alert("Failed to save flashcard. Check console.");
    }
}

function showToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
