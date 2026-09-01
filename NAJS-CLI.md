# Najs CLI

## Implemented

- `najs info`: release and CLI version.
- `najs status`: availability of Najs, Btrfs, pacman, and systemd facilities.
- `najs doctor`: read-only checks for release metadata, manifest validity,
  services, UEFI, generation root, Fastfetch, and Najs Fold assets.
- `najs validate`: strict manifest validation.
- `najs diff`: read-only package, service, and hostname comparison.

## Reserved for verified implementations

`apply`, `install`, `remove`, `upgrade`, `history`, `snapshot`, `rollback`,
`generations`, `switch`, `profile`, and `drivers` will not be exposed
as successful commands until their underlying safety properties are tested.
