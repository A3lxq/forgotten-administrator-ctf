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
            │   flask app :8000  │
            └───────────────────┘
```

## Host vs. guest IP — do not confuse these

- **Host IP as seen from inside the guest**: `10.0.2.2` (the SLIRP
  gateway). Only matters if something running *inside* the guest needs
  to reach back out to a service on the host (e.g. while debugging) —
  `127.0.0.1` inside the guest is the guest itself, not your host.
  The intended player path doesn't need this at all: Stage 4's
  credential-reuse pivot is a normal *inbound* SSH connection (player
  → VM, via the forwarded port below), not something initiated from
  inside the guest.
- **Guest IP as seen from the host**: not directly reachable by IP with
  user-mode networking — only via the forwarded ports below. If you
  need the guest's own address (e.g. for troubleshooting), SSH in and
  run `ip addr`.

## Port forwarding (host -> guest)

| Host address       | Guest address | Purpose                                            |
|---------------------|----------------|-----------------------------------------------------|
| 127.0.0.1:2222      | guest:22       | SSH — `ctfbuilder` (key, instructor) and `admin` (password, the intended Stage 4 player path) |
| 127.0.0.1:8080      | guest:8000     | the vulnerable web app (Stage 4)                   |

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
for `apt`/`pip` during provisioning. The intended player path (Stage 4)
doesn't rely on this at all anymore — it's a plain inbound SSH
connection using a password found via the IDOR, not anything the guest
initiates outbound. For a live event where you want to remove general
outbound reachability anyway (defense in depth), you can run with
`restrict=yes` on `-netdev user` once provisioning is done — this
blocks ALL guest-initiated outbound connections; it's not enabled by
default here since it would also break `apt`/`pip` if you ever need to
re-provision.

## Start / stop / reset

- Start: `./scripts/boot-vm.sh`
- Stop:  `./scripts/stop-vm.sh`
- Snapshot/reset: see `instructor-material/reset-guide.md` (Phase 3/5),
  built on `qemu-img snapshot` internal snapshots of
  `disks/forgotten-admin.qcow2`.
