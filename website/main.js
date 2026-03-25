// ── CUSTOM CURSOR ──────────────────────────────────────────────────────────
(function() {
  const cursor = document.getElementById('cursor');
  const trail  = document.getElementById('cursor-trail');
  if (!cursor || !trail) return;

  let mx = -100, my = -100, tx = -100, ty = -100;

  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    cursor.style.left = mx + 'px';
    cursor.style.top  = my + 'px';
  });

  function animTrail() {
    tx += (mx - tx) * 0.15;
    ty += (my - ty) * 0.15;
    trail.style.left = tx + 'px';
    trail.style.top  = ty + 'px';
    requestAnimationFrame(animTrail);
  }
  animTrail();

  document.querySelectorAll('a, button, .btn').forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.transform = 'translate(-50%,-50%) scale(2.5)';
      cursor.style.background = 'rgba(0,255,157,0.3)';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.transform = 'translate(-50%,-50%) scale(1)';
      cursor.style.background = 'transparent';
    });
  });
})();

// ── PARTICLE CANVAS ────────────────────────────────────────────────────────
(function() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const PARTICLES = 80;
  const particles = Array.from({ length: PARTICLES }, () => ({
    x:  Math.random() * canvas.width,
    y:  Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    r:  Math.random() * 1.5 + 0.5,
    a:  Math.random(),
  }));

  function drawHex(x, y, size, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha * 0.15;
    ctx.strokeStyle = '#00ff9d';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 3 * i;
      const px = x + size * Math.cos(angle);
      const py = y + size * Math.sin(angle);
      i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }

  // static hex grid
  const hexes = [];
  const hexSize = 60;
  const hexW = hexSize * 1.732;
  const hexH = hexSize * 2;
  for (let row = 0; row < Math.ceil(window.innerHeight / (hexH * 0.75)) + 2; row++) {
    for (let col = 0; col < Math.ceil(window.innerWidth / hexW) + 2; col++) {
      hexes.push({
        x: col * hexW + (row % 2 === 0 ? 0 : hexW / 2),
        y: row * hexH * 0.75,
        a: Math.random() * 0.4 + 0.1,
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // hex grid
    hexes.forEach(h => drawHex(h.x, h.y, hexSize, h.a));

    // moving particles
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;

      ctx.save();
      ctx.globalAlpha = p.a * 0.7;
      ctx.fillStyle = '#00ff9d';
      ctx.shadowBlur = 8; ctx.shadowColor = '#00ff9d';
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    // connecting lines between nearby particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 100) {
          ctx.save();
          ctx.globalAlpha = (1 - dist/100) * 0.12;
          ctx.strokeStyle = '#00ff9d';
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
          ctx.restore();
        }
      }
    }

    requestAnimationFrame(draw);
  }
  draw();
})();

// ── SCROLL REVEAL ──────────────────────────────────────────────────────────
(function() {
  const revealEls = document.querySelectorAll('.reveal');
  if (!revealEls.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, 80 * (entry.target.dataset.delay || 0));
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  revealEls.forEach(el => observer.observe(el));
})();

// ── PAGE TRANSITIONS ───────────────────────────────────────────────────────
(function() {
  const overlay = document.getElementById('page-transition');
  if (!overlay) return;

  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto')) return;

    link.addEventListener('click', e => {
      e.preventDefault();
      overlay.classList.add('out');
      setTimeout(() => { window.location.href = href; }, 450);
    });
  });

  // Fade in on load
  overlay.style.transformOrigin = 'top';
  overlay.style.transform = 'scaleY(1)';
  overlay.classList.remove('out');
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      overlay.style.transition = 'transform 0.55s cubic-bezier(0.76,0,0.24,1)';
      overlay.style.transform = 'scaleY(0)';
    });
  });
})();

// ── GLITCH EFFECT ON TITLE ─────────────────────────────────────────────────
(function() {
  const title = document.querySelector('.glitch');
  if (!title) return;

  setInterval(() => {
    title.style.animation = 'none';
    void title.offsetWidth;
    title.style.animation = 'glitch 0.3s steps(1) forwards';
  }, 4000);
})();

// ── TYPEWRITER ─────────────────────────────────────────────────────────────
(function() {
  const el = document.querySelector('.typewriter');
  if (!el) return;
  const text = el.textContent;
  el.textContent = '';
  let i = 0;
  function type() {
    if (i < text.length) {
      el.textContent += text[i++];
      setTimeout(type, 45);
    }
  }
  setTimeout(type, 1200);
})();