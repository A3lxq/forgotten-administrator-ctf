# Story

John (`jtyler_dev`) was a developer who maintained an internal web
application — internally, the project was called **ledger-tools**. He
left the organization in 2019, handing the project to an administrator.

Before he left, John committed project files and notes to a Git
repository, and left personal traces online: a profile page, a project
page, and some old photos from the handover.

The application he built is still running. It has two separate kinds of
users:

- **Web application accounts**: `john` and `admin` — logins inside the
  app itself.
- **Linux (operating system) accounts**: `john`, `admin`, and `root` —
  separate identities on the actual server. A web login as "admin" is
  **not** the same thing as being the Linux `admin` user.

Something in the application was never fixed after John left. The
administrator's own account has evidence of this — and of what happened
after the last security review, when something important was moved
somewhere only `root` could reach.

Your job: reconstruct John's trail, find what he left behind, get into
the application the way it was never supposed to allow, and find out
what the administrator — and eventually root — were protecting.
