"""Admin-only "network diagnostics" tool — contains the intentional OS
command injection (Section 10).

Story purpose: John's team built this so the admin account could quickly
check connectivity to internal hosts without shelling in manually. It
takes a hostname and runs `ping` against it.

INTENTIONAL VULNERABILITY: the hostname is concatenated into a shell
string and executed with shell=True. Any shell metacharacters in the
input are interpreted by the shell, giving arbitrary command execution
as whatever OS identity runs this process.

In this Phase 2 dev/test environment that's just the current OS user. In
the Phase 3 VM, this endpoint is invoked through a narrowly scoped
sudoers rule so it runs as the Linux "admin" account specifically (never
root) — that wiring is documented in vm/ once Phase 3 is built. This file
is not changed between dev and the VM; only how it's invoked changes.
"""
from __future__ import annotations

import subprocess

from flask import Blueprint, current_app, render_template, request

from .auth import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/diagnostics", methods=("GET", "POST"))
@admin_required
def diagnostics():
    output = None
    error = None
    target = ""

    if request.method == "POST":
        target = request.form.get("host", "")
        ping_bin = current_app.config["DIAG_PING_BINARY"]

        # --- INTENTIONAL VULNERABILITY (OS command injection, CWE-78) ---
        # A correct implementation would validate `target` against a strict
        # hostname/IP pattern and/or call subprocess with a fixed argument
        # list (shell=False, no string interpolation). Neither is done
        # here on purpose.
        command = f"{ping_bin} -c 1 {target}"
        try:
            result = subprocess.run(
                command,
                shell=True,  # noqa: S602 - intentional for this lab
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = (result.stdout or "") + (result.stderr or "")
        except subprocess.TimeoutExpired:
            error = "Command timed out."

    return render_template(
        "diagnostics.html", output=output, error=error, target=target
    )
