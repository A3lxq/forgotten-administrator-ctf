# Changelog

## Unreleased

### Phase 2 — Application
- Implemented Flask app (`app/forgotten_admin/`): seeded `john`/`admin` web
  identities, login/logout, `/records/<id>` with intentional IDOR,
  `/admin/diagnostics` with intentional OS command injection gated by
  admin role.
- Added 14 new automated tests (15 total) covering auth, IDOR, the admin
  role gate, command injection, health check, and seed idempotency — all
  passing (`./scripts/run-tests.sh`).
- Chose Ubuntu Server 24.04 LTS as the Phase 3 VM guest OS.

### Phase 1 — Skeleton
- Initialized git repository.
- Created project directory structure (`scripts/`, `app/`, `challenge-data/`,
  `player-material/`, `instructor-material/`, `vm/`, `logs/`).
- Added `README.md`, `PROJECT-STATUS.md`, `.gitignore`.
- Added placeholder player and instructor documentation.

### Phase 0 — Environment & plan
- Inspected host environment (OS, resources, tooling availability).
- Chose architecture: Flask + SQLite app, QEMU/KVM VM with cloud-init
  provisioning, host-only networking.
