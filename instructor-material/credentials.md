# Instructor Credentials — Direct Access

> **PRIVATE.** Never give this file, or any credential in it, to
> players. This is for the instructor/operator only — resetting the
> lab, checking logs, or inspecting state without going through the
> CTF's intended exploit path.

## SSH as `ctfbuilder` — full admin access, key-based

The one account meant for you, the operator. Full passwordless `sudo`
(`NOPASSWD:ALL`) — this is how you get a root shell, check logs, or
fix anything, without ever touching the `admin`/`john` accounts or the
intended exploit chain.

```
ssh -i vm/keys/ctfbuilder_ed25519 -p <port> ctfbuilder@<host>
```

- **Dev VM (QEMU, this repo's own `vm/scripts/boot-vm.sh`):**
  `<host>` = `127.0.0.1`, `<port>` = `2222`.
- **An OVA imported into VirtualBox/VMware:** `<port>` is whatever you
  set up as a port-forward to guest `22` (see `vm/dist/IMPORT.md`).
  `vm/keys/ctfbuilder_ed25519` only matches the public key baked into
  images *you* built from this repo — if you imported someone else's
  already-built OVA, this key won't be the right one for it.

**Get a root shell:** SSH in normally, then run `sudo -i` once
connected (interactive). This is the correct way to check logs,
inspect `/root`, or make any administrative change — never anything
that requires knowing the `root` account's own password, because
there isn't one (`root` login is disabled entirely, by design — see
`vm/README.md`).

**For a single non-interactive command without a separate login step**
(verified working):
```
ssh -i vm/keys/ctfbuilder_ed25519 -p <port> ctfbuilder@<host> \
    'sudo bash -c "<your command here>"'
```

**Useful things to check, as root:**
```
sudo systemctl status forgotten-admin          # the web app
sudo journalctl -u forgotten-admin -n 100      # its recent logs
sudo cat /var/log/admin-tools-cleanup.log      # the Stage 5 cron job's log
sudo ls -la /home/admin/flags /home/admin/evidence /root
```

## The Linux `john` and `admin` accounts (for completeness — not how you should normally get in)

These are the two *in-story* accounts, seeded with disposable fictional
passwords (also documented in `flag-manifest.json` and
`vm/scripts/remote-provision.sh`):

| Account | Password | SSH? | Notes |
|---|---|---|---|
| `john` | `Summer2019!` | No (password auth not offered for this account) | Console login only |
| `admin` | `N3tOps-Diag#7` | **Yes** — this is the intended Stage 4 player path | Same password for console and SSH, on purpose (credential reuse is the lesson) |

You generally don't need either of these for instructor purposes —
`ctfbuilder` + `sudo -i` can do everything these can, plus more. Use
`admin`'s credential if you specifically want to see exactly what a
player sees after completing Stage 4 (e.g. to sanity-check the player
experience), not as your normal way in.

## Resetting

See `reset-guide.md` for the full explanation. In short, from the
project root:
```
./scripts/reset.sh app       # wipe + re-seed just the web app's DB
./scripts/reset.sh privesc   # restore the Stage 5 weakness to clean
./scripts/reset.sh vm        # roll back the whole VM to the clean-start snapshot
```
All three use `ctfbuilder` under the hood — none of them need the
`john`/`admin` passwords above.

## If you only have an imported OVA, no SSH key

If someone handed you a pre-built `.ova` without the matching
`ctfbuilder` private key (the key is deliberately never bundled with a
distributed image — see `vm/dist/IMPORT.md`), you don't have root
access to that specific VM instance at all. Your options: ask whoever
built it for the key, or treat it as disposable and re-import a fresh
copy when you need a clean state (nothing on a never-SSH'd-into
instance can have drifted from the shipped baseline).
