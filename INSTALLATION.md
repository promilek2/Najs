# Installation

The pre-alpha live desktop contains an **Install Najs** launcher. It starts the
signed upstream Archinstall package with Najs defaults for KDE Plasma, PipeWire,
NetworkManager, systemd-boot, UKI, and the complete `desktop` profile.

Disk selection, partitioning, encryption, locale, and user credentials remain
interactive. No password or disk device is embedded in the ISO. After a
successful Archinstall run, the wrapper provisions the Najs CLI, profiles,
manifest, system defaults, services, branding, and initial-generation metadata
into `/mnt/archinstall`.

This flow is verified by an automated blank-disk QEMU installation and reboot
test. It remains pre-alpha software and should not be used on a disk containing
valuable data.

For an isolated manual test, run `./najs-dev run install-vm` in a development
shell containing QEMU and OVMF. The command creates a sparse 40 GiB QCOW2 image
under `.build/` and does not expose host disks to the guest.
