document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.inf-card');
  
    // staggered entrance
    cards.forEach((card, i) => {
      card.style.opacity = 0;
      card.style.transform = 'translateY(22px)';
      setTimeout(() => {
        card.style.transition = 'all 480ms cubic-bezier(.2,.9,.3,1)';
        card.style.opacity = 1;
        card.style.transform = 'translateY(0)';
      }, i * 110);
    });
  
    // subtle tilt on pointer move for non-touch devices
    const isTouch = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
    if (!isTouch) {
      cards.forEach(card => {
        card.addEventListener('pointermove', (e) => {
          const rect = card.getBoundingClientRect();
          const cx = rect.left + rect.width/2;
          const cy = rect.top + rect.height/2;
          const dx = (e.clientX - cx) / rect.width;
          const dy = (e.clientY - cy) / rect.height;
          const tiltX = (dy * 6).toFixed(2);
          const tiltY = (dx * -8).toFixed(2);
          card.style.transform = `translateY(-10px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(1.02)`;
        });
  
        card.addEventListener('pointerleave', () => {
          card.style.transform = '';
        });
      });
    }
  });
  