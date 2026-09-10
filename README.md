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
with OVMF. Najs Fold provides the system logo, Plasma live wallpaper, login
identity, terminal integration, a cross-desktop welcome center, and Fastfetch.

## Current commands

```text
najs info
najs status
najs doctor
najs validate --manifest manifest.toml
najs diff --manifest manifest.toml
najs completions bash
```

`najs diff` is read-only. Applying manifests and package transactions will be
added only with snapshot isolation and durable transaction records.
Completion definitions for Bash, Zsh, and Fish are installed system-wide in
Najs. `najs completions <shell>` can also generate them on demand.

## Installer choices

The **Cocky Installer** icon is placed directly on the live desktop and starts
the Najs dialog wizard in Konsole. It keeps the original keyboard-driven look
while using the current validated Archinstall backend. It offers:

- KDE Plasma, GNOME, Hyprland, Xfce, or Cinnamon
- automatic, AMD, Intel, recent NVIDIA, or virtual-machine graphics setup
- safe whole-disk installation with Btrfs, ext4, XFS, optional LUKS, and zram
- systemd-boot or GRUB and Stable, LTS, Zen, or Hardened kernels
- independently selectable Office, Media, Gaming, Creator, Development,
  Communication, and Virtualization application groups

The pinned Calamares frontend remains available as an optional advanced tool
for manual partitioning and F2FS, but it is no longer the default launcher.

Every installation includes:

- Firefox, archive tools, KeePassXC, firmware support, and broad font coverage
- PipeWire and the standard GStreamer codec set
- CUPS printing, Avahi discovery, and the printer configuration utility
- Bluetooth, NetworkManager OpenVPN support, and a default-on firewalld policy
- Flatpak with automatic Flathub configuration when a network is available
- QEMU, SPICE, and VirtualBox guest integration

The Gamer selection adds Steam, Lutris, Wine with Mono and Gecko, Winetricks,
Protontricks, GameMode, Gamescope, MangoHud, Vulkan tools and 32-bit GPU
libraries, Discord, and OBS Studio. The catalog is declared in
`installer/catalog.json`; generated choices are recorded in the installed Najs
manifest.

## Development

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

See `BUILDING.md`, `ARCHITECTURE.md`, and `ROADMAP.md` for the verified state and
next milestones.
