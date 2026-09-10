# Najs CLI

## Implemented

- `najs info`: release and CLI version.
- `najs status`: runtime facilities, root filesystem and subvolume, boot manager,
  current generation, and generation prerequisite readiness.
- `najs doctor`: read-only checks for release metadata, manifest validity,
  services, UEFI, generation root, Fastfetch, and Najs Fold assets. Use
  `najs doctor --json` for a machine-readable support report.
- `najs validate`: strict syntax and semantic validation, including duplicate,
  conflict, profile, hostname, locale, desktop, and feature checks.
- `najs diff`: read-only package, enabled/disabled service, feature, profile,
  desktop, locale, and hostname comparison. Backend failures are errors rather
  than being reported as system drift.
- `najs completions <bash|zsh|fish>`: generate shell completion definitions.
  Najs installs these definitions system-wide by default.

## Reserved for verified implementations

`apply`, `install`, `remove`, `upgrade`, `history`, `snapshot`, `rollback`,
`generations`, `switch`, `profile`, and `drivers` will not be exposed
as successful commands until their underlying safety properties are tested.
