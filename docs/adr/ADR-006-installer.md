# ADR-006: Archinstall for the installation prototype

- Status: restored as the primary UI by ADR-009
- Date: 2026-09-01

## Problem

Najs needs a testable installation path before investing in a graphical
installer. The chosen component must support UEFI, Btrfs, encryption,
systemd-boot, UKI, users, locale, networking, and unattended VM tests.

## Options

Calamares, Archinstall, and a new Najs installer were considered. Calamares is a
mature graphical framework but is not present in the signed official Arch
repositories and would require Najs packaging and update ownership immediately.
A new installer would duplicate risky partitioning and encryption work.

## Decision

Use the signed upstream Archinstall package for the pre-alpha installation
backend. The Najs wizard collects disk, filesystem, encryption, account, locale,
desktop, and package choices, then generates configuration and invokes
Archinstall in silent mode. Archinstall still owns disk, filesystem, bootloader,
account, and package operations. After a successful installation, the wrapper
provisions the Najs release metadata, manifest, profiles, welcome center, and CLI
into the mounted target.

No credential file is stored in the ISO or repository. The temporary credential
file is root-only and removed after success or failure. The wrapper refuses
non-UEFI installation in this phase and requires an explicit full-disk
erase-and-install confirmation.

## Consequences

The terminal installer is launched from the desktop as Cocky Installer. Its
generated Btrfs layout is an installation baseline; generation activation
remains disabled until the layout and UKI pair are verified after installation.
Calamares remains available as an optional advanced frontend.

## Sources

- https://archinstall.archlinux.page/installing/guided.html
- https://github.com/archlinux/archinstall
- https://github.com/calamares/calamares
