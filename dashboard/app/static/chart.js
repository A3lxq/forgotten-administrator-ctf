/* Hand-rolled SVG step-line chart (no charting library -- same
 * no-external-dependency approach as confetti.js) showing each team's
 * cumulative score over time. Polls /leaderboard/progression on the
 * same cadence as the rest of the leaderboard. */
(function () {
  "use strict";

  const POLL_MS = 4000;
  const COLORS = ["#39ff14", "#22d3ee", "#e879f9", "#facc15", "#ff4d6d", "#60a5fa", "#fb923c", "#a78bfa"];
  const SVG_NS = "http://www.w3.org/2000/svg";
  const W = 900;
  const H = 340;
  const PAD = { top: 20, right: 16, bottom: 28, left: 50 };

  function parseTime(sqliteDatetime) {
    // "YYYY-MM-DD HH:MM:SS" -> needs a 'T' for reliable cross-browser parsing.
    return new Date(sqliteDatetime.replace(" ", "T")).getTime();
  }

  function el(tag, attrs) {
    const e = document.createElementNS(SVG_NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  function render(series) {
    const container = document.getElementById("progression-chart");
    container.innerHTML = "";

    const allPoints = series.flatMap((s) => s.points);
    if (allPoints.length === 0) {
      const p = document.createElement("p");
      p.className = "meta";
      p.textContent = "No submissions yet -- the chart fills in as teams submit flags.";
      container.appendChild(p);
      return;
    }

    const now = Date.now();
    const times = allPoints.map((p) => parseTime(p.t));
    let minT = Math.min(...times);
    const maxT = Math.max(now, Math.max(...times));
    // Early in an event (or when a team submits several flags in a
    // quick burst), the real data span can be a few seconds while
    // "now" is the only thing far to the right -- without a floor,
    // every real point gets squeezed into a sliver at the left edge
    // and the chart reads as empty at a glance. Guarantee at least a
    // few minutes of visible span so early/clustered activity still
    // has room to be seen, without changing anything once the actual
    // spread already exceeds it.
    const MIN_SPAN_MS = 3 * 60 * 1000;
    if (maxT - minT < MIN_SPAN_MS) minT = maxT - MIN_SPAN_MS;
    const maxScore = Math.max(10, ...allPoints.map((p) => p.score));

    const x = (t) => PAD.left + ((t - minT) / Math.max(1, maxT - minT)) * (W - PAD.left - PAD.right);
    const y = (s) => H - PAD.bottom - (s / maxScore) * (H - PAD.top - PAD.bottom);

    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H, role: "img" });

    // Gridlines + Y-axis labels (4 bands) -- brighter than a typical
    // subtle grid, this chart is meant to be noticed, not blend in.
    for (let i = 0; i <= 4; i++) {
      const score = Math.round((maxScore / 4) * i);
      const gy = y(score);
      svg.appendChild(el("line", { x1: PAD.left, x2: W - PAD.right, y1: gy, y2: gy, stroke: "#2a3650", "stroke-width": 1 }));
      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", PAD.left - 10);
      label.setAttribute("y", gy + 4);
      label.setAttribute("text-anchor", "end");
      label.setAttribute("fill", "#c5cad4");
      label.setAttribute("font-size", "12");
      label.setAttribute("font-weight", "700");
      label.setAttribute("font-family", "ui-monospace, Consolas, Monaco, monospace");
      label.textContent = String(score);
      svg.appendChild(label);
    }

    // Defs: a glow filter per color, reused by that color's line + points.
    const defs = el("defs", {});
    series.forEach((s, i) => {
      const color = COLORS[i % COLORS.length];
      const filter = el("filter", { id: `chart-glow-${i}`, x: "-60%", y: "-60%", width: "220%", height: "220%" });
      const blur = el("feGaussianBlur", { stdDeviation: "4", result: "blur" });
      const merge = el("feMerge", {});
      merge.appendChild(el("feMergeNode", { in: "blur" }));
      merge.appendChild(el("feMergeNode", { in: "SourceGraphic" }));
      filter.appendChild(blur);
      filter.appendChild(merge);
      defs.appendChild(filter);
    });
    svg.appendChild(defs);

    // Max width (in px) of the diagonal ramp drawn at each score jump,
    // instead of a sheer vertical line -- purely cosmetic (matches a
    // reference leaderboard chart the project owner liked), clamped
    // per-transition so two fast back-to-back submissions never make a
    // ramp reach backward past the previous point (the same close-
    // together-submissions case that motivated this chart's
    // millisecond-precision timestamp fix elsewhere).
    const RAMP_PX = 18;

    series.forEach((s, i) => {
      const color = COLORS[i % COLORS.length];
      if (s.points.length === 0) return;

      // Step line with a short diagonal ramp at each submission, rather
      // than an instantaneous vertical jump -- the ramp always finishes
      // exactly at the real submission time, so the dot still marks the
      // true moment it happened.
      const firstX = x(parseTime(s.points[0].t));
      let d = `M ${firstX} ${y(0)}`;
      let prevScore = 0;
      let prevX = firstX;
      s.points.forEach((p) => {
        const px = x(parseTime(p.t));
        const ramp = Math.min(RAMP_PX, px - prevX);
        d += ` L ${px - ramp} ${y(prevScore)} L ${px} ${y(p.score)}`;
        prevScore = p.score;
        prevX = px;
      });
      d += ` L ${x(now)} ${y(prevScore)}`;

      svg.appendChild(el("path", {
        d, fill: "none", stroke: color, "stroke-width": 4,
        "stroke-linejoin": "round", filter: `url(#chart-glow-${i})`,
      }));

      s.points.forEach((p) => {
        svg.appendChild(el("circle", {
          cx: x(parseTime(p.t)), cy: y(p.score), r: 6, fill: color,
          stroke: "#0a0e17", "stroke-width": 2, filter: `url(#chart-glow-${i})`,
        }));
      });
    });

    container.appendChild(svg);

    // Legend.
    const legend = document.createElement("div");
    legend.className = "chart-legend";
    series.forEach((s, i) => {
      const item = document.createElement("span");
      item.className = "chart-legend-item";
      const swatch = document.createElement("span");
      swatch.className = "chart-legend-swatch";
      swatch.style.background = COLORS[i % COLORS.length];
      item.appendChild(swatch);
      item.appendChild(document.createTextNode(s.name));
      legend.appendChild(item);
    });
    container.appendChild(legend);
  }

  function poll() {
    fetch("/leaderboard/progression")
      .then((r) => r.json())
      .then((data) => render(data.series))
      .catch(() => {
        /* transient network hiccup -- just try again next tick */
      });
  }

  poll();
  setInterval(poll, POLL_MS);
})();
