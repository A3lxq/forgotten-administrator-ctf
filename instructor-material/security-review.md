# Security Review

> Private. Self-review against the project's own safety requirements
> (Section 20, Section 24), based on what was actually checked against
> the live VM during Phases 3–5 — not assumed.

## Network isolation

| Check | Status | Evidence |
|---|---|---|
| No bridged networking | ✅ confirmed | `boot-vm.sh` uses `-netdev user` (QEMU usermode NAT/SLIRP) only; no `-netdev bridge`, no `-netdev tap` anywhere in the scripts. |
| No public interface exposure | ✅ confirmed | Forwarded ports are bound to `127.0.0.1` only (`hostfwd=tcp:127.0.0.1:2222-:22`, `...:8080-:8000`), not `0.0.0.0`. |
| Only the intended ports are forwarded | ✅ confirmed | Exactly two: SSH (instructor-only) and the web app. No other guest port is reachable from the host. |
| App bound to a specific port, not wide open | ✅ confirmed | App listens on guest `0.0.0.0:8000` — guest-internal only; external reachability is controlled entirely by the hostfwd rule above, not by the app itself. |
| Tested on a real multi-host lab network (not just this single dev host) | ⚠️ **not yet tested** | Everything so far was verified on one machine (loopback hostfwd). `vm/networking.md` documents what to change (bind to the lab interface IP, not `127.0.0.1`) but that specific multi-host configuration has not been exercised end-to-end. |

## Account / access isolation

| Check | Status | Evidence |
|---|---|---|
| Players never get SSH credentials | ✅ by design | Only `ctfbuilder` has an SSH key; `john`/`admin` have console passwords only, `ssh_pwauth: false`. |
| `root` login disabled | ✅ confirmed | `disable_root: true` in cloud-init; `root` has no password set, no SSH key. |
| `admin` has no sudo rights | ✅ confirmed live | `sudo -u admin sudo -n -l` → "a password is required"; no NOPASSWD entries anywhere for `admin`. |
| App runs as `admin`, never root | ✅ confirmed live | `ps -o user= -C python3` → `admin`, both before and after Phase 5 changes. |
| Exactly one privesc vector | ✅ confirmed | Only the Phase 5 cron/group-writable-script weakness exists; no other SUID/sudo/cron shortcut was added. `find / -perm -4000` after a reset shows only the base Ubuntu image's standard SUID binaries. |
| Host (this dev machine) never modified | ✅ confirmed | No script in `vm/scripts/` touches anything outside `vm/disks/`, `vm/seed/`, or the VM's own filesystem over SSH. No host account, firewall, bootloader, or network config was changed. |

## Flags and credentials

| Check | Status | Evidence |
|---|---|---|
| No real organizations/people/credentials | ✅ confirmed | All names (`jtyler_dev`, `ledger-tools`, Synnefo-branded flags) and all passwords are fictional, generated for this project. |
| Private manifest not player-accessible | ✅ confirmed | `instructor-material/flag-manifest.json` is outside `app/static`, `app/templates`, and `player-material/`; not served by the Flask app. |
| Decoys don't leak genuine values | ✅ confirmed by validator | `scripts/validate-flags.sh` checks `genuine_values & decoy_values == ∅`; passes. |
| No homemade cryptography | ✅ confirmed | `flagcrypto.py` uses `cryptography`'s `Scrypt` + `AESGCM` only. |
| Final artifact password ≠ any Linux password, ≠ its own encrypted flag's password | ✅ confirmed | Flag 3's password is `BlueHarbor-99`; the final artifact's password is Flag 3's *decrypted value* (`SYN{git_ghost_61ace7b2}`) — distinct strings, neither matches `john`'s, `admin`'s, or (nonexistent) `root`'s Linux password. |

## Application scope

| Check | Status | Evidence |
|---|---|---|
| IDOR and command injection are the only intentional web vulnerabilities | ✅ confirmed by code review | `app/forgotten_admin/` has exactly two marked `INTENTIONAL VULNERABILITY` sections (`records.py`, `admin.py`); no other route skips auth/authorization checks. |
| No general-purpose remote command service | ✅ confirmed | The only command execution path is the single `host` field in `/admin/diagnostics`, gated by the admin role — not a generic exec endpoint. |
| Dev-only `SECRET_KEY` is not a live risk | ✅ acceptable for this lab | `app/forgotten_admin/__init__.py` has a hardcoded Flask `SECRET_KEY` — fine for an isolated, disposable lab VM; would need to change for any non-disposable deployment (noted, not a finding against this project's actual threat model). |
| The unauthenticated `/materials/` blueprint only serves player-safe content, and rejects path traversal | ✅ confirmed, live | `materials.py` uses `send_from_directory` exclusively (validates the resolved path stays inside the given directory). Tested live against the VM: `/materials/osint/../../app/forgotten_admin/db.py` and a similar traversal attempt at `instructor-material/flag-manifest.json` both → `404`. `PUBLIC_DATA_DIR` on the VM (`/opt/forgotten-admin/public-data`) is a curated copy containing only Stage 1-3 player content — never instructor-material, app source, or the flag-staging directory. |

## Listening services on the VM

Checked with `sudo ss -tlnp` on the live VM:
```
0.0.0.0:22     sshd                (expected -- forwarded for ctfbuilder only)
0.0.0.0:8000   python3 (the app)   (expected -- forwarded as the web app)
127.0.0.53:53, 127.0.0.54:53   systemd-resolved stub   (loopback only, standard Ubuntu DNS stub, not forwarded/reachable from the host)
```
✅ Confirmed: nothing unexpected is listening. Exactly the two intended
services are reachable via the hostfwd rules.

## Outstanding / not yet verified

- Multi-host lab network configuration (players on a separate physical
  machine from the VM host) has not been tested — see `vm/networking.md`
  for what would need changing and re-verifying.
