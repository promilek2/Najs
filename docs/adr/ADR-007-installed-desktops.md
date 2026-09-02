# ADR-007: Multiple installed desktop choices

- Status: accepted for pre-alpha
- Date: 2026-09-02

## Problem

The Plasma live environment is useful as a stable reference, but users need to
choose a familiar desktop without manually reconstructing package and display
manager settings. The selection must remain compatible with unattended install
tests and official Arch packages.

## Decision

Keep KDE Plasma Wayland as the live and reference desktop. The Najs installer
may generate Archinstall profiles for KDE Plasma, GNOME, Hyprland, Xfce, and
Cinnamon. Each choice records its environment, session type, display manager,
application groups, graphics choice, and package list in installation metadata
and the initial Najs manifest.

The Najs welcome center uses Zenity and XDG autostart so one maintained workflow
works across every supported desktop. Desktop-specific branding remains best on
the Plasma reference environment and must not block other sessions.

## Consequences

The installer catalog becomes the source of truth for package bundles and GPU
runtime additions. Every desktop configuration must be generated in unit tests;
the reference KDE selection continues through the full blank-disk VM test.

## Sources

- https://archinstall.archlinux.page/
- https://wiki.archlinux.org/title/Desktop_environment
- https://wiki.archlinux.org/title/Hyprland
