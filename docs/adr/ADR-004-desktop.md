# ADR-004: KDE Plasma on Wayland

- Status: accepted for v1
- Date: 2026-08-31

## Decision

Ship KDE Plasma with Wayland as the single supported v1 desktop. Use SDDM,
NetworkManager, PipeWire, XDG portals, and Konsole in the live environment.

## Rationale

Plasma is mature, configurable without a maintained fork, and fits gaming and
power-user goals. GNOME is mature but less suitable for the intended defaults;
COSMIC remains an option to revisit after its ecosystem and packaging settle.

Najs will own defaults and system integrations, not fork KWin or Plasma.

## Sources

- https://kde.org/plasma-desktop/
- https://community.kde.org/Plasma/Wayland
- https://wiki.archlinux.org/title/KDE
