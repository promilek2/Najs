# Installation

The live desktop contains a **Cocky Installer** icon. It opens the original Najs
keyboard-driven dialog wizard in Konsole without changing its visual style. The
wizard uses the current validated Archinstall backend and shows a summary, one
clear erase-and-install confirmation, and progress reporting.

The wizard selects:

- language, keyboard layout, time zone, hostname, and administrator account
- a dedicated whole-disk target, Btrfs/ext4/XFS, zram, and optional LUKS
- KDE Plasma, GNOME, Hyprland, Xfce, or Cinnamon
- graphics support for automatic/open drivers, AMD, Intel, recent NVIDIA, or VM
- stable, LTS, Zen, or Hardened kernel and systemd-boot or GRUB
- Office, Multimedia, Gaming, Creative, Development, Communication,
  Virtualization, Accessibility, and Advanced Tools collections

Cocky Installer excludes mounted disks and revalidates the selected disk
immediately before installation. One password of at least four characters is
entered once for the account and is also used for LUKS when encryption is
selected. Packages come from the official Arch repositories.

No password or disk device is embedded in the ISO. Temporary credentials are
stored in a root-only runtime file and removed after success or failure. After a
successful install, the Najs finalization step provisions the CLI, profiles,
manifest, defaults, services, branding, and generation metadata into the target.

The first graphical login opens a small cross-desktop Najs Welcome window with
direct links to settings, software installation, files, diagnostics, and local
help. It can be disabled from that window and reopened from the application menu.

The Cocky Installer backend is verified by an automated blank-disk QEMU install
and reboot test. The optional Calamares frontend has separate configuration,
launch, and visual checks and remains pre-alpha software.

Run `sudo /usr/local/bin/najs-calamares` from the live system only when manual
partitioning or F2FS is required.

For an isolated manual test, run `./najs-dev run install-vm` in a development
shell containing QEMU and OVMF. The command creates a sparse 40 GiB QCOW2 image
under `.build/` and does not expose host disks to the guest.
