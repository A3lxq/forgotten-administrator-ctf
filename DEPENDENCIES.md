# Dependencies & Build Plan

## Host (development machine, this container/VM you're reading this on)

Already present: Python 3.14, git, openssl, gpg, Docker (optional, dev-only).

Needed, not yet installed (owner must run — needs sudo password):
```
sudo apt-get update && sudo apt-get install -y \
    qemu-system-x86 qemu-utils cloud-image-utils genisoimage \
    libimage-exiftool-perl sqlite3
```
- `qemu-system-x86`, `qemu-utils`, `cloud-image-utils`, `genisoimage` — build
  and boot the challenge VM (Phase 3).
- `libimage-exiftool-perl` — generate/verify Stage 2 metadata files (Phase 4).
- `sqlite3` — CLI convenience for inspecting the app DB (optional; Python's
  stdlib `sqlite3` module is already available and is what the app uses).

## Python (app venv, created in Phase 2)

```
python3 -m venv app/.venv
source app/.venv/bin/activate
pip install -r app/requirements.txt
```
- `flask` — the vulnerable web application.
- `cryptography` — AES-GCM + PBKDF2/scrypt for encrypted flags and the final
  artifact (standard, documented primitives only — no homemade crypto).
- `pytest` — automated tests.

## Inside the challenge VM (Phase 3+, via cloud-init/provisioning script)

- Ubuntu Server (minimal cloud image) — same distro family as the host, long
  support window, well documented.
- `python3`, `python3-venv` (to run the deployed copy of the Flask app).
- Whatever minimal package the chosen privilege-escalation vector needs
  (named explicitly once Phase 5 picks the exact mechanism).

## Why these choices

- **Flask + stdlib sqlite3** instead of a bigger framework/DB server: fewer
  moving parts to install, reset, and explain; matches "simplest maintainable
  architecture."
- **QEMU/KVM with cloud-init** instead of VirtualBox/Vagrant: no GUI
  installer needed, fully scriptable, and the host already has `/dev/kvm`
  and the apt packages available — no extra platform to install.
- **cryptography (AES-GCM + PBKDF2/scrypt)** instead of hand-rolled crypto:
  required by the spec (Section 8/13) and is the standard authenticated-
  encryption choice for a password-protected artifact.
