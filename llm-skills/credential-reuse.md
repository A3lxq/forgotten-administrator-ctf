# Skill: Credential Reuse Hunting

## When to use this

Immediately after finding *any* credential — a password, API key, or
token — from any source (a leaked file, an IDOR'd record, a config
file, metadata, anything).

## The core technique

A huge fraction of real-world breaches come down to exactly this: a
password gets reused across a web login and a system account, or
across two different services, because someone found it more
convenient than tracking separate credentials. Always test for this
*before* assuming you need to find or build a more complex exploit.

1. **Identify every place the same identity might plausibly log in.**
   If a credential is tied to a username/account name, that account
   may exist beyond just the one place you found the password:
   - The same web app, under a different role
   - SSH on the same server (if you know or can discover its address)
   - Any other service mentioned nearby in the same text
2. **Test SSH specifically if the target is a Linux box you can
   reach.** Try the found username/password combination directly:
   ```
   ssh <username>@<host> -p <port>
   # if it prompts for a password, try the one you found
   ```
   If SSH offers key-based auth only and rejects password attempts
   outright, that specific account's password reuse path is closed —
   but try other accounts the same way if you have more than one
   credential.
3. **Don't skip this step because it feels "too easy."** In a
   well-built lab, an easy-looking step that actually works *is* the
   intended path — the lesson is precisely that credential reuse is a
   simple mistake with serious consequences, not that the exploit
   needs to be elaborate.
4. **Confirm what you actually got**, don't assume: run `id` or
   `whoami` immediately after a successful login to confirm exactly
   which account you're now operating as and what group memberships
   it has — this matters for your next step (enumeration/privesc).

## What NOT to do

- Don't immediately jump to code-execution vulnerabilities (injection,
  deserialization, etc.) on an admin panel before checking whether a
  disclosed credential just... works, somewhere more direct.
- Don't give up on an account after one failed attempt if you have
  more than one credential or more than one username to try it with.
