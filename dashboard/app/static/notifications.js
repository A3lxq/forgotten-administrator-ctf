/* Polls /hints/unread so a team notices an admin reply from anywhere
 * in the dashboard (leaderboard, rules, submit), not just while the
 * /hints page itself is open. Only loaded on pages where a team
 * session exists (see base.html) -- same isolation guarantee as
 * everything else in hints.py applies here, this just reports a
 * boolean for the logged-in team's own thread. */
(function () {
  "use strict";

  const POLL_MS = 5000;

  function poll() {
    fetch("/hints/unread")
      .then((r) => r.json())
      .then((data) => {
        const dot = document.getElementById("hints-unread-dot");
        if (!dot) return; // not on a page with the nav, or not a team session
        dot.classList.toggle("show", !!data.unread);
      })
      .catch(() => {
        /* transient network hiccup -- just try again next tick */
      });
  }

  poll();
  setInterval(poll, POLL_MS);
})();
