// Add subtle animation to search input on page load
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.focus();
        searchInput.style.transform = 'translateY(-5px)';
        searchInput.style.opacity = '0';
        
        setTimeout(() => {
            searchInput.style.transition = 'all 0.3s ease';
            searchInput.style.transform = 'translateY(0)';
            searchInput.style.opacity = '1';
        }, 100);
    }
});
