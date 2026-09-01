# Contributing

Run `./najs-dev test` before submitting a change. Rust must pass formatting,
Clippy with warnings denied, and unit tests. Claims about boot, installation, or
rollback require a recorded VM test; a configuration file alone is not proof.

Major architectural changes require an ADR in `docs/adr/`.
