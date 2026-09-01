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
