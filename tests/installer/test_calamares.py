from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CALAMARES = ROOT / "installer/calamares/etc/calamares"


class CalamaresConfigTests(unittest.TestCase):
    def test_advanced_installer_sequence_is_complete(self) -> None:
        settings = (CALAMARES / "settings.conf").read_text(encoding="utf-8")
        for step in (
            "welcome",
            "locale",
            "keyboard",
            "packagechooser@bootloader",
            "partition",
            "packagechooser@desktop",
            "packagechooser@kernel",
            "packagechooser@graphics",
            "netinstall",
            "users",
            "summary",
        ):
            self.assertIn(f"- {step}", settings)
        self.assertIn("branding: najs", settings)
        self.assertIn("prompt-install: true", settings)

    def test_supported_desktops_kernels_and_graphics_are_exposed(self) -> None:
        modules = CALAMARES / "modules"
        desktop = (modules / "packagechooser_desktop.conf").read_text(encoding="utf-8")
        kernel = (modules / "packagechooser_kernel.conf").read_text(encoding="utf-8")
        graphics = (modules / "packagechooser_graphics.conf").read_text(encoding="utf-8")
        for value in ("KDE Plasma", "GNOME", "Hyprland", "Xfce", "Cinnamon"):
            self.assertIn(f"name: {value}", desktop)
        for value in ("Linux Stable", "Linux LTS", "Linux Zen", "Linux Hardened"):
            self.assertIn(f"name: {value}", kernel)
        for value in ("AMD Radeon", "Intel Graphics", "NVIDIA Turing or newer", "Virtual machine"):
            self.assertIn(f"name: {value}", graphics)

    def test_hyprland_installs_a_complete_session(self) -> None:
        desktop = (CALAMARES / "modules/packagechooser_desktop.conf").read_text(
            encoding="utf-8"
        )
        for package in (
            "brightnessctl",
            "kitty",
            "mako",
            "nwg-displays",
            "polkit-gnome",
            "sddm",
            "thunar",
            "waybar",
            "wofi",
            "xdg-desktop-portal-hyprland",
        ):
            self.assertIn(package, desktop)
        hyprland = (ROOT / "branding/hyprland/hyprland.conf").read_text(encoding="utf-8")
        self.assertIn("exec-once = waybar", hyprland)
        self.assertIn("$terminal = kitty", hyprland)
        self.assertIn("$menu = wofi --show drun", hyprland)

    def test_every_calamares_desktop_has_essential_gui_packages(self) -> None:
        desktop = (CALAMARES / "modules/packagechooser_desktop.conf").read_text(
            encoding="utf-8"
        )
        sections = {
            name: desktop.split(f"- id: {name}", 1)[1].split("  - id:", 1)[0]
            for name in ("kde", "gnome", "hyprland", "xfce", "cinnamon")
        }
        required = {
            "kde": ("plasma-meta", "sddm", "dolphin", "konsole"),
            "gnome": ("gnome", "gdm", "gnome-disk-utility"),
            "hyprland": ("hyprland", "sddm", "kitty", "thunar", "nwg-displays"),
            "xfce": ("xfce4", "lightdm", "gvfs", "pavucontrol", "xdg-desktop-portal-xapp"),
            "cinnamon": ("cinnamon", "lightdm", "gnome-terminal", "xdg-desktop-portal-xapp"),
        }
        for name, packages in required.items():
            with self.subTest(desktop=name):
                for package in packages:
                    self.assertIn(package, sections[name])

    def test_storage_defaults_are_safe_and_najs_native(self) -> None:
        partition = (CALAMARES / "modules/partition.conf").read_text(encoding="utf-8")
        mount = (CALAMARES / "modules/mount.conf").read_text(encoding="utf-8")
        self.assertIn("initialPartitioningChoice: none", partition)
        self.assertIn("luksGeneration: luks2", partition)
        self.assertIn("enableLuksAutomatedPartitioning: true", partition)
        self.assertEqual(partition.count("defaultFileSystemType: btrfs"), 3)
        self.assertIn("subvolume: /roots/initial", mount)
        self.assertIn("subvolume: /snapshots", mount)

    def test_welcome_page_does_not_override_the_english_ui_from_geoip(self) -> None:
        welcome = (CALAMARES / "modules/welcome.conf").read_text(encoding="utf-8")
        self.assertIn("style: none", welcome)

    def test_live_desktop_launcher_uses_cocky_installer(self) -> None:
        launcher = (ROOT / "installer/najs-installer.desktop").read_text(encoding="utf-8")
        wrapper = (ROOT / "installer/najs-calamares").read_text(encoding="utf-8")
        installer = (ROOT / "installer/najs-install").read_text(encoding="utf-8")
        self.assertIn("Name=Cocky Installer", launcher)
        self.assertIn("Exec=konsole -e sudo /usr/local/bin/najs-install", launcher)
        self.assertIn('"Cocky Installer"', installer)
        self.assertNotIn("ERASE {disk}", installer)
        self.assertNotIn('"Encryption password"', installer)
        self.assertIn('"encryption_password": user_password if encrypted else None', installer)
        self.assertIn("opt/najs/calamares-smoke/raw", wrapper)
        self.assertIn("tee /dev/ttyS0", wrapper)

    def test_hyprland_has_a_graphical_settings_hub(self) -> None:
        settings = (ROOT / "branding/najs-hyprland-settings").read_text(encoding="utf-8")
        for command in ("nwg-displays", "nm-connection-editor", "pavucontrol", "nwg-look"):
            self.assertIn(command, settings)

    def test_fastfetch_uses_the_six_eyes_character_art(self) -> None:
        config = (ROOT / "branding/fastfetch-config.jsonc").read_text(encoding="utf-8")
        build = (ROOT / "tools/build-iso-in-container").read_text(encoding="utf-8")
        logo = (ROOT / "branding/fastfetch-logo.txt").read_text(encoding="utf-8")
        self.assertIn('"type": "file"', config)
        self.assertIn('/usr/share/najs/fastfetch/logo.txt', config)
        self.assertIn('branding/fastfetch-logo.txt', build)
        self.assertGreaterEqual(logo.count("@"), 6)

    def test_external_installer_binaries_remain_executable_in_archiso(self) -> None:
        profile = (ROOT / "iso/archiso/profiledef.sh").read_text(encoding="utf-8")
        self.assertIn('["/usr/bin/calamares"]="0:0:755"', profile)
        self.assertIn('["/usr/bin/ckbcomp"]="0:0:755"', profile)

    def test_calamares_abi_compatibility_library_is_pinned_and_live_only(self) -> None:
        build = (ROOT / "tools/build-iso-in-container").read_text(encoding="utf-8")
        self.assertIn("boost-libs-1.91.0-2-x86_64.pkg.tar.zst", build)
        self.assertIn(
            "62cfd278b0260bd2ce5c93f6ab4669d2eefe840eab19e2c3854762f295924655",
            build,
        )
        for library in ("container", "graph", "python314"):
            self.assertIn(f"usr/lib/libboost_{library}.so.1.91.0", build)
        self.assertNotIn("boost-libs", (ROOT / "installer/catalog.json").read_text(encoding="utf-8"))

    def test_pacstrap_wrapper_excludes_distribution_specific_target_packages(self) -> None:
        wrapper = (ROOT / "installer/calamares/scripts/pacstrap_calamares").read_text(
            encoding="utf-8"
        )
        for package in (
            "cachyos-grub-theme",
            "grub-btrfs-support",
            "grub-hook",
            "linux-cachyos*",
            "systemd-boot-manager",
        ):
            self.assertIn(package, wrapper)
        self.assertIn('exec /usr/local/lib/najs/pacstrap_calamares "${filtered[@]}"', wrapper)

    def test_live_pacman_configuration_enables_official_multilib_for_target(self) -> None:
        live_pacman = (ROOT / "iso/archiso/airootfs/etc/pacman.conf").read_text(
            encoding="utf-8"
        )
        build_pacman = (ROOT / "iso/archiso/pacman.conf").read_text(encoding="utf-8")
        self.assertEqual(live_pacman, build_pacman)
        self.assertIn("[multilib]", live_pacman)

    def test_branding_contains_no_cachyos_identity(self) -> None:
        for path in CALAMARES.rglob("*"):
            if path.is_file():
                self.assertNotIn("cachyos", path.read_text(encoding="utf-8").lower(), path)


if __name__ == "__main__":
    unittest.main()
