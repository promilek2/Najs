# ADR-002: Btrfs deployment roots

- Status: accepted for the installation prototype
- Date: 2026-08-31

## Decision

Use a flat Btrfs layout with `roots/<generation-id>` for bootable system roots.
Use separate persistent subvolumes for `home`, `var-log`, `var-cache`, `var-tmp`,
and explicitly reviewed application data. Keep package databases in each root.

Do not exclude all of `/var`: doing so would separate pacman state from `/usr`
and make rollback inconsistent. Nested subvolumes are not recursively included
in Btrfs snapshots, so every persistent path needs an explicit policy.

Snapper may provide checkpoints and retention metadata but will not coordinate
boot rollback. Avoid qgroups in v1 due to their cost with frequent snapshots.

## Sources

- https://btrfs.readthedocs.io/en/latest/Subvolumes.html
- https://btrfs.readthedocs.io/en/latest/btrfs-quota.html
- https://snapper.io/manpages/snapper.html
