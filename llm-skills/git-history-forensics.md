# Skill: Git History Forensics

## When to use this

Whenever you're handed, or find, a `.git` repository (or an archive
containing one) — even if its current, checked-out files look boring
or incomplete.

## The core technique

**The current working tree is only the most recent snapshot.** A
repository's real content is its full history, including anything
that was later deleted or changed:

1. **List the full commit history first**, not just the latest state:
   ```
   git log --oneline --all
   ```
   If the number of commits is more than you'd expect from the current
   file list, something was removed along the way.
2. **Read every commit message**, not just the file diffs. A commit
   message is free-text and challenge authors (and real developers)
   routinely put passwords, hints, or context there that doesn't
   appear in any file.
3. **Recover a file from an old commit without checking it out** —
   this reads a specific file's content at a specific point in
   history, leaving your working tree untouched:
   ```
   git show <commit>:<path/to/file>
   git show <commit>:<path/to/file> > recovered_file
   ```
4. **Find exactly what was deleted and when:**
   ```
   git log --oneline --diff-filter=D --name-only
   ```
5. **Be skeptical of the newest-looking history.** If there are
   multiple old/removed files, the most recently-removed one (closest
   to the current HEAD) is not automatically the important one — it
   might be a deliberate decoy placed exactly because it's the first
   thing a quick `git log` scan surfaces.

## Practical commands

```
git log --oneline --all                      # full history, compact
git log --diff-filter=D --name-only           # what got deleted
git show <rev>:<path>                         # read an old file's content
git show <rev>:<path> > out.bin               # save it to disk
git log -p <path>                             # full diff history of one file
```

## What NOT to do

- Don't assume `git log` with no arguments shows everything — check
  `--all` in case there are other branches/refs.
- Don't trust that the commit closest to HEAD is the one that matters
  just because it's the first one you see.
