# Skill: OSINT & Web Reconnaissance

## When to use this

At the very start of any challenge like this, and whenever you land on
a new page or endpoint you haven't examined carefully yet.

## The core technique

Most agents (and most humans) read a web page for its *rendered*
content and stop. Investigation means reading it as data:

1. **Fetch the raw response, not a rendered summary.** Use `curl` (or
   equivalent) and actually read the HTML/text that comes back —
   don't rely on a mental model of "what a page like this usually
   says."
2. **Read every line, especially the boring ones.** A changelog, a
   footer, an "about" blurb, a commit list — these are exactly where
   something small and specific gets buried in otherwise-ordinary
   prose. If a sentence has a noun phrase that looks like an ID, a
   hash, a version string, or anything in an unusual bracket/brace
   format, that's worth flagging even if it's not visually
   highlighted.
3. **Treat visually prominent things with suspicion, not trust.** A
   bold callout, a colored box, or anything that says "look at me" is
   exactly as likely to be a deliberate distraction as a genuine
   find — in a well-built challenge, more likely. Obviousness is not
   evidence of correctness.
4. **Correlate identities across pages.** A username, project name, or
   handle that appears on one page and links (even just by name, not
   a hyperlink) to another page is a signal to go look at that other
   page too.
5. **Check links you haven't followed.** A page that mentions another
   resource by name, even without a clickable link, is telling you
   where to look next.

## Practical commands

```
curl -s <url>                      # raw response
curl -s <url> | grep -i <keyword>  # scan for something specific
curl -sI <url>                     # headers only, sometimes reveal paths
```

If the target is a web app, also check its root URL (`/`) for a
landing page — a well-built target doesn't require you to guess paths;
it tells you where to go next from the front door.

## What NOT to do

- Don't assume the first flag-shaped string you see is the real one.
  See `SKILLS.md`'s note on decoys.
- Don't stop reading a page once you've found one interesting thing —
  there may be a second, less obvious thing on the same page.
