# ADR-006: Archinstall for the installation prototype

- Status: accepted for pre-alpha
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
prototype. Najs supplies a non-secret catalog and an easy selection wizard that
generates the preset. Archinstall owns disk, filesystem, bootloader, account, and
package operations. After a successful installation, the wrapper provisions the
Najs release metadata, manifest, profiles, welcome center, and CLI into the
mounted target.

No credential file is stored in the ISO or repository. Disk and user choices
remain interactive. The wrapper refuses non-UEFI installation in this phase.

## Consequences

The prototype is a terminal installer launched from the desktop, not the final
Najs installation experience. Its generated Btrfs layout is an installation
baseline; generation activation remains disabled until the layout and UKI pair
are verified after installation. Calamares can be reconsidered after Najs has a
signed package repository, or replaced by a focused graphical frontend over a
stable installation backend.

## Sources

- https://archinstall.archlinux.page/installing/guided.html
- https://github.com/archlinux/archinstall
- https://github.com/calamares/calamares
