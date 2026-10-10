"""Dev/VM entry point: `flask --app wsgi run` or `python wsgi.py`.

Not for production anywhere outside the isolated CTF VM.
"""
import os

from forgotten_admin import create_app

_config = {}
# Set by the systemd unit on the VM to point at the curated, player-safe
# copy of challenge-data/ deployed under /opt/forgotten-admin/public-data
# (see vm/scripts/remote-provision.sh). Falls back to create_app()'s own
# dev default (the repo's own challenge-data/) if unset.
if os.environ.get("PUBLIC_DATA_DIR"):
    _config["PUBLIC_DATA_DIR"] = os.environ["PUBLIC_DATA_DIR"]

app = create_app(_config or None)

if __name__ == "__main__":
    app.run(debug=False)
