// --- Dark / Light Theme Toggle Module ---
function toggleDarkMode() {
    const htmlEl = document.documentElement;
    const isDark = htmlEl.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeUI(isDark);
    if (window.currentCompetitors && window.currentCompetitors.length > 0 && typeof renderChart === 'function') {
        renderChart(window.currentCompetitors, window.currentMyPrice);
    }
}

function updateThemeUI(isDark) {
    const sun = document.getElementById('sunIcon');
    const moon = document.getElementById('moonIcon');
    if (sun && moon) {
        if (isDark) {
            sun.classList.add('hidden');
            moon.classList.remove('hidden');
        } else {
            sun.classList.remove('hidden');
            moon.classList.add('hidden');
        }
    }
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        updateThemeUI(true);
    } else {
        document.documentElement.classList.remove('dark');
        updateThemeUI(false);
    }
}
