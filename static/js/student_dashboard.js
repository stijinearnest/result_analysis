// center text plugin for doughnut charts
const centerText = {
    id: 'centerText',
    afterDraw(chart, args, options) {
      if (!options || !options.text) return;
      const {ctx} = chart;
      const meta = chart.getDatasetMeta(0);
      if (!meta || !meta.data || !meta.data[0]) return;
  
      const x = meta.data[0].x;
      const y = meta.data[0].y;
  
      ctx.save();
      ctx.font = 'bold 14px Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial';
      ctx.fillStyle = '#1A1A1A';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(options.text, x, y);
      ctx.restore();
    }
  };
  
  // ---------- SGPA Area Line Chart ----------
  (function(){
    const ctx = document.getElementById('sgpaChart').getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 0, 200);
    grad.addColorStop(0, 'rgba(79, 70, 229, 0.25)');
    grad.addColorStop(1, 'rgba(79, 70, 229, 0.02)');
  
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: window.sgpaLabels || [],
        datasets: [{
          label: 'SGPA',
          data: window.sgpaValues || [],
          borderColor: '#4f46e5',
          backgroundColor: grad,
          borderWidth: 3,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: '#4f46e5',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverRadius: 6,
          tension: 0.35
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { color: '#64748b' } },
          y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.06)' }, ticks: { color: '#64748b' } }
        },
        maintainAspectRatio: false
      }
    });
  })();
  
  // ---------- Subject Doughnut Dials ----------
  (function(){
    const passRatio = 0.5;
    if (window.marksData) {
      window.marksData.forEach((m, idx) => {
        const obtained = m.marks_obtained || 0;
        const maxm = m.max_marks || 0;
        const remain = maxm - obtained;
        const ratio = maxm ? obtained / maxm : 0;
        const color = ratio < passRatio ? '#ef4444' : '#4f46e5';
  
        const el = document.getElementById(`dial${idx+1}`).getContext('2d');
        new Chart(el, {
          type: 'doughnut',
          data: {
            datasets: [{
              data: [obtained, remain],
              backgroundColor: [color, '#f1f5f9'],
              borderWidth: 0
            }]
          },
          options: {
            cutout: '72%',
            plugins: { legend: { display: false }, centerText: { text: obtained + '/' + maxm } }
          },
          plugins: [centerText]
        });
      });
    }
  })();
  