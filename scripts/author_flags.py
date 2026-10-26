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
import random
import shutil
import struct
import subprocess
import sys
import zlib
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

def make_png(width: int, height: int, pixel_fn) -> bytes:
    """A tiny, dependency-free PNG encoder (stdlib only: zlib/struct/
    binascii via zlib.crc32). pixel_fn(x, y) -> (r, g, b) in 0-255.
    No external imaging library needed to generate something that
    looks like *a* photo rather than a literal blank square -- this
    project otherwise has zero third-party build-time dependencies
    beyond what's already in app/requirements.txt, and Pillow isn't
    installable here without system jpeg headers, so this stays
    consistent with the existing 1x1-PNG-via-base64 approach instead
    of adding a new dependency just for cosmetic images."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type: none
        for x in range(width):
            raw.extend(pixel_fn(x, y))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # truecolor
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def render_handover_photo() -> bytes:
    """A small, deterministic, generic desk-scene render -- no real
    people/places, just enough visual content that opening the file
    looks like a (low-res, noisy) photo rather than a blank square."""
    w, h = 160, 120
    rng = random.Random("handover_photo-v1")  # fixed seed: reproducible

    def pixel(x: int, y: int) -> tuple[int, int, int]:
        # Desk background: warm wood-brown gradient, top to bottom.
        r, g, b = 150 - y // 4, 110 - y // 6, 70 - y // 8
        # Laptop base: a dark trapezoid-ish block, lower-middle.
        if 35 <= x <= 125 and 70 <= y <= 95:
            r, g, b = 40, 40, 44
        # Laptop screen: lighter panel above the base, with a few
        # faint horizontal "text" lines.
        if 45 <= x <= 115 and 35 <= y <= 70:
            r, g, b = 60, 70, 80
            if y % 6 in (0, 1) and 50 <= x <= 108:
                r, g, b = 140, 150, 160
        # A small yellow sticky note, upper-right.
        if 128 <= x <= 150 and 20 <= y <= 40:
            r, g, b = 225, 205, 70
        # Grain: small per-pixel jitter so it doesn't look like flat
        # vector art.
        n = rng.randint(-10, 10)
        return (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))

    return make_png(w, h, pixel)


def render_scan_backup() -> bytes:
    """A small, deterministic render that looks like a flatbed-scanned
    document page (header bar + paragraph-like gray bars on an
    off-white background), not a photo."""
    w, h = 170, 220
    rng = random.Random("scan_backup-v1")
    # A handful of fixed "paragraph" line-bands so it reads as text.
    bands = [(18, 30, 150), (36, 48, 130), (54, 66, 155),
             (84, 96, 140), (102, 114, 120), (120, 132, 150),
             (150, 162, 100), (168, 180, 145)]

    def pixel(x: int, y: int) -> tuple[int, int, int]:
        base = 245
        if y <= 12:
            base = 35  # dark header bar
        else:
            for top, bottom, width in bands:
                if top <= y <= bottom and 15 <= x <= 15 + width:
                    base = 160
                    break
        n = rng.randint(-4, 4)
        v = max(0, min(255, base + n))
        return (v, v, v)

    return make_png(w, h, pixel)


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

# Exactly one decoy per stage (5 total) -- a mix of plaintext and
# encrypted so the "decoys can be either" lesson still comes through,
# just without two of everything.
DECOYS = {
    "d1a": dict(value="FFLAG:old_profile_rev1_55c2", stage="1-osint", encrypted=False),
    "d2b": dict(value="FFLAG:draft_scan_metadata_77b0", stage="2-metadata", encrypted=True, password="scanpass2017"),
    "d3b": dict(value="FFLAG:rotated_out_jan_2019_e2a4", stage="3-git-crypto", encrypted=True, password="old-wifi-2018"),
    "d4a": dict(value="FFLAG:ticket_closed_wontfix_19d7", stage="4-web-idor-admin", encrypted=False),
    "d5b": dict(value="FFLAG:old_root_snapshot_f02e", stage="5-privesc-root", encrypted=True, password="SnapshotKey-2023"),
}


def reset_dir(p: Path) -> None:
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)


def build_stage1_osint() -> dict:
    d = CHALLENGE / "stage1-osint"
    reset_dir(d)

    # Decoy (d1a): deliberately LOUD and first thing on the page --
    # looks like a found flag, inviting a quick, satisfied submission.
    # Genuine (Flag 1): blended into ordinary changelog prose on the
    # *other* page, no special styling -- you have to actually read it.
    profile_html = f"""<!doctype html>
<html><head><title>SynHub — jtyler_dev</title></head>
<body>
<h1>jtyler_dev</h1>
<blockquote style="border:2px solid #c00;padding:0.5em">
  <strong>⚠️ cached status badge, 2017 (spark-ci-badge, dead project):</strong><br>
  <code>test-flag: {DECOYS['d1a']['value']}</code>
</blockquote>
<p>Full-stack tinkerer. Builds small internal tools, then forgets about
them. Previously: <em>ledger-tools</em> (internal), a few archived
scripts.</p>
<h2>Activity</h2>
<ul>
  <li>2019-11: Archived project <code>ledger-tools</code> — "handed off,
      see project page"</li>
  <li>2017-03: Archived project <code>spark-ci-badge</code> (dead CI
      integration, badge cached above)</li>
</ul>
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
  <li>v0.4 — handover notes added, see repo history. Tagged this build
      {GENUINE[1]['value']} in case anyone needs to reference it later.</li>
  <li>v0.3 — admin account provisioned (reused the same password
      everywhere -- todo: fix before launch -- never got fixed)</li>
  <li>v0.2 — initial IDOR-prone record viewer (todo: fix before launch —
      never got fixed)</li>
  <li>v0.1 — initial commit</li>
</ul>
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

    files = {
        "handover_photo.png": {
            "render": render_handover_photo,
            "Comment": f"handover desk photo — {GENUINE[2]['value']}",
            "Artist": "jtyler_dev",
        },
        "scan_backup.png": {
            "render": render_scan_backup,
            "Comment": flagcrypto.encrypt_bytes(
                DECOYS["d2b"]["password"], DECOYS["d2b"]["value"].encode()
            ).hex(),
            # Loud on purpose -- a decoy password note should be the
            # easiest thing to notice in this whole stage.
            "Artist": f"PASSWORD (use this to unlock the Comment field!): {DECOYS['d2b']['password']}",
        },
    }

    for name, file_spec in files.items():
        render = file_spec.pop("render")
        tags = file_spec
        path = d / name
        path.write_bytes(render())
        args = ["exiftool", "-overwrite_original"]
        for tag, val in tags.items():
            args.append(f"-{tag}={val}")
        args.append(str(path))
        subprocess.run(args, check=True, capture_output=True)

    (d / "README.md").write_text(
        "# Stage 2 — Metadata\n\n"
        "Two photos from the handover. Inspect their metadata, not just "
        "what's visible in the image itself. Try:\n"
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

    decoy3b_blob = flagcrypto.encrypt_bytes(DECOYS["d3b"]["password"], DECOYS["d3b"]["value"].encode())
    (d / "old_backup_2018.enc").write_bytes(decoy3b_blob)
    git("add", "old_backup_2018.enc")
    # Loud on purpose: the password is right in the commit message, and
    # this commit sits CLOSER to HEAD than the genuine one -- a player
    # scanning `git log` newest-first hits this one first.
    git("commit", "-q", "-m", "Found the old 2018 backup again! Password is old-wifi-2018, decrypt old_backup_2018.enc")

    # Simulate "deleted or changed file recoverable through history":
    # the backup + notes get removed from the latest commit, but remain
    # recoverable via `git log --follow` / `git show <commit>:path`.
    (d / "handover_backup.enc").unlink()
    (d / "notes.txt").unlink()
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
    (admin_evidence / "decrypt_notes.txt").write_text(
        "Password notes from the last handover (clean these up...):\n"
        f"  original_flag_4.enc -> {GENUINE[4]['password']}\n"
    )
    # Loud on purpose: a file that all but announces itself as "the flag".
    (admin_evidence / "FOUND_A_FLAG.txt").write_text(
        f"Found this while cleaning up old tickets, looks like a flag:\n"
        f"{DECOYS['d4a']['value']}\n"
        f"(context: TICKET-1182, admin account flagged by security review "
        f"for credential reuse, status wontfix)\n"
    )

    (root_dir / "final_evidence.enc").write_bytes(
        flagcrypto.encrypt_bytes(GENUINE[5]["password"], GENUINE[5]["value"].encode())
    )
    (root_dir / "old_evidence.enc").write_bytes(
        flagcrypto.encrypt_bytes(DECOYS["d5b"]["password"], DECOYS["d5b"]["value"].encode())
    )
    # Loud on purpose: whatever's in /root should feel like "the" prize
    # the moment you can finally read it -- old_evidence.enc looks like
    # exactly that, right down to the password sitting in the same file.
    (root_dir / "root_note.txt").write_text(
        "Finally got root, huh? Before you get excited:\n"
        f"- old_evidence.enc — this looks important, password is "
        f"{DECOYS['d5b']['password']} (turned out to be last year's "
        "deprecated snapshot, kept around for the audit trail)\n"
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
