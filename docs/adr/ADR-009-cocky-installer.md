# ADR-009: Cocky Installer as the primary frontend

- Status: accepted
- Date: 2026-09-06

## Decision

Use the existing Najs dialog wizard under the visible name **Cocky Installer**
as the primary live-desktop installer. Keep its established terminal appearance
and keyboard workflow while retaining the newer disk validation, silent
Archinstall backend, Btrfs layout, encryption, desktop selection, package
catalog, and target provisioning.

Keep the pinned Calamares frontend installed in the live image as an optional
advanced path for manual partitioning and F2FS. Both frontends continue to share
the Najs finalization code.

## Consequences

The default path is smaller in scope and easier to validate end to end. It only
offers dedicated whole-disk installation and refuses mounted targets. The user
enters one password once; when LUKS is selected, that password is shared by the
account and disk unlock. Calamares remains available from a terminal when its
broader partitioning UI is required.

Every advertised desktop must provide a display manager, session file, terminal,
file manager, settings path, network and audio controls, policy agent, and an
appropriate desktop portal. Finalization fails instead of silently accepting a
missing graphical session.
