# VM Networking

## Topology

This lab uses **QEMU user-mode networking (SLIRP)**, started by
`scripts/boot-vm.sh`. There is no bridge to any physical or shared
network, and no interface is placed in promiscuous/bridged mode. This
satisfies the "host-only / isolated" requirement without needing extra
host networking privileges.

```
   Player / instructor machine (host)
   127.0.0.1:2222  ──┐
   127.0.0.1:8080  ──┤   QEMU user-mode NAT (10.0.2.0/24 inside)
                      ▼
            ┌───────────────────┐
            │   Guest VM         │
            │   10.0.2.15 (eth0) │   <- typical SLIRP guest address
            │   sshd :22         │
            │   flask app :80    │
            └───────────────────┘
```

## Host vs. guest IP — do not confuse these

- **Host IP as seen from inside the guest**: `10.0.2.2` (the SLIRP
  gateway). If a reverse shell payload needs to connect back to "the
  machine running the listener," and that listener runs on the same
  host as this VM (e.g. during instructor testing), the target is
  `10.0.2.2`, **not** `127.0.0.1`. `127.0.0.1` inside the guest is the
  guest itself.
- **Guest IP as seen from the host**: not directly reachable by IP with
  user-mode networking — only via the forwarded ports below. If you
  need the guest's own address (e.g. for troubleshooting), SSH in and
  run `ip addr`.

## Port forwarding (host -> guest)

| Host address       | Guest address | Purpose                              |
|---------------------|----------------|---------------------------------------|
| 127.0.0.1:2222      | guest:22       | SSH, `ctfbuilder` only (instructor)   |
| 127.0.0.1:8080      | guest:80       | the vulnerable web app (Stage 4)      |

Both are bound to `127.0.0.1` on the host — nothing here is reachable
from another machine on your network, let alone the public internet.

**If players are on a separate physical/VLAN lab network** (not just
this single development host), do not reuse 127.0.0.1 bindings. Instead:
bind the forwarded ports to the host's lab-only interface IP (e.g.
`192.168.x.x:8080-:80`), confirm that interface is not routed to the
internet, and never bind to `0.0.0.0` on a host that also has a public
interface. Update `scripts/boot-vm.sh`'s `hostfwd` accordingly and
re-document the exact IP here before an event.

## Outbound access from the guest

SLIRP gives the guest outbound NAT by default — this is **required**
for `apt`/`pip` during provisioning, and it is also what makes the
intended command-injection → reverse-shell path (Phase 2's admin
diagnostics vulnerability) work: the guest can open an outbound TCP
connection to a listener on the host (at `10.0.2.2`) or, if the host
itself has internet access, anywhere outbound. For a live event where
you want to remove that general outbound reachability (defense in depth,
not required for the intended path), you can later add a QEMU network
ACL or run with `restrict=yes` on `-netdev user` — this intentionally
blocks ALL guest-initiated connections (including the one the intended
exploit path needs locally), so only do this if the actual listener is
reachable via a hostfwd instead; it is not enabled by default here to
avoid breaking the documented player path.

## Reverse shell catcher (for testing or during an event)

Run a listener on the host (or on the player's machine, once a
non-loopback hostfwd/lab network is in place):
```
nc -lvnp 4444
```
From inside the guest (after exploiting the command injection), connect
back to `10.0.2.2:4444` when testing against this same host, or to the
instructor/player machine's lab-network IP when running on a real
multi-host lab network.

## Start / stop / reset

- Start: `./scripts/boot-vm.sh`
- Stop:  `./scripts/stop-vm.sh`
- Snapshot/reset: see `instructor-material/reset-guide.md` (Phase 3/5),
  built on `qemu-img snapshot` internal snapshots of
  `disks/forgotten-admin.qcow2`.
