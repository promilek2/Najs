# Najs Manifest v1

The manifest is strict TOML. Unknown keys and unsupported schema versions are
errors so configuration mistakes cannot silently disappear.

```toml
version = 1

[system]
hostname = "najs-pc"
locale = "pl_PL.UTF-8"

[desktop]
environment = "plasma"
session = "wayland"

[profiles]
enabled = ["development"]

[packages]
install = ["firefox", "git"]
remove = []

[services]
enable = ["NetworkManager.service"]
disable = []
```

The default path is `/etc/najs/manifest.toml`. `najs validate` parses and checks
the file. `najs diff` compares its managed subset with the running system and is
read-only. `najs apply` is intentionally unavailable until isolated generation
composition exists.

Validation rejects duplicate entries, package install/remove conflicts, service
enable/disable conflicts, unknown profiles, malformed hostnames or locales, and
feature settings that contradict explicit service operations. This prevents a
manifest from describing two incompatible outcomes for the same resource.

Supported desktop environments are `plasma`, `gnome`, `hyprland`, `xfce`, and
`cinnamon`. Supported session types are `wayland` and `xorg`. The installer
records all selected application-group profiles and resolved packages in this
manifest.

Supported profiles are `desktop`, `office`, `media`, `gaming`, `creator`,
`development`, `communication`, and `virtualization`.
