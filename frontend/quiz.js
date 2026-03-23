const API_BASE = 'http://127.0.0.1:5000';

let dueQuestions = [];
let allBacks = [];
let currentIndex = 0;

const stateMap = {
    0: "New",
    1: "Learning",
    2: "Review",
    3: "Relearning"
};

document.addEventListener('DOMContentLoaded', initQuiz);

async function initQuiz() {
    try {
        const [dueRes, allRes] = await Promise.all([
            fetch(`${API_BASE}/get_questions`),
            fetch(`${API_BASE}/all_questions`)
        ]);
        const dueData = await dueRes.json();
        const allData = await allRes.json();
        
        dueQuestions = dueData.questions || [];
        allBacks = (allData.questions || []).map(q => q.back);
        currentIndex = 0;
        
        renderCurrentState();
    } catch (error) {
        console.error("Error fetching questions:", error);
        document.getElementById('quiz-container').innerHTML = `
            <div class="card">
                <h2>Connection Error</h2>
                <p>Could not connect to the backend server. Make sure it is running on port 5000.</p>
            </div>
        `;
    }
}

function renderCurrentState() {
    const container = document.getElementById('quiz-container');
    
    if (dueQuestions.length === 0 || currentIndex >= dueQuestions.length) {
        container.innerHTML = `
            <div class="card done-state">
                <h2>All Caught Up! 🎉</h2>
                <p>You have reviewed all your due flashcards for now.</p>
                <div style="margin-top: 2rem;">
                    <a href="edit.html" class="btn btn-primary" style="text-decoration:none;">Manage Questions</a>
                </div>
            </div>
        `;
        return;
    }
    
    const q = dueQuestions[currentIndex];
    const statusText = stateMap[q.state] || "Review";
    const cardsLeft = dueQuestions.length - currentIndex;

    // Generate multiple choice options dynamically
    let options = [q.back];
    // Filter out the correct answer to form distractors, and keep only unique values
    let distractors = [...new Set(allBacks.filter(b => b !== q.back))];
    // Shuffle distractors
    distractors.sort(() => Math.random() - 0.5);
    // Take up to 3 distractors
    options.push(...distractors.slice(0, 3));
    // Shuffle final options
    options.sort(() => Math.random() - 0.5);

    let optionsHTML = options.map(opt => `
        <button class="btn btn-option" onclick="selectOption(this, '${opt.replace(/'/g, "\\'")}', '${q.back.replace(/'/g, "\\'")}')">
            ${opt}
        </button>
    `).join('');

    container.innerHTML = `
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items:center; margin-bottom: 2rem;">
                <span class="status-badge" style="margin-bottom:0;">${statusText}</span>
                <span style="color:var(--text-muted); font-size:0.9rem;">Question ${currentIndex + 1} of ${dueQuestions.length}</span>
            </div>
            
            <div class="question-text">${q.front}</div>
            
            <div class="options-grid">
                ${optionsHTML}
            </div>
        </div>
    `;
}

async function selectOption(btn, selected, correct) {
    const isCorrect = selected === correct;
    
    // Disable all options to prevent double clicking
    const allBtns = document.querySelectorAll('.btn-option');
    allBtns.forEach(b => b.disabled = true);
    
    if (isCorrect) {
        btn.classList.add('correct');
        // Submit "Good" (3) rating automatically
        await submitReview(3);
    } else {
        btn.classList.add('incorrect');
        // highlight the true correct one
        allBtns.forEach(b => {
            if (b.innerText.trim() === correct.trim()) {
                b.classList.add('correct');
            }
        });
        // Submit "Again" (1) rating automatically
        await submitReview(1);
    }
}

async function submitReview(rating) {
    const q = dueQuestions[currentIndex];
    try {
        await fetch(`${API_BASE}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: q.id, rating: rating })
        });
    } catch (error) {
        console.error("Error submitting review:", error);
    }
    
    // Wait slightly to let the user see whether they were right or wrong
    setTimeout(() => {
        currentIndex++;
        renderCurrentState();
    }, 1500);
}
