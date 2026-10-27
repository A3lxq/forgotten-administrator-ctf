/* Polls /leaderboard/state and updates the live leaderboard, firing the
 * live-winner and final-winner banners + confetti exactly once each
 * (on the poll that first reveals them, and once more on initial page
 * load if a winner was already set before the page opened -- so anyone
 * who joins the page late still sees the celebration once). */
(function () {
  "use strict";

  const POLL_MS = 4000;
  let seenLiveWinner = false;
  let seenFinalWinner = false;

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function renderStandings(standings) {
    const tbody = document.getElementById("leaderboard-body");
    tbody.innerHTML = "";
    standings.forEach((team, i) => {
      const tr = document.createElement("tr");
      tr.className = "rank-" + (i + 1);

      const rankTd = el("td", "rank", "#" + (i + 1));
      const nameTd = el("td", null, team.name);
      const scoreTd = el("td", "score", String(team.score));

      const progressTd = el("td");
      const track = el("div", "progress-track");
      const fill = el("div", "progress-fill");
      const pct = team.genuine_total > 0 ? (team.genuine_found / team.genuine_total) * 100 : 0;
      fill.style.width = pct + "%";
      track.appendChild(fill);
      progressTd.appendChild(track);
      progressTd.appendChild(document.createTextNode(team.genuine_found + "/" + team.genuine_total));

      tr.appendChild(rankTd);
      tr.appendChild(nameTd);
      tr.appendChild(scoreTd);
      tr.appendChild(progressTd);
      tbody.appendChild(tr);
    });

    if (standings.length === 0) {
      const tr = document.createElement("tr");
      const td = el("td", "meta", "No teams yet -- be the first to submit a flag.");
      td.colSpan = 4;
      tr.appendChild(td);
      tbody.appendChild(tr);
    }
  }

  function showBanner(id, titleText, teamName) {
    const banner = document.getElementById(id);
    banner.querySelector(".title").textContent = titleText;
    banner.querySelector(".team-name").textContent = teamName;
    banner.classList.add("show");
  }

  function poll() {
    fetch("/leaderboard/state")
      .then((r) => r.json())
      .then((data) => {
        renderStandings(data.standings);

        document.getElementById("stat-teams").textContent = String(data.standings.length);
        document.getElementById("stat-flags").textContent = String(data.genuine_total);
        document.getElementById("stat-status").textContent = data.event_ended
          ? "Ended"
          : "In progress";

        if (data.live_winner) {
          const isNewTransition = !seenLiveWinner;
          seenLiveWinner = true;
          if (isNewTransition) {
            showBanner("live-winner-banner", "First to clear all flags", data.live_winner);
            window.confettiBurst({ count: 180 });
          }
        }

        if (data.final_winner) {
          const isNewTransition = !seenFinalWinner;
          seenFinalWinner = true;
          if (isNewTransition) {
            showBanner("final-winner-banner", "Event winner", data.final_winner);
            window.confettiBurst({ count: 220, durationMs: 5000 });
          }
        }

        if (data.event_ended) {
          document.getElementById("event-ended-note").hidden = false;
        }
      })
      .catch(() => {
        /* transient network hiccup on a LAN -- just try again next tick */
      });
  }

  poll();
  setInterval(poll, POLL_MS);
})();
