// dashboard.js – fixes syntax errors and completes dashboard
const user = 'kchour96-dev';
const avatarUrl = `https://github.com/${user}.png`;
const userUrl = `https://github.com/${user}`;
const apiUrl = `https://api.github.com/users/${user}`;

async function fetchUser() {
    try {
        const res = await fetch(apiUrl);
        const data = await res.json();
        renderDashboard(data);
    } catch (e) { console.error(e); }
}

function renderDashboard(data) {
    const container = document.getElementById('dashboard-content');
    if (!container) return;

    container.innerHTML = `
        <div class="dashboard-overview">
            <div class="avatar"><img src="${avatarUrl}" alt="GitHub Avatar" loading="lazy"></div>
            <div class="profile">
                <h2>${data.login}</h2>
                <p class="name"><a href="${userUrl}" target="_blank">${data.name || data.login}</a></p>
                <p class="stats">
                    Public Repos: <strong>${data.public_repos}</strong> |
                    Followers: <strong>${data.followers}</strong> |
                    Following: <strong>${data.following}</strong>
                </p>
            </div>
        </div>
        <div class="dashboard-heatmap">
            <h3>Contribution Calendar</h3>
            <img src="https://github.com/users/${user}/contributions?i=1" alt="GitHub Contribution Calendar">
        </div>
        <div class="dashboard-projects">
            <h3>Projects In Progress</h3>
            <ul id="projects-list">
            </ul>
        </div>
        <div class="dashboard-skills">
            <h3>Technical Skills</h3>
            <canvas id="skills-chart" width="400" height="400"></canvas>
        </div>
    `;

    // Projects section
    const projects = [
        { name: 'Ollama AI Scheduler', status: 80, url: 'https://github.com/kchour96-dev/ollama-scheduler' },
        { name: 'OpenClaw CLI Enhancer', status: 60, url: 'https://github.com/kchour96-dev/openclaw-cli' },
        { name: 'Portfolio Site', status: 100, url: 'https://github.com/kchour96-dev/autonomous-portfolio-2026' }
    ];

    const listEl = document.getElementById('projects-list');
    projects.forEach(p => {
        const li = document.createElement('li');
        li.innerHTML = `<a href="${p.url}" target="_blank">
                            ${p.name} — <span>${p.status}%</span>
                            <progress value="${p.status}" max="100"></progress>
                        </a>`;
        listEl.appendChild(li);
    });

    // Skills chart
    const skills = ['JavaScript', 'HTML/CSS', 'PowerShell', 'Python', 'Bash'];
    const counts = [35, 30, 15, 12, 8];  // Dummy percentages based on repo count
    const ctx = document.getElementById('skills-chart').getContext('2d');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: skills,
            datasets: [{
                data: counts,
                backgroundColor: ['#9CCD38', '#F39C12', '#E74C3C', '#3498DB', '#2ECC71']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

fetchUser();
