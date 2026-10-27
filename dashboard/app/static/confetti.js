/* Small, dependency-free confetti burst (canvas + requestAnimationFrame).
 * Hand-rolled rather than a vendored third-party library, consistent
 * with this project's general avoidance of external runtime deps --
 * see scripts/author_flags.py's own PNG writer for the same reasoning.
 * Usage: confettiBurst() fires one burst; safe to call repeatedly. */
(function (global) {
  "use strict";

  const COLORS = ["#39ff14", "#22d3ee", "#e879f9", "#facc15", "#ff4d6d"];

  function ensureCanvas() {
    let canvas = document.getElementById("confetti-canvas");
    if (canvas) return canvas;
    canvas = document.createElement("canvas");
    canvas.id = "confetti-canvas";
    document.body.appendChild(canvas);
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", resize);
    resize();
    return canvas;
  }

  function confettiBurst(opts) {
    opts = opts || {};
    const count = opts.count || 160;
    const durationMs = opts.durationMs || 4000;
    const canvas = ensureCanvas();
    const ctx = canvas.getContext("2d");

    const particles = [];
    for (let i = 0; i < count; i++) {
      particles.push({
        x: canvas.width / 2 + (Math.random() - 0.5) * 120,
        y: canvas.height * 0.25 + (Math.random() - 0.5) * 60,
        vx: (Math.random() - 0.5) * 8,
        vy: Math.random() * -6 - 4,
        size: Math.random() * 7 + 4,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        rotation: Math.random() * Math.PI * 2,
        rotationSpeed: (Math.random() - 0.5) * 0.3,
        shape: Math.random() < 0.5 ? "rect" : "circle",
      });
    }

    const gravity = 0.18;
    const drag = 0.995;
    const start = performance.now();

    function frame(now) {
      const elapsed = now - start;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      let alive = false;
      for (const p of particles) {
        p.vx *= drag;
        p.vy = p.vy * drag + gravity;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;

        if (p.y < canvas.height + 20) alive = true;

        const fadeStart = durationMs * 0.6;
        const alpha = elapsed < fadeStart ? 1 : Math.max(0, 1 - (elapsed - fadeStart) / (durationMs - fadeStart));

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation);
        ctx.globalAlpha = alpha;
        ctx.fillStyle = p.color;
        if (p.shape === "rect") {
          ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      if (alive && elapsed < durationMs) {
        requestAnimationFrame(frame);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }

    requestAnimationFrame(frame);
  }

  global.confettiBurst = confettiBurst;
})(window);
