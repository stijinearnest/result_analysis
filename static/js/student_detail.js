// SGPA Chart
document.addEventListener("DOMContentLoaded", () => {

    const canvas = document.getElementById('sgpaChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const isAdminMode = document.body.classList.contains("admin-mode");

    const emerald = '#10b981';
    const emeraldSoft = 'rgba(16, 185, 129, 0.15)';
    const textLight = '#f1f5f9';
    const textDark = '#1e293b';

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: sgpaLabels,
            datasets: [{
                label: 'SGPA',
                data: sgpaValues,
                borderColor: emerald,
                backgroundColor: emeraldSoft,
                tension: 0.4,
                fill: true,
                borderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 8,
                pointBackgroundColor: emerald,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isAdminMode
                        ? 'rgba(17, 24, 39, 0.95)'
                        : 'rgba(0, 0, 0, 0.75)',
                    titleColor: emerald,
                    bodyColor: isAdminMode ? textLight : textDark,
                    borderColor: emerald,
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { size: 14 },
                    bodyFont: { size: 14 }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: isAdminMode ? '#cbd5e1' : '#475569'
                    },
                    grid: {
                        color: isAdminMode
                            ? 'rgba(255,255,255,0.05)'
                            : 'rgba(0,0,0,0.05)'
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 10,
                    ticks: {
                        color: isAdminMode ? '#cbd5e1' : '#475569'
                    },
                    grid: {
                        color: isAdminMode
                            ? 'rgba(255,255,255,0.05)'
                            : 'rgba(0,0,0,0.05)'
                    }
                }
            }
        }
    });
}); 