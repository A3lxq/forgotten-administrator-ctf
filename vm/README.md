# VM — The Forgotten Administrator

Guest OS: **Ubuntu Server 24.04 LTS** (official cloud image), via
QEMU/KVM + cloud-init (NoCloud). See `instructor-material/build-guide.md`
for the full build procedure and rationale.

## Layout

```
vm/
    images/            base cloud image (downloaded, gitignored, large)
    cloud-init/        user-data.yaml, meta-data.yaml (committed — this
                       IS the reproducible account/package setup)
    seed/              generated cloud-init seed.img (gitignored)
    disks/             the VM's writable qcow2 disk + pidfile/monitor
                       socket (gitignored, large, contains lab state)
    keys/              instructor-only SSH keypair (gitignored — private
                       key must never be committed or shared with players)
    scripts/
        create-disk.sh       build the disk + seed from the base image
        boot-vm.sh            start the VM (host-only networking)
        stop-vm.sh            clean shutdown
        provision.sh          (run on host) deploy/update the app in the VM
        remote-provision.sh   (runs inside the VM) actual setup logic
    networking.md      host-only networking explained, port map, IPs
```

## Quick start (after the base image is downloaded — see build-guide.md)

```
cd vm
./scripts/create-disk.sh
./scripts/boot-vm.sh
# wait for first boot + cloud-init (several minutes under software
# emulation; faster with /dev/kvm access)
./scripts/provision.sh
```

## Accounts created by cloud-init

| Account      | Purpose                                              | Login method |
|--------------|-------------------------------------------------------|--------------|
| `ctfbuilder` | Instructor-only provisioning/maintenance             | SSH key only |
| `john`       | Story character (departed developer)                  | console password only, no SSH |
| `admin`      | Runs the vulnerable web app; the Stage 4 target        | SSH password (scoped to this account only, via an sshd `Match User admin` block — see `remote-provision.sh`), console password |
| `root`       | — | disabled (`disable_root: true`); no direct login |

Players are never handed any of these credentials directly. The
intended path to `admin` is: find the password via the web app's IDOR,
then `ssh admin@<vm>` with it — the same password is deliberately
reused on both sides (Stage 4's "second vulnerability" is credential
reuse, not code). See `instructor-material/solution-walkthrough.md`
for the verified end-to-end path.
