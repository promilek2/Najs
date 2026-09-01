#!/usr/bin/env bash
# shellcheck disable=SC2034 # mkarchiso sources and consumes these variables.

iso_name="najs"
iso_label="NAJS_$(date --date="@${SOURCE_DATE_EPOCH:-0}" +%Y%m)"
iso_publisher="Najs Project <https://github.com/najs-os/najs>"
iso_application="Najs Live"
iso_version="${NAJS_VERSION:-0.1.0-dev}"
install_dir="najs"
buildmodes=("iso")
bootmodes=(
  "bios.syslinux"
  "uefi.systemd-boot"
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=("-comp" "zstd" "-Xcompression-level" "15" -b "1M")
bootstrap_tarball_compression=("zstd" "-c" "-T0" "--auto-threads=logical" "-19")
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/sudoers.d/10-najs-live"]="0:0:440"
  ["/usr/local/lib/najs/create-live-user"]="0:0:755"
  ["/usr/local/lib/najs/apply-desktop-branding"]="0:0:755"
  ["/usr/local/lib/najs/report-live-health"]="0:0:755"
  ["/usr/local/lib/najs/run-vm-install"]="0:0:755"
  ["/usr/local/bin/najs"]="0:0:755"
  ["/usr/local/bin/najs-install"]="0:0:755"
  ["/usr/local/bin/najs-welcome-gui"]="0:0:755"
)
