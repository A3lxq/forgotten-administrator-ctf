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

## `rsync -a` silently loosened `/root` from mode `700` to `775`

**Symptom:** after switching `deploy-flags.sh` from `cp` to
`rsync -a --delete` (to properly remove a decoy file that had been
dropped from the staged source — `cp` doesn't delete stale files, so a
removed decoy kept lingering on the VM), `/root` itself came out as
`drwxrwxr-x` (775) instead of the intended `drwx------` (700). Caught
by actually reading `ls -la /root`'s output rather than assuming the
swap from `cp` to `rsync` was behavior-equivalent.

**Cause:** `rsync -a` includes `-p` (preserve permissions) for every
directory it touches — including the *pre-existing destination
directory itself* when syncing `src/` into an already-existing `dest/`
with trailing slashes on both sides. The local staging directory
(`vm/flag-staging/root/`, created by Python's `Path.mkdir()` under this
build's umask) had mode `775`, and that got copied onto `/root` on the
VM, which already existed with its own, different, correct mode `700`.
`cp` had never done this because it only touches the directory
*contents*, never resets a pre-existing destination directory's own
mode.

**Fix:** added `--no-perms` to every `rsync` call in `deploy-flags.sh`
that targets a pre-existing directory (`/home/admin/evidence`,
`/home/admin/flags`, `/root`), plus an unconditional `chmod 700 /root`
/ `chmod 750` on the evidence dirs right after, as a hard safeguard
that doesn't depend on getting `rsync`'s flags right. Re-verified live
and on an independently-booted copy of the exported VM image.

**Lesson:** when swapping `cp` for `rsync -a` (or vice versa) to fix
one specific gap (here: stale-file cleanup), don't assume the two are
otherwise equivalent — `rsync -a`'s archive mode touches far more
(permissions, timestamps, the destination directory entry itself) than
a plain recursive copy does. Check the *destination's own* metadata
after the change, not just its contents.

## Networking never comes up when the OVA is imported into VirtualBox (NAT or Bridged, either one)

**Symptom:** imported the exported `.ova` into VirtualBox, booted it,
and the guest never gets an IP under *either* NAT or Bridged networking
— `arp-scan`/`netdiscover` find nothing, and VirtualBox's own NAT
(which has its own built-in DHCP server) doesn't hand out a lease
either. This image had only ever been tested under QEMU before a real
VirtualBox import was tried.

**Cause:** `vm/cloud-init/user-data.yaml` never supplied an explicit
`network-config` to the NoCloud datasource. Without one, cloud-init's
*fallback* network generator detects whatever NIC is present at first
boot and writes a netplan rule **pinned to that NIC's exact MAC
address**:
```yaml
network:
  ethernets:
    enp0s2:
      match:
        macaddress: "52:54:00:12:34:56"   # QEMU's own virtio MAC
      dhcp4: true
```
That MAC is QEMU/virtio-specific. VirtualBox assigns its virtual NIC a
completely different MAC, so this rule never matches on import, the
interface is never configured, and no DHCP request is ever sent —
identically under NAT or Bridged, since the problem is entirely on
the guest side and has nothing to do with which VirtualBox networking
mode is selected. (Confirmed by checking `/etc/netplan/50-cloud-init.yaml`
directly on the dev VM — it really was MAC-pinned.)

**Fix:** added `vm/cloud-init/network-config.yaml`, matching by
interface *name* instead (`match: {name: "en*"}`), and pass it via
`cloud-localds -N cloud-init/network-config.yaml ...` in
`create-disk.sh`. This is hardware/hypervisor-agnostic — any NIC that
gets a predictable `en*`-style name (virtio, e1000, whatever the
hypervisor emulates) works identically. For the already-provisioned
VM, patched `/etc/netplan/50-cloud-init.yaml` directly and ran
`netplan apply`; confirmed the interface stayed up with the same
behavior afterward, then re-exported.

**How this was actually found:** by SSHing into the still-running dev
VM and reading `/etc/netplan/*.yaml` and
`/var/lib/cloud/instances/*/network-config.json` directly, rather than
continuing to guess from symptoms alone. Worth doing this first any
time "networking doesn't work after moving a cloud image to different
virtual hardware" comes up — the actual written config settles it in
one command, where guessing (NIC type? chipset? promiscuous mode?)
can burn a lot of time on the wrong theory.

## OVF descriptor's `VirtualSCSI` controller was never actually tested against real VirtualBox/VMware

**Symptom:** no specific error observed, but noted as a risk while
debugging the networking issue above — `vm/scripts/export-ova.sh`'s
hand-written OVF descriptor declared the disk controller as a
VMware-style `VirtualSCSI` resource subtype, carried over from a
reference example rather than validated against an actual VirtualBox
import (no VirtualBox was available in the build environment itself).

**Fix:** switched to a plain IDE controller (`ResourceType 5`,
`ResourceSubType PIIX4`) — the one controller type every hypervisor
(VirtualBox, VMware, QEMU) implements identically and unambiguously.
Disk I/O performance doesn't matter for a small CTF lab VM; removing
ambiguity does.

## A password set in VirtualBox's GRUB recovery mode didn't survive a reboot

**Symptom:** reported while debugging the above — a password change
made via `passwd` in VirtualBox's recovery-mode root shell appeared
not to persist once back at a normal login prompt.

**Investigated, but NOT a disk-image bug:** tested directly on the
dev VM (no VirtualBox involved): set a test password with `chpasswd`,
captured its shadow hash, issued a real `sudo reboot`, and compared
the hash after boot — byte-identical. This image's filesystem
persistence is fine; a `chpasswd`/`passwd` change survives a genuine
reboot on this disk.

**Likely explanation (unconfirmed — would need the user's VirtualBox
session to verify directly):** the classic Ubuntu recovery-mode
gotcha where `/` mounts read-only until you explicitly run
`mount -o remount,rw /` before changing anything. If `passwd` ran
against a read-only root, the change could appear to succeed but never
actually reach disk. If this recurs: run that remount command first,
and separately check `mount | grep ' / '` to confirm the root
filesystem's actual mount mode before assuming a deeper problem.
