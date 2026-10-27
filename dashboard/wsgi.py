"""Dev/event entry point: `python wsgi.py` or `flask --app wsgi run`.

Runs on the instructor's own host machine, not the CTF VM -- see
instructor-material/dashboard-guide.md. Binds to 0.0.0.0 by default so
players on the same (Bridged) LAN as the CTF VM can reach it; set
DASHBOARD_PORT to change the port (default 7000 -- NOT 6000: that's in
Chrome/Firefox's browser-blocked port list, reserved for X11
(6000-6063), and loading it fails with ERR_UNSAFE_PORT in-browser even
though the server itself works fine -- found by testing this with a
real browser, not just curl).
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", "7000"))
    # threaded=True: without it, Flask's dev server handles one request
    # at a time -- fine for light, spread-out polling, but a real event
    # has exactly the kind of correlated burst (everyone's leaderboard
    # fires confetti at once and they all refresh) that would queue up
    # behind each other otherwise. Verified this was a real, measurable
    # bottleneck (latency scaling with concurrent load) before adding
    # this, and that it's gone afterward -- see dashboard-guide.md.
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
