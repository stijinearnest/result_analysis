// Simple validation for date format
document.getElementById('loginForm').addEventListener('submit', function(e) {
    const dobInput = document.getElementById('dob');
    const dobPattern = /^\d{4}-\d{2}-\d{2}$/;

    if (!dobPattern.test(dobInput.value)) {
        e.preventDefault();
        document.getElementById('errorMessage').textContent = 'Please enter date in YYYY-MM-DD format';
        document.getElementById('errorMessage').classList.add('show');
    }
});

// Clear error when user starts typing
const inputs = document.querySelectorAll('input');
inputs.forEach(input => {
    input.addEventListener('input', () => {
        document.getElementById('errorMessage').classList.remove('show');
    });
});
