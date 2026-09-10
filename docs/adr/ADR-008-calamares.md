# ADR-008: Calamares graphical installer

- Status: superseded as the primary UI by ADR-009; retained as optional
- Date: 2026-09-02

## Decision

Use the CachyOS-maintained Calamares 3.4 engine for the user-facing installer.
Pin the live-only binary artifact by version and SHA-256, replace all CachyOS
configuration and branding with Najs-owned files, and keep installed-system
packages on the official Arch repositories.

Expose location, keyboard, bootloader, automatic and manual partitioning, LUKS2,
desktop, kernel, graphics, software collections, account, summary, and progress
pages. Put an executable **Install Najs** launcher directly on the live desktop.
The interface and Najs-authored descriptions use English.

Keep the existing silent Archinstall path as a fallback and as the deterministic
blank-disk installation test until a reliable GUI automation test covers the
same Calamares choices and the installed-system reboot.

## Consequences

The live image consumes a GPL-3.0-or-later Calamares build maintained by CachyOS
and records the exact archive hash in the build pipeline. The package is
extracted into the live filesystem and is not installed into the target. Najs
owns its module configuration, styling, images, package selections, and target
finalization logic.

The Calamares build links to Boost.Python 1.91. The build extracts only its
three versioned runtime libraries (`boost_python314`, `boost_container`, and
`boost_graph`) from a SHA-256 pinned official Arch Linux Archive package. It
does not replace the live system's current Boost package and is not copied or
installed into the target.

## Sources

- https://github.com/CachyOS/cachyos-calamares
- https://github.com/CachyOS/CachyOS-Live-ISO
- https://calamares.io/
- https://archive.archlinux.org/packages/b/boost-libs/
