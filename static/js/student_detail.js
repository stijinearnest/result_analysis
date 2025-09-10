// SGPA Chart
document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById('sgpaChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: sgpaLabels,   // Defined in template
            datasets: [{
                label: 'SGPA',
                data: sgpaValues, // Defined in template
                borderColor: '#4a6cf7',
                backgroundColor: 'rgba(74, 108, 247, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 5,
                pointBackgroundColor: '#4a6cf7',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleFont: { size: 14 },
                    bodyFont: { size: 14 }
                }
            }
        }
    });
});
