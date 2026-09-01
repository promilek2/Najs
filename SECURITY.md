# Security

Najs is pre-alpha and must not be used as a trusted production system.

Report vulnerabilities privately to the future project security contact; do not
include credentials or private keys in an issue. No signing keys belong in this
repository. Package signatures remain required, telemetry is absent, and future
crash reporting must be explicit opt-in.

Privileged build operations run only inside a disposable build container. The
runtime transaction service will use a narrow polkit API rather than making the
entire desktop CLI setuid or permanently privileged.
