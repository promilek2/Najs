# Roadmap

## M0: foundation (verified)

- Rust CLI, strict manifest parser, and read-only diff.
- Archiso Plasma/Wayland live profile.
- Isolated build tooling and UEFI VM smoke-test entry point.

## M1: bootable live ISO (verified baseline)

- ISO builds successfully with Archiso 89.
- OVMF reaches systemd-boot and boots the live root.
- SDDM automatically starts a Plasma Wayland session.
- NetworkManager and `najs validate` are checked by the VM health probe.

Remaining M1 release work: pin the builder and package snapshot, test on physical
hardware, and complete visual review of the integrated Najs Fold identity.

## M2: installation

- Archinstall integration with Najs provisioning, Btrfs, and systemd-boot.
- Automated blank-disk QEMU install and reboot test (verified baseline).

## M3: transactions and generations

- Offline pacman adapter against a cloned root.
- Durable SQLite transaction metadata.
- Generation-specific UKI publication and boot counting.
- Tested failure handling and rollback.

## M4: declarative system

- `najs apply`, profile expansion, managed-file ownership, and conflict policy.
- Gaming and development profiles with hardware-aware package resolution.

## Alpha gates

All gates listed in the project specification remain open until automated tests
record successful ISO boot, installation, update, snapshot, and rollback runs.
