# ADR-005: Generation activation and boot

- Status: proposed; implementation follows live ISO
- Date: 2026-08-31

## Decision

Installed Najs will use UEFI, systemd-boot, generation-specific Unified Kernel
Images, dracut, and systemd automatic boot assessment. A generation ID pairs a
Btrfs root with exactly one immutable UKI name and transaction record.

Composition clones the active root, runs pacman against the candidate in an
isolated mount namespace, validates it, stages a UKI away from the real ESP, and
publishes it before changing the preferred boot entry. At least one known-good
generation remains selectable.

The first live ISO may use Archiso's standard boot path. That is bootstrap media,
not the final installed-system generation design.

## Sources

- https://uapi-group.org/specifications/specs/boot_loader_specification/
- https://uapi-group.org/specifications/specs/unified_kernel_image/
- https://www.freedesktop.org/software/systemd/man/latest/systemd-boot.html
- https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/
- https://dracut-ng.github.io/dracut/man/dracut.8.html
