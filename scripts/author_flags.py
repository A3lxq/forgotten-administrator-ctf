#!/usr/bin/env python3
"""author_flags.py — instructor-only. Generates all 15 flags' content and
the private manifest from a single source of truth (FLAGS / DECOYS below).

Re-running regenerates challenge-data/ and instructor-material/flag-
manifest.json from scratch (idempotent in effect, though it overwrites
rather than diffing) and also writes the Stage 4/5 artifacts that
vm/scripts/deploy-flags.sh pushes onto the VM afterward.

Run with the app's venv (needs `cryptography`):
    app/.venv/bin/python3 scripts/author_flags.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "challenge-data" / "tools"))
import flagcrypto  # noqa: E402

CHALLENGE = ROOT / "challenge-data"
MANIFEST_PATH = ROOT / "instructor-material" / "flag-manifest.json"
VM_STAGING = ROOT / "vm" / "flag-staging"  # gitignored; pushed to the VM

# ---------------------------------------------------------------------------
# Single source of truth. Genuine flags use SYN{...}; decoys use FFLAG:...
# (format mandated by the project spec). Passwords here are the AUTHOR's
# record — this script is what ends up NOT shipped to players (it lives
# under scripts/, but more importantly its *output* manifest lives under
# instructor-material/, which is the actual player/instructor boundary).
# ---------------------------------------------------------------------------

GENUINE = {
    1: dict(value="SYN{osint_fingerprint_f0c73a91}", stage="1-osint",
            points=100, encrypted=False),
    2: dict(value="SYN{exif_breadcrumb_8d12ff04}", stage="2-metadata",
            points=100, encrypted=False),
    3: dict(value="SYN{git_ghost_61ace7b2}", stage="3-git-crypto",
            points=150, encrypted=True, password="BlueHarbor-99"),
    4: dict(value="SYN{admin_blindspot_9f4e2c18}", stage="4-web-idor-admin",
            points=200, encrypted=True, password="oldhandoff-rotate-2024"),
    5: dict(value="SYN{root_of_all_evidence_3b7d55a0}", stage="5-privesc-root",
            points=250, encrypted=True, password="SYN{git_ghost_61ace7b2}"),
            # ^ Flag 5's password IS Flag 3's decrypted plaintext (the
            # project's "Original Flag 3 unlocks the final artifact" rule).
}

DECOYS = {
    "d1a": dict(value="FFLAG:old_profile_rev1_55c2", stage="1-osint", encrypted=False),
    "d1b": dict(value="FFLAG:deprecated_repo_link_a913", stage="1-osint", encrypted=True, password="legacyKey2016"),
    "d2a": dict(value="FFLAG:camera_test_shot_2017_cc41", stage="2-metadata", encrypted=False),
    "d2b": dict(value="FFLAG:draft_scan_metadata_77b0", stage="2-metadata", encrypted=True, password="scanpass2017"),
    "d3a": dict(value="FFLAG:legacy_test_flag_2018_3f09", stage="3-git-crypto", encrypted=False),
    "d3b": dict(value="FFLAG:rotated_out_jan_2019_e2a4", stage="3-git-crypto", encrypted=True, password="old-wifi-2018"),
    "d4a": dict(value="FFLAG:ticket_closed_wontfix_19d7", stage="4-web-idor-admin", encrypted=False),
    "d4b": dict(value="FFLAG:backup_pre_rotation_88c5", stage="4-web-idor-admin", encrypted=True, password="prerotate-2023"),
    "d5a": dict(value="FFLAG:old_root_memo_4b61", stage="5-privesc-root", encrypted=False),
    "d5b": dict(value="FFLAG:old_root_snapshot_f02e", stage="5-privesc-root", encrypted=True, password="SnapshotKey-2023"),
}


def reset_dir(p: Path) -> None:
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)


def build_stage1_osint() -> dict:
    d = CHALLENGE / "stage1-osint"
    reset_dir(d)

    profile_html = f"""<!doctype html>
<html><head><title>SynHub — jtyler_dev</title></head>
<body>
<h1>jtyler_dev</h1>
<p>Full-stack tinkerer. Builds small internal tools, then forgets about
them. Previously: <em>ledger-tools</em> (internal), a few archived
scripts.</p>
<h2>Activity</h2>
<ul>
  <li>2019-11: Archived project <code>ledger-tools</code> — "handed off,
      see project page"</li>
  <li>2017-03: Archived project <code>spark-ci-badge</code> (dead CI
      integration) — last status badge cached below:
      <code>test-flag: {DECOYS['d1a']['value']}</code></li>
</ul>
<h2>Old gist (2016 migration backup, don't need this anymore)</h2>
<pre>{flagcrypto.encrypt_bytes(DECOYS['d1b']['password'], DECOYS['d1b']['value'].encode()).hex()}</pre>
<p><small>unlock code from the 2016 migration, in case I ever need this
again: {DECOYS['d1b']['password']}</small></p>
<p>Contact: jtyler (dot) dev (at) oldmail example — inbox is dead, don't
bother.</p>
</body></html>
"""
    (d / "profile.html").write_text(profile_html)

    project_html = f"""<!doctype html>
<html><head><title>ledger-tools — internal project page</title></head>
<body>
<h1>ledger-tools</h1>
<p>Internal handover tooling. Maintained by jtyler_dev until the 2019
handover. See the admin for ongoing access.</p>
<h2>Changelog</h2>
<ul>
  <li>v0.4 — handover notes added, see repo history</li>
  <li>v0.3 — added admin diagnostics page</li>
  <li>v0.2 — initial IDOR-prone record viewer (todo: fix before launch —
      never got fixed)</li>
  <li>v0.1 — initial commit</li>
</ul>
<footer>
  <p>Build fingerprint: {GENUINE[1]['value']}</p>
</footer>
</body></html>
"""
    (d / "project-page.html").write_text(project_html)

    (d / "README.md").write_text(
        "# Stage 1 — OSINT\n\n"
        "Start here: `profile.html` is jtyler_dev's public profile page. "
        "It links to this project's own page. Look at both carefully — "
        "page source included, not just rendered text.\n"
    )
    return {"stage1_dir": str(d.relative_to(ROOT))}


def build_stage2_metadata() -> dict:
    d = CHALLENGE / "stage2-metadata"
    reset_dir(d)

    # Minimal valid 1x1 white PNG (no external deps needed).
    import base64
    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AA"
        "QUBAScY42YAAAAASUVORK5CYII="
    )

    files = {
        "handover_photo.png": {
            "Comment": f"handover desk photo — {GENUINE[2]['value']}",
            "Artist": "jtyler_dev",
        },
        "old_office.png": {
            "Comment": f"2017 office move, keep for records — {DECOYS['d2a']['value']}",
            "Artist": "unknown",
        },
        "scan_backup.png": {
            "Comment": flagcrypto.encrypt_bytes(
                DECOYS["d2b"]["password"], DECOYS["d2b"]["value"].encode()
            ).hex(),
            "Artist": f"password noted on the back: {DECOYS['d2b']['password']}",
        },
    }

    for name, tags in files.items():
        path = d / name
        path.write_bytes(png_1x1)
        args = ["exiftool", "-overwrite_original"]
        for tag, val in tags.items():
            args.append(f"-{tag}={val}")
        args.append(str(path))
        subprocess.run(args, check=True, capture_output=True)

    (d / "README.md").write_text(
        "# Stage 2 — Metadata\n\n"
        "Three photos from the handover. Inspect their metadata (not just "
        "the pixels — they're all 1x1 placeholder images). Try:\n"
        "`exiftool handover_photo.png`\n"
    )
    return {"stage2_dir": str(d.relative_to(ROOT))}


def build_stage3_git() -> dict:
    d = CHALLENGE / "stage3-git-history"
    reset_dir(d)

    def git(*args):
        subprocess.run(["git", *args], cwd=d, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.name", "jtyler_dev")
    git("config", "user.email", "jtyler@example.invalid")

    (d / "README.md").write_text("# ledger-tools\n\nInternal handover tooling.\n")
    git("add", "README.md")
    git("commit", "-q", "-m", "Initial commit")

    (d / "notes.txt").write_text(
        "Encrypting the handover backup with our standard passphrase for "
        "this rotation: BlueHarbor-99\n"
        "(old 2018 wifi password was retired: old-wifi-2018 — don't reuse "
        "that one)\n"
    )
    flag3_blob = flagcrypto.encrypt_bytes(GENUINE[3]["password"], GENUINE[3]["value"].encode())
    (d / "handover_backup.enc").write_bytes(flag3_blob)
    git("add", "notes.txt", "handover_backup.enc")
    git("commit", "-q", "-m", "Add encrypted handover backup + passphrase note")

    (d / "old_test_flag.txt").write_text(f"{DECOYS['d3a']['value']}\n(old test value, ignore)\n")
    decoy3b_blob = flagcrypto.encrypt_bytes(DECOYS["d3b"]["password"], DECOYS["d3b"]["value"].encode())
    (d / "old_backup_2018.enc").write_bytes(decoy3b_blob)
    git("add", "old_test_flag.txt", "old_backup_2018.enc")
    git("commit", "-q", "-m", "Rotate out the 2018 backup (encrypted with the old-wifi-2018 passphrase)")

    # Simulate "deleted or changed file recoverable through history":
    # the backup + notes get removed from the latest commit, but remain
    # recoverable via `git log --follow` / `git show <commit>:path`.
    (d / "handover_backup.enc").unlink()
    (d / "notes.txt").unlink()
    (d / "old_test_flag.txt").unlink()
    (d / "old_backup_2018.enc").unlink()
    (d / "README.md").write_text(
        "# ledger-tools\n\nInternal handover tooling.\n\n"
        "(cleanup: removed stale backup files from the working tree)\n"
    )
    git("add", "-A")
    git("commit", "-q", "-m", "Clean up stale backup files")

    # Also publish a downloadable archive (players can't `git clone` a
    # live repo through the web app's materials blueprint -- they
    # download this, extract it, and run git locally against it).
    import tarfile

    archive_path = CHALLENGE / "stage3-git-history.tar.gz"
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(d, arcname="stage3-git-history")

    return {"stage3_dir": str(d.relative_to(ROOT)), "stage3_archive": str(archive_path.relative_to(ROOT))}


def build_stage4_and_5_artifacts() -> dict:
    """Builds the files that get deployed onto the VM (admin home + root
    home). Written to a local staging dir; vm/scripts/deploy-flags.sh
    copies them into place with the right ownership."""
    staging = VM_STAGING
    reset_dir(staging)

    admin_evidence = staging / "admin-evidence"
    admin_evidence.mkdir(parents=True)
    admin_flags = staging / "admin-flags"
    admin_flags.mkdir(parents=True)
    root_dir = staging / "root"
    root_dir.mkdir(parents=True)

    (admin_flags / "original_flag_4.enc").write_bytes(
        flagcrypto.encrypt_bytes(GENUINE[4]["password"], GENUINE[4]["value"].encode())
    )
    (admin_flags / "original_flag_4_backup.enc").write_bytes(
        flagcrypto.encrypt_bytes(DECOYS["d4b"]["password"], DECOYS["d4b"]["value"].encode())
    )
    (admin_evidence / "decrypt_notes.txt").write_text(
        "Password notes from the last handover (clean these up...):\n"
        f"  original_flag_4.enc        -> {GENUINE[4]['password']}\n"
        f"  original_flag_4_backup.enc -> {DECOYS['d4b']['password']} "
        "(old, pre-rotation backup — superseded)\n"
    )
    (admin_evidence / "old_ticket.txt").write_text(
        f"TICKET-1182: Diagnostics tool flagged by security review.\n"
        f"Status: wontfix (deprioritized)\n"
        f"ref: {DECOYS['d4a']['value']}\n"
    )

    (root_dir / "final_evidence.enc").write_bytes(
        flagcrypto.encrypt_bytes(GENUINE[5]["password"], GENUINE[5]["value"].encode())
    )
    (root_dir / "old_evidence.enc").write_bytes(
        flagcrypto.encrypt_bytes(DECOYS["d5b"]["password"], DECOYS["d5b"]["value"].encode())
    )
    (root_dir / "root_note.txt").write_text(
        "Old note to self:\n"
        f"- last year's snapshot (old_evidence.enc) password: {DECOYS['d5b']['password']} "
        "(deprecated set, kept for the audit trail)\n"
        f"- {DECOYS['d5a']['value']} (stale, pre-dates this handover, ignore)\n"
    )

    return {"vm_staging_dir": str(staging.relative_to(ROOT))}


def build_manifest(extra: dict) -> None:
    entries = []
    for fid, g in GENUINE.items():
        entries.append({
            "id": f"original_flag_{fid}",
            "classification": "genuine",
            "stage": g["stage"],
            "points": g["points"],
            "encrypted": g["encrypted"],
            "value": g["value"],
            "password": g.get("password"),
            "decryption_method": (
                "flagcrypto.py decrypt <password> <file> - "
                "(scrypt KDF + AES-256-GCM)" if g["encrypted"] else "plaintext, no decryption needed"
            ),
        })
    for did, dec in DECOYS.items():
        entries.append({
            "id": did,
            "classification": "decoy",
            "stage": dec["stage"],
            "points": 0,
            "encrypted": dec["encrypted"],
            "value": dec["value"],
            "password": dec.get("password"),
            "decryption_method": (
                "flagcrypto.py decrypt <password> <file> - "
                "(scrypt KDF + AES-256-GCM)" if dec["encrypted"] else "plaintext, no decryption needed"
            ),
        })

    manifest = {
        "_warning": "PRIVATE. Never place under app/static, app/templates, "
                    "challenge-data served paths, or player-material.",
        "totals": {
            "genuine": len(GENUINE),
            "decoys": len(DECOYS),
            "genuine_encrypted": sum(1 for g in GENUINE.values() if g["encrypted"]),
            "decoy_encrypted": sum(1 for d in DECOYS.values() if d["encrypted"]),
            "max_score": sum(g["points"] for g in GENUINE.values()),
        },
        "locations": extra,
        "flags": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> int:
    extra = {}
    extra.update(build_stage1_osint())
    extra.update(build_stage2_metadata())
    extra.update(build_stage3_git())
    extra.update(build_stage4_and_5_artifacts())
    build_manifest(extra)
    print("Done. Wrote:")
    print(f"  {CHALLENGE / 'stage1-osint'}")
    print(f"  {CHALLENGE / 'stage2-metadata'}")
    print(f"  {CHALLENGE / 'stage3-git-history'}")
    print(f"  {VM_STAGING}")
    print(f"  {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
