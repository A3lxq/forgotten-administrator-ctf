# Skill: File Metadata Forensics

## When to use this

Whenever you're given, or find a link to, a file — especially an
image, document, or any binary — and the file's *visible content*
seems too plain to be the point.

## The core technique

Files carry data beyond what you see when you open them normally:

1. **Inspect metadata with a dedicated tool, not just by opening the
   file.** `exiftool <file>` (installed on most Linux systems; install
   with your package manager if missing) dumps every metadata field a
   file carries — EXIF tags on images, document properties, embedded
   comments.
2. **Look at every field exiftool prints, not just the obvious ones**
   (`DateTimeOriginal`, `GPSPosition`). Fields like `Comment`,
   `Artist`, `Description`, `UserComment`, or custom/software-specific
   tags are common places to hide or disclose something deliberately.
3. **If a field's value looks like hex or base64, it might be
   encrypted or encoded data, not a string to read directly.** Convert
   it back to bytes before deciding it's meaningless:
   ```
   echo "<hex string>" | xxd -r -p > recovered.bin
   # or, in Python:
   bytes.fromhex("<hex string>")
   ```
4. **A password for encrypted data is often sitting in a *different*
   field of the same file, or an adjacent file** — check things like
   `Artist`/`Author` fields specifically when `Comment` looks
   encrypted.
5. **Don't assume the file's visible pixels/content matter at all.** A
   challenge may ship a trivial or placeholder image purely as a
   carrier for its metadata.

## Practical commands

```
exiftool <file>                 # dump all metadata
exiftool -Comment -Artist <file>  # just specific fields
file <file>                     # confirm the actual file type
strings <file> | less           # last resort: raw string scan of the binary
```

## What NOT to do

- Don't conclude "nothing here" after only looking at the file
  visually — always run a metadata tool first.
- Don't ignore a field just because its value looks like noise —
  noise-looking hex/base64 is often the actual payload.
