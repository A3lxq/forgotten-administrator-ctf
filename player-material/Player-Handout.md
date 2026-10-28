# The Forgotten Administrator — Player Handout

Everything you need to start, in one place. (`Story.md`, `Rules.md`,
`Getting-Started.md`, and `Flag-Submission.md` cover the same ground in
more depth if you want it — this is the concise version.)

## The story, briefly

John (`jtyler_dev`) built and ran an internal web app — **ledger-tools**
— then left in 2019 and handed it to an administrator. He left traces
behind: a profile page, a project page, old photos, and a Git history.
The app's web accounts (`john`, `admin`) and the server's own Linux
accounts (`john`, `admin`, `root`) are **separate things** — don't
assume one login gets you the other. Something was never fixed after
John left, and the administrator's own account hints at what, and
where it ended up. Your job: follow the trail from John, into the app,
onto the box, and up to `root`.

## What you're given

Just the web app's address (your instructor gives you this, e.g.
`http://<lab-ip>:8080/`). Its landing page (`/`) links to all the
handover material — John's old profile and project pages, photos, the
`ledger-tools` Git repo, and the decrypt tool — under `/materials/`.
Nothing else is downloaded or handed to you separately unless your
instructor says otherwise.

**Your starting web login**: `john` / `Summer2019!` — use the "sign in"
link on the landing page. Start with the handover material first,
though; there's a reason it's linked before the login form.

**Decrypt tool** (linked from `/materials/`), for anything you find
encrypted, once you have the right password:
```
python3 flagcrypto.py decrypt "<password>" <file> -
```

**Tools worth having**: `exiftool` (metadata stage), `git` (history
stage — `log`, `show`, `log --diff-filter=D`), a browser or `curl` (web
stage), and an SSH client (for the privesc stage's follow-through, once
you've earned a credential for it).

## Flags and scoring

- **Genuine flags**: `SYN{...}` — 5 of them, 800 points total (100,
  100, 150, 200, 250).
- **Decoy flags**: `FFLAG{...}` — 5 of them, one per stage, genuinely
  findable and often the faster/easier-looking find. They score 0
  points. Finding one isn't a mistake, submitting one just doesn't
  score — check the prefix before you celebrate.
- **Original Flag 3 is special**: its decrypted value isn't just a flag
  to submit — keep it. It's a password you'll need again much later. (It
  is not any Linux account's login password.)
- **Submitting**: your instructor will give you the scoring dashboard's
  address separately (a different address from the CTF box itself).
  Pick a team name + PIN once, then submit flag values there as you
  find them — the leaderboard updates live. If you ever lose
  connection or the dashboard restarts, the same team name + PIN gets
  you straight back in with your scores intact.
- **Stuck?** Ask for a hint right from the dashboard (the "ask for a
  hint" link) — it's a private thread between your team and the
  instructor only, and it doesn't cost you anything. The instructor may
  also occasionally send every team a message unprompted — don't assume
  everything that shows up there is a genuine nudge; read it the same
  way you'd read anything else in this challenge.

## Rules

1. **Scope.** Only attack the lab VM you were given. Not the host
   machine, other teams' instances, the instructor's machine, or
   anything outside the lab network.
2. **No denial-of-service.** Don't intentionally crash, flood, or lock
   up the VM or the web app. Accidents happen — tell your instructor,
   they can reset it.
3. **No attacking other teams**, if this event has multiple teams/VMs.
   Stay inside your own.
4. **Flags are evidence of understanding, not the goal by themselves.**
   Decoys exist on purpose and cost nothing to find.
5. **Ask for hints.** Not cheating — that's what the dashboard's hint
   thread is for.
6. **Report, don't exploit, anything outside the intended path.** If
   something seems unintended (not one of the five documented stages),
   stop and tell your instructor instead of using it to skip ahead.
7. **No AI assistance.** No ChatGPT, Copilot, or any other AI tool to
   solve stages or find flags. Solve it yourself, with your own team,
   using your own reasoning.
8. **No flag sharing.** Don't give, trade, or post your flags (genuine
   or decoy) to or for another team. Every team finds and submits its
   own.

Good luck.
