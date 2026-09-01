<p align="center">
  <img src="branding/logo.svg" width="128" alt="Najs Fold logo">
</p>

# Najs

Najs is an experimental desktop Linux distribution built around a declarative,
transactional system-state layer. Arch Linux currently provides bootstrap
packages; Najs owns the manifest, profiles, transaction history, generations,
recovery policy, release channels, and desktop integration.

The project is pre-alpha. The CLI foundation is implemented and tested. The ISO,
UEFI live boot, and isolated blank-disk installation are verified in QEMU/KVM
with OVMF. Najs Fold provides the system logo, Plasma wallpaper, SDDM identity,
Konsole palette, and Fastfetch preset.

## Current commands

```text
najs info
najs status
najs doctor
najs validate --manifest manifest.toml
najs diff --manifest manifest.toml
```

`najs diff` is read-only. Applying manifests and package transactions will be
added only with snapshot isolation and durable transaction records.

## Built-in desktop

The `desktop` profile is a complete Plasma baseline rather than a minimal live
environment. It includes:

- Dolphin, Ark, Kate, Konsole, KCalc, Gwenview, and KDE Partition Manager
- Firefox, LibreOffice, Okular, KeePassXC, Haruna, Elisa, and Kamoso
- PipeWire and the standard GStreamer codec set
- CUPS printing, Avahi discovery, and the printer configuration utility
- Bluetooth, NetworkManager OpenVPN support, and a default-on firewalld policy
- Flatpak with automatic Flathub configuration when a network is available
- firmware updates, common device firmware, and broad font coverage
- QEMU, SPICE, and VirtualBox guest integration

The package and service baseline is declared in `profiles/desktop.toml` and is
kept in sync between the live ISO and the installed system.

## Development

```bash
./najs-dev bootstrap
./najs-dev build cli
./najs-dev test
./najs-dev build iso
./najs-dev test vm
./najs-dev run vm
./najs-dev run install-vm
```

See `BUILDING.md`, `ARCHITECTURE.md`, and `ROADMAP.md` for the verified state and
next milestones.
