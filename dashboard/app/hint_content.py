"""Curated hint/taunt message pools for the admin "Give Hint" broadcast
(see admin.py's give_hint route). Keyed by stage number (1-5, roughly
"number of genuine flags found so far + 1") plus a "completed" bucket
for a team that's already found all of them.

Writing rules followed here, matching this project's existing
genuine/decoy philosophy elsewhere:
- "hint" entries nudge toward the right TECHNIQUE or place to look,
  never the flag/password itself -- same standard as every genuine
  clue already built into the challenge.
- "taunt" entries tease toward the stage's actual decoy (grounded in
  real artifact names already in the box -- no new lore invented
  here), loud and a little smug, never literally handing over the
  decoy's flag value either. Several variants per bucket so repeated
  broadcasts don't feel identical.
- Taunts also point at the pure-flavor distractions that aren't tied
  to any flag at all (the SynHub employee directory, password-trap.txt,
  john's IMPORTANT_README.txt) -- these cost a team nothing but time,
  same spirit as the FFLAG decoys, just with no flag value sitting at
  the end of the detour.
- In-story voice: dry, a little knowing, consistent with the existing
  decoy asides (e.g. root_note.txt's "Finally got root, huh?").
"""
from __future__ import annotations

import random

STAGE_CONTENT: dict[int | str, dict[str, list[str]]] = {
    1: {  # OSINT
        "hint": [
            "John's profile page isn't the only thing worth reading slowly. "
            "The project page's version history has more in it than the "
            "headline entries.",
            "Don't just skim for anything bold or boxed off. Read the "
            "project page's changelog line by line, including the boring-"
            "looking ones.",
        ],
        "taunt": [
            "That red-bordered callout on jtyler_dev's profile page sure "
            "catches the eye, doesn't it? Almost like it wants to be found.",
            "A 'cached status badge' with a flag-shaped string sitting "
            "right in the middle of the page. Convenient.",
            "There's a whole 'Employee Directory' linked right next to "
            "John's profile. Every single name in it is clearly worth a "
            "click.",
            "Somebody left an entire credential dump sitting in the OSINT "
            "folder. If you've got a password and a box with SSH open, "
            "you already know what to try.",
        ],
    },
    2: {  # Metadata
        "hint": [
            "exiftool shows more than one field. Check the Comment AND the "
            "Artist field on both photos, not just whichever one you open "
            "first.",
            "Two photos, two different stories in their metadata. Compare "
            "them side by side before deciding which one matters.",
        ],
        "taunt": [
            "scan_backup.png's Artist field practically hands you a "
            "password. Must be your lucky day.",
            "Finding a cleartext password sitting in an EXIF tag feels "
            "like winning, doesn't it?",
        ],
    },
    3: {  # Git history + crypto
        "hint": [
            "git log --oneline only shows one branch by default. Try "
            "--all, and keep reading past the first deleted file you spot.",
            "The newest-looking commit in the history isn't necessarily "
            "the one that matters most. Go back one step further.",
        ],
        "taunt": [
            "A commit message that just hands you a password AND the "
            "filename to use it on? old_backup_2018.enc is right there "
            "waiting.",
            "2018. 'Rotated out.' Sounds like exactly the kind of thing "
            "someone would leave behind as a red herring, if you think "
            "about it.",
        ],
    },
    4: {  # Web IDOR + credential reuse
        "hint": [
            "You're logged in as john, looking at your own record. What "
            "happens if you change just the number in that URL?",
            "A password disclosed on the web doesn't have to stay on the "
            "web. If the same account name exists somewhere else on this "
            "box, try it there too.",
        ],
        "taunt": [
            "N3tOps-Diag#7 -- 'Diag' like there's a diagnostics tool just "
            "waiting to be found. Funny how naming conventions stick "
            "around.",
            "An admin password handed to you in plain text inside "
            "someone else's record. Almost feels like the system wants "
            "you to have it.",
            "Once you're in as admin, it might be worth poking around "
            "john's home directory too. He apparently left something "
            "very important in there.",
        ],
    },
    5: {  # Linux privesc + final artifact
        "hint": [
            "Check what's running on a schedule as root, and whether the "
            "script it actually executes is writable by your own group.",
            "You've got a password from earlier that you were told to "
            "keep. The final artifact's password isn't new -- it's "
            "something you already decrypted.",
        ],
        "taunt": [
            "root_note.txt practically begs you to go straight for "
            "old_evidence.enc with the password right there in the same "
            "sentence. 'Last year's deprecated snapshot,' it says. Sure.",
            "SnapshotKey-2023, handed to you the moment you get root. "
            "Feels like the finish line, doesn't it?",
        ],
    },
    "completed": {
        "hint": [
            "All five, already. Nothing left to nudge you toward -- nice work.",
        ],
        "taunt": [
            "You've already got everything there is to find here. Nothing "
            "left to tease you with.",
        ],
    },
}


def stage_for_progress(genuine_found: int, genuine_total: int) -> int | str:
    """Same proxy used throughout: roughly 'genuine flags found + 1' as
    the stage a team is likely working on, capped at the last real
    stage, with a dedicated bucket once they've found everything."""
    if genuine_found >= genuine_total:
        return "completed"
    stage = genuine_found + 1
    return min(stage, 5)


def pick_message(stage: int | str, mode: str) -> str:
    """mode is 'hint' or 'taunt'. Picks one variant at random so
    repeated broadcasts don't always show the identical line."""
    bucket = STAGE_CONTENT.get(stage, STAGE_CONTENT[5])
    return random.choice(bucket[mode])
