# Reset Guide

> Private — instructor use only.

## Resetting between teams/runs

Three independent layers, reset separately (so you can reset only what
you need):

### 1. Web application state (DB, sessions)
```
cd vm
ssh -i keys/ctfbuilder_ed25519 -p 2222 ctfbuilder@127.0.0.1 \
    'sudo systemctl stop forgotten-admin && sudo rm -f /opt/forgotten-admin/app/instance/*.sqlite3'
./scripts/provision.sh   # re-seeds the DB, restarts the service
```

### 2. Privilege-escalation mechanism
```
cd vm
./scripts/reset-privesc.sh
```
Restores `/opt/admin-tools/cleanup.sh` to its clean content/permissions
and removes known exploit artifacts. See `privesc-design.md` for what
it does and doesn't touch.

### 3. Full VM reset (new team, clean slate)
Fastest: snapshot-based. Take a snapshot right after Phase 4's
`deploy-flags.sh` completes (clean state, before any team touches it):
```
cd vm
./scripts/stop-vm.sh
qemu-img snapshot -c clean-start disks/forgotten-admin.qcow2
./scripts/boot-vm.sh
```
To roll back to that snapshot for the next team:
```
cd vm
./scripts/stop-vm.sh
qemu-img snapshot -a clean-start disks/forgotten-admin.qcow2
./scripts/boot-vm.sh
```
List snapshots: `qemu-img snapshot -l disks/forgotten-admin.qcow2`.

Slowest but most thorough (full rebuild from scratch):
```
cd vm
./scripts/stop-vm.sh
./scripts/create-disk.sh --force
./scripts/boot-vm.sh
# wait for cloud-init (several minutes under software emulation)
./scripts/provision.sh
./scripts/deploy-flags.sh
```

## Never reset the host

None of the above touches anything outside `vm/disks/`,
`vm/seed/`, or the VM's own filesystem. The host machine (this
development environment) is never modified by any reset step.

## Verifying a reset worked

```
./scripts/run-tests.sh                                   # app-level tests still pass
cd vm && ssh ... 'id admin'                               # admin has no sudo, no leftover group changes
ssh ... 'test -e /tmp/rootbash && echo BAD || echo OK'    # no leftover SUID shell
ssh ... 'sudo -u admin test -w /opt/admin-tools/cleanup.sh && echo OK'  # weakness still present
```
