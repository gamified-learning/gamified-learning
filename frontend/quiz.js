const API_BASE = 'http://127.0.0.1:5000';
let dueQuestions = [];
let allQuestions = [];
let currentIndex = 0;

const stateMap = { 0: "New", 1: "Learning", 2: "Review", 3: "Relearning" };

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
        allQuestions = allData.questions || [];
        currentIndex = 0;
        
        renderCurrentState();
    } catch (error) {
        console.error("Error fetching questions:", error);
        document.getElementById('quiz-container').innerHTML = `
            <article class="card">
                <h2>Connection Error</h2>
                <p>Could not connect to the backend server. Make sure it is running on port 5000.</p>
            </article>
        `;
    }
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

function renderCurrentState() {
    if (dueQuestions.length === 0 || currentIndex >= dueQuestions.length) {
        document.getElementById('quiz-container').innerHTML = `
            <article class="card done-state">
                <h2>All Caught Up! 🎉</h2>
                <p>You have reviewed all your due flashcards for now.</p>
                <a href="edit.html" class="btn btn-primary">Manage Questions</a>
            </article>
        `;
        return;
    }

    const q = dueQuestions[currentIndex];

    // Update status badge and progress
    document.querySelector('.status-badge').textContent = stateMap[q.state] ?? "Review";
    document.querySelector('.card-progress').textContent =
        `Question ${currentIndex + 1} of ${dueQuestions.length}`;

    // Update question
    document.querySelector('.question-front').textContent = q.front;

    // Generate options
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    // Get wrong options from allQuestions
    let wrongOptions = allQuestions
        .filter(item => item.id !== q.id && item.back !== q.back)
        .map(item => item.back);
    
    // Shuffle wrong options and take up to 3
    wrongOptions = shuffleArray(wrongOptions).slice(0, 3);
    
    // Combine correct and wrong options
    let allOptions = [q.back, ...wrongOptions];
    
    // If we don't have enough options from the DB, fill with placeholders
    while(allOptions.length < 4) {
        allOptions.push(`Placeholder Option ${allOptions.length}`);
    }
    
    // Shuffle final options
    allOptions = shuffleArray(allOptions);
    
    // Render option buttons
    allOptions.forEach(optText => {
        const btn = document.createElement('button');
        btn.className = 'btn-option';
        btn.textContent = optText;
        
        const isCorrect = (optText === q.back);
        
        btn.onclick = () => handleOptionClick(btn, isCorrect, q.id);
        
        optionsContainer.appendChild(btn);
    });
}

async function handleOptionClick(clickedBtn, isCorrect, qid) {
    // Disable all buttons to prevent multiple clicks
    const btns = document.querySelectorAll('.btn-option');
    btns.forEach(b => b.disabled = true);
    
    if (isCorrect) {
        clickedBtn.classList.add('correct');
        rateCard(qid, 4); // 4 = Easy
    } else {
        clickedBtn.classList.add('incorrect');
        // Find and highlight correct answer
        const q = dueQuestions[currentIndex];
        btns.forEach(b => {
            if (b.textContent === q.back) {
                b.classList.add('correct');
            }
        });
        rateCard(qid, 1); // 1 = Again
    }
    
    // Wait briefly and move to next question
    setTimeout(() => {
        currentIndex++;
        renderCurrentState();
    }, 1500);
}

async function rateCard(qid, rating) {
    try {
        await fetch(`${API_BASE}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: qid, rating })
        });
    } catch (error) {
        console.error("Error submitting review:", error);
    }
}
