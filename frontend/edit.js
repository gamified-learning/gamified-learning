const API_BASE = '/api';

let allQuestions = [];
let currentEditingId = null;
let questionCatalog = { subjects: [], chapters_by_subject: {} };

document.addEventListener('DOMContentLoaded', initPage);

function initPage() {
    const subjectInput = document.getElementById('q-subject');
    subjectInput.addEventListener('input', renderChapterOptions);
    subjectInput.addEventListener('change', renderChapterOptions);
    fetchAllQuestions();
}

async function fetchAllQuestions() {
    try {
        const questionsResponse = await fetch(`${API_BASE}/all_questions`);
        const questionsData = await questionsResponse.json();

        allQuestions = questionsData.questions || [];
        questionCatalog = buildQuestionCatalog();

        try {
            const catalogResponse = await fetch(`${API_BASE}/catalog`);
            if (catalogResponse.ok) {
                const catalogData = await catalogResponse.json();
                questionCatalog = {
                    subjects: catalogData.subjects || [],
                    chapters_by_subject: catalogData.chapters_by_subject || {},
                };
            }
        } catch (catalogError) {
            console.warn('Catalog unavailable, falling back to local question data.', catalogError);
        }

        renderSubjectOptions();
        renderChapterOptions();
        renderList();
        
        // Auto-open if query param exists
        const urlParams = new URLSearchParams(window.location.search);
        const editId = urlParams.get('id');
        if (editId) {
            editQuestion(parseInt(editId, 10));
        }
    } catch (error) {
        console.error("Error fetching all questions:", error);
        document.getElementById('questions-list').innerHTML = `
            <p style="color:var(--danger); padding:1rem;">Failed to load questions. Is backend running?</p>
        `;
    }
}

function buildQuestionCatalog() {
    const chaptersBySubject = {};

    allQuestions.forEach(question => {
        const subject = question.subject || 'General';
        const chapter = question.chapter || 'General';
        if (!chaptersBySubject[subject]) {
            chaptersBySubject[subject] = [];
        }
        if (!chaptersBySubject[subject].includes(chapter)) {
            chaptersBySubject[subject].push(chapter);
        }
    });

    return {
        subjects: Object.keys(chaptersBySubject),
        chapters_by_subject: chaptersBySubject,
    };
}

function renderSubjectOptions() {
    const subjectOptions = document.getElementById('subject-options');
    subjectOptions.innerHTML = '';

    questionCatalog.subjects.forEach(subject => {
        const option = document.createElement('option');
        option.value = subject;
        subjectOptions.appendChild(option);
    });
}

function renderChapterOptions() {
    const subject = document.getElementById('q-subject').value.trim();
    const chapterOptions = document.getElementById('chapter-options');
    chapterOptions.innerHTML = '';

    const chapters = subject && questionCatalog.chapters_by_subject[subject]
        ? questionCatalog.chapters_by_subject[subject]
        : Object.values(questionCatalog.chapters_by_subject).flat();

    [...new Set(chapters)].forEach(chapter => {
        const option = document.createElement('option');
        option.value = chapter;
        chapterOptions.appendChild(option);
    });
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
        const subject = q.subject || 'General';
        const chapter = q.chapter || 'General';
        
        div.innerHTML = `
            <h4>${q.front}</h4>
            <p>${q.back}</p>
            <div class="q-item-meta">${subject} · ${chapter}</div>
        `;
        list.appendChild(div);
    });
}

function openNewForm() {
    currentEditingId = null;
    document.getElementById('form-title').innerText = "Add New Card";
    document.getElementById('q-id').value = "";
    document.getElementById('q-subject').value = "";
    document.getElementById('q-chapter').value = "";
    document.getElementById('q-front').value = "";
    document.getElementById('q-back').value = "";
    renderChapterOptions();
    renderList();
}

function editQuestion(id) {
    const q = allQuestions.find(x => x.id === id);
    if (!q) return;
    
    currentEditingId = id;
    document.getElementById('form-title').innerText = "Edit Flashcard";
    document.getElementById('q-id').value = q.id;
    document.getElementById('q-subject').value = q.subject || 'General';
    document.getElementById('q-chapter').value = q.chapter || 'General';
    document.getElementById('q-front').value = q.front;
    document.getElementById('q-back').value = q.back;
    renderChapterOptions();
    renderList();
}

async function saveQuestion() {
    const idVal = document.getElementById('q-id').value;
    const subject = document.getElementById('q-subject').value.trim();
    const chapter = document.getElementById('q-chapter').value.trim();
    const front = document.getElementById('q-front').value.trim();
    const back = document.getElementById('q-back').value.trim();
    
    if (!subject || !chapter || !front || !back) {
        alert("Subject, chapter, front, and back are required!");
        return;
    }
    
    const payload = {
        subject: subject,
        chapter: chapter,
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
        
        questionCatalog = buildQuestionCatalog();
        renderSubjectOptions();
        renderChapterOptions();
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
