// --- Main Application Entry Point & Initialization ---
window.currentMyPrice = 0;
window.currentCompetitors = [];

document.addEventListener('click', function(e) {
    const container = document.getElementById('langDropdownContainer');
    if (container && !container.contains(e.target)) {
        if (typeof closeLangDropdown === 'function') closeLangDropdown();
    }
    const mpContainer = document.getElementById('mpDropdownContainer');
    if (mpContainer && !mpContainer.contains(e.target)) {
        if (typeof closeMpDropdown === 'function') closeMpDropdown();
    }
});

// Initialize default view on DOM load
window.addEventListener('DOMContentLoaded', () => {
    if (typeof initTheme === 'function') initTheme();
    if (typeof renderMyProducts === 'function') renderMyProducts();
    if (typeof setLanguage === 'function') setLanguage(currentLang);
});
