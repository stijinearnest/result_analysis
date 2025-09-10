// Optional: Add a smooth fade-in animation for the success card
document.addEventListener('DOMContentLoaded', function() {
    const card = document.querySelector('.success-card');
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 150);
    }
});
