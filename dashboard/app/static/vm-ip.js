/* Plays a 5-second countdown before revealing the lab VM address, the
 * first time a team's submit page shows a given value (the server
 * decides whether to show the countdown at all -- see teams.py's
 * submit() route; this script only ever animates, never decides). */
(function () {
  "use strict";

  const countdown = document.getElementById("vm-ip-countdown");
  if (!countdown) return;

  const ip = countdown.getAttribute("data-vm-ip");
  const reveal = document.getElementById("vm-ip-reveal");
  let n = 5;
  countdown.textContent = String(n);

  const timer = setInterval(() => {
    n -= 1;
    if (n <= 0) {
      clearInterval(timer);
      countdown.remove();
      reveal.textContent = ip;
      reveal.classList.add("show");
    } else {
      countdown.textContent = String(n);
    }
  }, 1000);
})();
