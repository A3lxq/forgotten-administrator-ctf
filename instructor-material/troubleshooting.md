# Troubleshooting

> Private. Real issues hit while building this project, and how they
> were actually fixed — not generic advice.

## cloud-init: "useradd: group admin exists" / the `admin` Linux account never gets created

**Symptom:** `cloud-init status` reports `status: error`;
`getent passwd admin` returns nothing even though `john` and
`ctfbuilder` exist.

**Cause:** Ubuntu's cloud image already ships a system group named
`admin`. `useradd admin` (cloud-init's default behavior) tries to
create a *new* private group called `admin` for the new user and
collides with the existing one.

**Fix:** in `vm/cloud-init/user-data.yaml`, the `admin` user entry sets
`no_user_group: true` and `primary_group: admin` so it reuses the
existing group instead of trying to create one. If you ever see this
again after editing `user-data.yaml`, rebuild the VM from scratch
(`./scripts/create-disk.sh --force && ./scripts/boot-vm.sh`) rather than
patching the running instance — a patched instance won't tell you if
the *documented* build path is actually correct.

## `scp`'s port flag is `-P`, not `-p`

**Symptom:** `vm/scripts/provision.sh` failed with
`scp: stat local "2222": No such file or directory`.

**Cause:** `ssh` uses `-p <port>`; `scp` uses `-P <port>` (`-p` means
"preserve file attributes" for `scp`). Reusing an `ssh`-style options
array verbatim for an `scp` call silently breaks.

**Fix:** `provision.sh` and `deploy-flags.sh` build `scp`'s flags
explicitly rather than reusing the `ssh` options array unchanged.

## `chmod`/glob failing with "No such file or directory" even though the files exist

**Symptom:** in `deploy-flags.sh`,
`sudo chmod 640 /home/admin/evidence/*` failed with "No such file or
directory" right after a `cp` into that same directory had (apparently)
succeeded.

**Cause:** shell glob expansion for `*` happens in the *calling* shell
— `ctfbuilder`'s, here — **before** `sudo` escalates to root.
`/home/admin/evidence` is mode `750`, owned by `admin:admin`;
`ctfbuilder` can't read it to expand the glob, so the literal,
unexpanded string `/home/admin/evidence/*` gets passed to `chmod`,
which then fails to find a file with an asterisk in its name.

**Fix:** wrap the glob-using commands in `sudo bash -c '...'` so the
glob expands *inside* the root shell, which can read the directory.

## QEMU boots very slowly without `/dev/kvm` access

**Symptom:** first boot + cloud-init took roughly 8-10 minutes.

**Cause:** this build environment's user wasn't in the `kvm` group, so
`boot-vm.sh` fell back to TCG (software CPU emulation) instead of KVM
hardware acceleration.

**Fix / workaround:** `boot-vm.sh` already auto-detects and uses KVM if
`/dev/kvm` is readable/writable by the current user — no script change
needed, just `sudo usermod -aG kvm $USER` (then re-login) on the build
host if you want faster boots. Software emulation works correctly, just
slowly; don't mistake a long "activating" `cloud-final.service` for a
hang — check `ps aux | grep qemu` for actual CPU usage before assuming
it's stuck.

## `qemu-system-x86_64 -nographic` is incompatible with `-daemonize`

**Symptom:** `boot-vm.sh` failed immediately with
`-nographic cannot be used with -daemonize`.

**Fix:** use `-display none` (plus `-serial file:...` for console
logging) instead of `-nographic` when also passing `-daemonize`.
