/* Polls /hints/state so a team sees an admin reply without reloading
 * the page. Only ever requests this team's own thread -- the session
 * cookie set at claim/resume is what scopes every request server-side
 * (see hints.py), there is no team_id passed from this script at all. */
(function () {
  "use strict";

  const POLL_MS = 4000;
  let lastCount = document.querySelectorAll("#chat-thread .chat-bubble").length;

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function render(messages) {
    const thread = document.getElementById("chat-thread");
    thread.innerHTML = "";
    if (messages.length === 0) {
      thread.appendChild(el("p", "meta", "No questions yet — ask below if you're stuck."));
      return;
    }
    messages.forEach((m) => {
      const bubble = el("div", "chat-bubble " + (m.sender === "team" ? "from-team" : "from-admin"));
      const meta = el("div", "chat-meta", (m.sender === "team" ? "you" : "instructor") + " · " + m.sent_at);
      const body = el("div", "chat-body", m.body);
      bubble.appendChild(meta);
      bubble.appendChild(body);
      thread.appendChild(bubble);
    });
  }

  function poll() {
    fetch("/hints/state")
      .then((r) => r.json())
      .then((data) => {
        if (data.messages.length !== lastCount) {
          lastCount = data.messages.length;
          render(data.messages);
        }
      })
      .catch(() => {
        /* transient network hiccup -- just try again next tick */
      });
  }

  setInterval(poll, POLL_MS);
})();
