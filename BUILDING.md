# Building Najs

## Host requirements

- Git
- Python 3.11 or newer
- Podman or Docker for the isolated Archiso build
- QEMU x86_64 and OVMF for the UEFI smoke test
- At least 20 GiB free disk space

Do not build against the host root. `najs-dev build iso` uses a privileged,
disposable container because `mkarchiso` needs mount and loop-device access.

## Commands

```bash
./najs-dev bootstrap
./najs-dev build cli
./najs-dev test
./najs-dev build iso
./najs-dev test vm
./najs-dev test install-vm
./najs-dev run vm
./najs-dev run install-vm
```

Rootless Podman cannot provide the mount operations required by `mkarchiso`.
When Podman is the selected engine, enter a development shell and run the ISO
command with `sudo`; Docker installations may provide equivalent privileges via
their daemon. No package is installed into the host root.

Artifacts are written below `out/`; temporary state is written below `.build/`.
The container base is not digest-pinned yet, so ISO builds are not reproducible
at this stage. Pinning package snapshots and the builder digest is tracked as a
release blocker rather than being represented as complete.

Build timestamps use the latest Git commit. Before the first commit, developer
builds use the current time so software that rejects epoch-zero configuration
files, including SDDM, can load them correctly.

`run install-vm` creates or reuses `.build/vm-install/najs-install.qcow2` and
attaches no host block devices. `test install-vm` instead creates a fresh 40 GiB
QCOW2 image, installs unattended, reboots from that image, and verifies the
installed desktop and services. Neither path exposes a host block device.
