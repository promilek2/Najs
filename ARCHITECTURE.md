# Najs Architecture

## Product identity

Najs is a declarative and transactional desktop distribution over a standard
Linux package ecosystem. Unlike an image-only OS, users can request local state
changes. Unlike a traditional package wrapper, changes are composed into a new
bootable Btrfs generation before activation.

```text
Arch packages and pacman
          |
Najs platform packages
          |
manifest + profiles + policy
          |
offline transaction composer
          |
Btrfs root generation + matching UKI
```

## Version-one boundaries

- Arch Linux is an upstream and bootstrap source, not the product identity.
- KDE Plasma on Wayland is the live and reference desktop. Cocky Installer is
  the primary dialog frontend over Archinstall and can install KDE Plasma,
  GNOME, Hyprland, Xfce, or Cinnamon. Calamares remains an optional advanced
  frontend and shares the same Najs target provisioning.
- Pacman remains the low-level package manager.
- TOML manifests describe packages, services, profiles, and selected settings.
- A transaction will modify a writable clone of the active Btrfs root.
- A generation will pair one root subvolume with one UKI and transaction record.
- Persistent data is split by policy; all of `/var` is never excluded wholesale.
- Secure Boot, TPM-bound secrets, and graphical control center follow after the
  basic generation and rollback path is verified.

## Safety invariant

The active root and its boot artifact are never overwritten during composition.
The new root is validated first, its UKI is published under a unique name, and
only then is it made the preferred boot entry. At least one known-good pair is
retained. Btrfs and FAT do not provide a shared atomic transaction, so ordering
and boot counting are part of the design.

See `docs/adr/` for decisions and alternatives.
