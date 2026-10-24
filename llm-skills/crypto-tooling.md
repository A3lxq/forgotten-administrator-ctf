# Skill: Using Provided Decrypt Tooling Correctly

## When to use this

Whenever a challenge gives you an encrypted file *and* a tool meant to
decrypt it (rather than expecting you to write your own crypto code).

## The core technique

1. **Read the tool's own usage/help text first** — don't guess its
   argument order:
   ```
   python3 <tool> --help
   python3 <tool>              # often prints usage with no args
   ```
2. **A typical pattern**: `<tool> decrypt <password> <ciphertext-file>
   <output>` — where `<output>` can often be `-` to print to stdout
   instead of writing a file.
3. **A wrong password should fail loudly, not silently produce
   garbage.** A well-built tool using authenticated encryption (e.g.
   AES-GCM) will raise a clear error on a wrong password rather than
   returning corrupted plaintext — if you get a clean error, the
   password is wrong (or you have the wrong file), not that the tool
   is broken.
4. **Track which password unlocks which file carefully, especially
   when there's more than one encrypted thing.** A common pattern in
   layered challenges: decrypting file A requires password P1 (which
   you found somewhere), and the *plaintext you get out of file A* —
   not P1 itself — turns out to be the password needed for a later,
   separate encrypted file B. Keep clear notes distinguishing "the
   password I used" from "the value I decrypted," because they are
   not interchangeable and later steps may specifically need the
   latter.
5. **If a decoy and a genuine item use the same tool**, don't assume
   just because decryption *succeeds* that the result is the genuine
   answer — check the decrypted value's format/prefix against what
   you were told counts as genuine before reporting it as solved.

## Practical pattern

```
python3 <tool> decrypt "<password>" <file.enc> -
```

## What NOT to do

- Don't assume a decryption failure means the tool is broken — it
  almost always means wrong password or wrong file.
- Don't discard a password after using it once if you have more
  encrypted files to try — a hinted or found password may unlock more
  than one file in the same challenge.
