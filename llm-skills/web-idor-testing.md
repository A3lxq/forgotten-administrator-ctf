# Skill: Web IDOR / Broken Object-Level Authorization Testing

## When to use this

Whenever you're logged into a web application and it shows you *your
own* data via some kind of identifier in the URL or request — a
record ID, a user ID, a document number, anything that looks like a
reference to a specific object.

## The core technique

IDOR (Insecure Direct Object Reference) is one of the most common real
web vulnerabilities: an endpoint checks that you're *logged in*, but
not that the specific object you're asking for actually *belongs to
you*.

1. **Find your own object's identifier first.** Log in normally and
   see what ID appears when you view your own data (e.g.
   `/records/mine` redirecting to `/records/7`, or similar).
2. **Change only the identifier, nothing else about your session.**
   Stay logged in as yourself; just request a different ID:
   ```
   curl -s -b cookies.txt <url>/<resource>/<different-id>
   ```
3. **Try adjacent and small numbers first** (id-1, id+1, 1, 2, 3...) —
   object IDs are very often sequential integers, so a small
   administrative or "special" record is often a low number even if
   your own account was created later.
4. **Compare the response, not just the status code.** A 200 response
   with different content than your own object — especially content
   that mentions a role, account, or data you shouldn't have — is the
   signal, not just "it didn't 403."
5. **A real IDOR returns genuinely different, unauthorized content.**
   If changing the ID just 404s or redirects you back to your own
   data, that's *not* a vulnerability — it means the check is actually
   happening. Don't report a non-vulnerability as a finding.

## Practical commands

```
# capture a session first
curl -s -c cookies.txt -b cookies.txt -X POST <url>/login -d "username=...&password=..."

# then probe object IDs
curl -s -b cookies.txt <url>/records/1
curl -s -b cookies.txt <url>/records/2
curl -s -b cookies.txt <url>/records/3
```

## What this often leads to

A disclosed administrative record frequently contains a credential or
pointer to a further privileged function. See `credential-reuse.md`
for the very next thing to check once you find a credential this way —
don't assume you need a second, more complex exploit before checking
whether the simple thing (the same credential working somewhere else)
already works.
