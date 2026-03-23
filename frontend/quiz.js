const API_BASE = 'http://127.0.0.1:5000';
let dueQuestions = [];
let currentIndex = 0;
let answerRevealed = false;

const stateMap = { 0: "New", 1: "Learning", 2: "Review", 3: "Relearning" };

document.addEventListener('DOMContentLoaded', initQuiz);

async function initQuiz() {
    try {
        const res = await fetch(`${API_BASE}/get_questions`);
        const data = await res.json();
        dueQuestions = data.questions || [];
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

function renderCurrentState() {
    answerRevealed = false;

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

    // Update question and answer content
    document.querySelector('.question-front').textContent = q.front;
    document.querySelector('.question-back').textContent = q.back;

    // Hide answer and rating controls until revealed
    document.querySelector('.question-back').hidden = true;
    document.querySelector('.rating-controls').hidden = true;
}

function showAnswer() {
    document.querySelector('.question-back').hidden = false;
    document.querySelector('.rating-controls').hidden = false;
    answerRevealed = true;
}

async function rateCard(rating) {
    if (!answerRevealed) return;

    const q = dueQuestions[currentIndex];
    try {
        await fetch(`${API_BASE}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: q.id, rating })
        });
    } catch (error) {
        console.error("Error submitting review:", error);
    }

    setTimeout(() => {
        currentIndex++;
        renderCurrentState();
    }, 1500);
}
