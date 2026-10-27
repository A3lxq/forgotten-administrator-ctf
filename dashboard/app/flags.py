"""Loads instructor-material/flag-manifest.json (the CTF project's own
single source of truth for flag values/classification/points) and
classifies a submitted string against it.

This module never writes to the manifest and never exposes its contents
(or any flag value a team hasn't itself submitted) back over any route --
see teams.py/leaderboard.py for how classification results are used.
"""
from __future__ import annotations

import json
from pathlib import Path


class FlagBook:
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self._by_value: dict[str, dict] = {}
        self._genuine_count = 0
        self.load()

    def load(self) -> None:
        data = json.loads(self.manifest_path.read_text())
        by_value: dict[str, dict] = {}
        genuine_count = 0
        for f in data["flags"]:
            by_value[f["value"]] = {
                "id": f["id"],
                "classification": f["classification"],
                "points": f["points"],
            }
            if f["classification"] == "genuine":
                genuine_count += 1
        self._by_value = by_value
        self._genuine_count = genuine_count

    @property
    def genuine_count(self) -> int:
        return self._genuine_count

    def classify(self, submitted: str) -> dict:
        """Returns {classification: genuine|decoy|invalid, id, points}.
        'invalid' means the string isn't a recognized flag at all --
        never reveals what a *real* flag would have looked like."""
        submitted = submitted.strip()
        match = self._by_value.get(submitted)
        if match is None:
            return {"classification": "invalid", "id": None, "points": 0}
        return {
            "classification": match["classification"],
            "id": match["id"],
            "points": match["points"] if match["classification"] == "genuine" else 0,
        }
