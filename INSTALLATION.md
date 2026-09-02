# Installation

The live desktop contains an **Install Najs** launcher. It first opens a simple
keyboard-driven wizard. Arrow keys move, Space toggles application groups, and
Enter accepts a page.

The wizard selects:

- KDE Plasma, GNOME, Hyprland, Xfce, or Cinnamon
- graphics support for automatic/open drivers, AMD, Intel, recent NVIDIA, or VM
- a Minimal, Daily, Gamer, Creator, Developer, or Everything starting point
- individual application groups and optional additional official packages

The generated configuration then starts the signed upstream Archinstall
package with Najs defaults for PipeWire, NetworkManager, systemd-boot, UKI, and
the selected desktop and packages.

Disk selection, partitioning, encryption, locale, and user credentials remain
interactive. No password or disk device is embedded in the ISO. After a
successful Archinstall run, the wrapper provisions the Najs CLI, profiles,
manifest, system defaults, services, branding, and initial-generation metadata
into `/mnt/archinstall`.

The first graphical login opens a small cross-desktop Najs Welcome window with
direct links to settings, software installation, files, diagnostics, and local
help. It can be disabled from that window and reopened from the application menu.

This flow is verified by an automated blank-disk QEMU installation and reboot
test. It remains pre-alpha software and should not be used on a disk containing
valuable data.

For an isolated manual test, run `./najs-dev run install-vm` in a development
shell containing QEMU and OVMF. The command creates a sparse 40 GiB QCOW2 image
under `.build/` and does not expose host disks to the guest.
