#!/usr/bin/env python3
"""validate_flags.py — instructor-only local validation utility
(Section 18). Checks the manifest's structure and, where a flag is
encrypted, that it actually decrypts with its recorded password and
NOT with a wrong one. Does not touch the VM (filesystem-permission
checks against the live VM are done separately by
vm/scripts/deploy-flags.sh's own verification step, and were observed
in PROJECT-STATUS.md's Phase 3/4 notes).

Exit code 0 only if every check passes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "challenge-data" / "tools"))
import flagcrypto  # noqa: E402

MANIFEST_PATH = ROOT / "instructor-material" / "flag-manifest.json"


def fail(msg: str, failures: list[str]) -> None:
    failures.append(msg)
    print(f"[FAIL] {msg}")


def ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def main() -> int:
    failures: list[str] = []
    manifest = json.loads(MANIFEST_PATH.read_text())
    flags = manifest["flags"]

    genuine = [f for f in flags if f["classification"] == "genuine"]
    decoys = [f for f in flags if f["classification"] == "decoy"]

    # Counts
    if len(genuine) == 5:
        ok(f"exactly 5 genuine flags ({len(genuine)})")
    else:
        fail(f"expected 5 genuine flags, found {len(genuine)}", failures)

    if len(decoys) == 10:
        ok(f"exactly 10 decoy flags ({len(decoys)})")
    else:
        fail(f"expected 10 decoy flags, found {len(decoys)}", failures)

    # Encryption distribution
    genuine_enc = sum(1 for f in genuine if f["encrypted"])
    decoy_enc = sum(1 for f in decoys if f["encrypted"])
    if genuine_enc == 3:
        ok(f"3 genuine flags encrypted ({genuine_enc})")
    else:
        fail(f"expected 3 genuine encrypted, found {genuine_enc}", failures)
    if decoy_enc == 5:
        ok(f"5 decoy flags encrypted ({decoy_enc})")
    else:
        fail(f"expected 5 decoy encrypted, found {decoy_enc}", failures)

    # Uniqueness
    values = [f["value"] for f in flags]
    if len(values) == len(set(values)):
        ok(f"all {len(values)} flag values are unique")
    else:
        dupes = {v for v in values if values.count(v) > 1}
        fail(f"duplicate flag values found: {dupes}", failures)

    # Format rules
    bad_genuine = [f for f in genuine if not f["value"].startswith("SYN{")]
    if not bad_genuine:
        ok("all genuine flags use the SYN{...} format")
    else:
        fail(f"genuine flags with wrong format: {[f['id'] for f in bad_genuine]}", failures)

    bad_decoy = [f for f in decoys if not f["value"].startswith("FFLAG:")]
    if not bad_decoy:
        ok("all decoy flags use the FFLAG:... format")
    else:
        fail(f"decoy flags with wrong format: {[f['id'] for f in bad_decoy]}", failures)

    decoy_values = {f["value"] for f in decoys}
    genuine_values = {f["value"] for f in genuine}
    if not (decoy_values & genuine_values):
        ok("no decoy value matches a genuine value")
    else:
        fail("a decoy value collides with a genuine value", failures)

    # Scoring
    max_score = sum(f["points"] for f in genuine)
    if max_score == 800:
        ok(f"max score == 800 ({max_score})")
    else:
        fail(f"expected max score 800, got {max_score}", failures)
    if all(f["points"] == 0 for f in decoys):
        ok("all decoys award 0 points")
    else:
        fail("a decoy has nonzero points", failures)

    # Actual decryption: every encrypted flag must decrypt with its
    # recorded password, and must NOT decrypt with a wrong one.
    # Encrypted content lives in challenge-data/ (stage1/2/3) or
    # vm/flag-staging/ (stage4/5) depending on where author_flags.py put
    # it; locate by id.
    locations = manifest.get("locations", {})
    stage3_dir = ROOT / locations["stage3_dir"]

    def from_git(path_in_repo: str) -> bytes:
        # Flags 3 and the stage-3 decoy are deliberately removed from the
        # stage-3 repo's current working tree (that's the git-history
        # exercise) -- recover them the same way a player would, via
        # `git show <rev>:<path>`, not from the working tree.
        return subprocess.run(
            ["git", "show", f"HEAD~1:{path_in_repo}"],
            cwd=stage3_dir, check=True, capture_output=True,
        ).stdout

    enc_file_map = {
        "original_flag_3": lambda: from_git("handover_backup.enc"),
        "original_flag_4": lambda: (ROOT / "vm" / "flag-staging" / "admin-flags" / "original_flag_4.enc").read_bytes(),
        "original_flag_5": lambda: (ROOT / "vm" / "flag-staging" / "root" / "final_evidence.enc").read_bytes(),
        "d1b": None,  # embedded in stage1 profile.html as a hex blob; spot-checked separately
        "d2b": None,  # embedded in stage2 PNG metadata; spot-checked separately
        "d3b": lambda: from_git("old_backup_2018.enc"),
        "d4b": lambda: (ROOT / "vm" / "flag-staging" / "admin-flags" / "original_flag_4_backup.enc").read_bytes(),
        "d5b": lambda: (ROOT / "vm" / "flag-staging" / "root" / "old_evidence.enc").read_bytes(),
    }

    for f in flags:
        if not f["encrypted"]:
            continue
        loader = enc_file_map.get(f["id"])
        if loader is None:
            print(f"[skip] {f['id']}: not file-checked here (embedded in media/page, see README)")
            continue
        try:
            blob = loader()
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            fail(f"{f['id']}: could not load ciphertext ({exc})", failures)
            continue
        try:
            decrypted = flagcrypto.decrypt_bytes(f["password"], blob).decode()
        except ValueError as exc:
            fail(f"{f['id']}: correct password failed to decrypt ({exc})", failures)
            continue
        if decrypted == f["value"]:
            ok(f"{f['id']}: decrypts correctly with its recorded password")
        else:
            fail(f"{f['id']}: decrypted to unexpected value {decrypted!r}", failures)

        try:
            flagcrypto.decrypt_bytes(f["password"] + "-wrong", blob)
            fail(f"{f['id']}: decrypted successfully with a WRONG password (should fail)", failures)
        except ValueError:
            ok(f"{f['id']}: correctly rejects a wrong password")

    print()
    if failures:
        print(f"RESULT: {len(failures)} check(s) FAILED")
        return 1
    print("RESULT: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
