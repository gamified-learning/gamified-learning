const API_BASE = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', fetchStats);

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();
        
        document.getElementById('stat-due').textContent = data.due_count || 0;
        document.getElementById('stat-learning').textContent = data.learning_count || 0;
        document.getElementById('stat-total').textContent = data.total_count || 0;
    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}
