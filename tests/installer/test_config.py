from __future__ import annotations

import json
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "installer/najs-install"
BASE_CONFIG = ROOT / "installer/archinstall/config.json"
CATALOG = ROOT / "installer/catalog.json"


class InstallerConfigTests(unittest.TestCase):
    def generate(self, *arguments: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "config.json"
            subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER),
                    "--generate-config",
                    str(output),
                    "--base-config",
                    str(BASE_CONFIG),
                    "--catalog",
                    str(CATALOG),
                    *arguments,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(output.read_text(encoding="utf-8"))

    def test_hostname_matches_cli_validation_rules(self) -> None:
        hostname = runpy.run_path(str(INSTALLER))["HOSTNAME"]
        for valid in ("najs", "gaming-pc", "najs42"):
            self.assertIsNotNone(hostname.fullmatch(valid))
        for invalid in ("", "-najs", "najs-", "najs.local", "najs pc"):
            self.assertIsNone(hostname.fullmatch(invalid))

    def test_every_desktop_maps_to_archinstall(self) -> None:
        expected = {
            "kde": ("KDE Plasma", "sddm", "plasma", "wayland"),
            "gnome": ("GNOME", "gdm", "gnome", "wayland"),
            "hyprland": ("Hyprland", "sddm", "hyprland", "wayland"),
            "xfce": ("Xfce4", "lightdm-gtk-greeter", "xfce", "xorg"),
            "cinnamon": ("Cinnamon", "lightdm-gtk-greeter", "cinnamon", "xorg"),
        }
        for desktop, values in expected.items():
            with self.subTest(desktop=desktop):
                config = self.generate("--desktop", desktop)
                profile = config["profile_config"]
                selection = config["najs"]
                self.assertEqual(profile["profile"]["details"], [values[0]])
                self.assertEqual(profile["greeter"], values[1])
                self.assertEqual(selection["environment"], values[2])
                self.assertEqual(selection["session"], values[3])

    def test_every_desktop_manifest_contains_a_complete_graphical_session(self) -> None:
        required = {
            "kde": {"plasma-meta", "sddm", "dolphin", "konsole"},
            "gnome": {"gnome", "gdm", "gnome-disk-utility"},
            "hyprland": {"hyprland", "sddm", "kitty", "thunar", "nwg-displays"},
            "xfce": {"xfce4", "lightdm", "gvfs", "pavucontrol"},
            "cinnamon": {"cinnamon", "lightdm", "gnome-terminal"},
        }
        for desktop, expected_packages in required.items():
            with self.subTest(desktop=desktop):
                packages = set(self.generate("--desktop", desktop)["packages"])
                self.assertTrue(expected_packages <= packages)
                self.assertIn("gnome-software", packages)

    def test_gaming_enables_complete_runtime_and_multilib(self) -> None:
        config = self.generate(
            "--desktop",
            "kde",
            "--use-case",
            "gaming",
            "--gpu",
            "amd",
        )
        packages = set(config["packages"])
        for package in (
            "steam",
            "lutris",
            "wine",
            "winetricks",
            "gamemode",
            "gamescope",
            "mangohud",
            "lib32-vulkan-radeon",
            "obs-studio",
            "protontricks",
            "wine-gecko",
            "wine-mono",
        ):
            self.assertIn(package, packages)
        self.assertIn("multilib", config["mirror_config"]["optional_repositories"])

    def test_hyprland_profile_is_usable_without_manual_configuration(self) -> None:
        config = self.generate("--desktop", "hyprland")
        packages = set(config["packages"])
        for package in (
            "brightnessctl",
            "kitty",
            "mako",
            "polkit-gnome",
            "sddm",
            "thunar",
            "waybar",
            "wofi",
            "xdg-desktop-portal-hyprland",
        ):
            self.assertIn(package, packages)

    def test_hyprland_configuration_is_copied_to_existing_users(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory)
            skel = target / "etc/skel/.config"
            (skel / "hypr").mkdir(parents=True)
            (skel / "waybar").mkdir()
            (skel / "hypr/hyprland.conf").write_text("$mod = SUPER\n", encoding="utf-8")
            (skel / "waybar/config.jsonc").write_text("{}\n", encoding="utf-8")
            home = target / "home/tester"
            home.mkdir(parents=True)

            installer["configure_hyprland_users"](target)

            self.assertEqual(
                (home / ".config/hypr/hyprland.conf").read_text(encoding="utf-8"),
                "$mod = SUPER\n",
            )
            self.assertEqual(
                (home / ".config/waybar/config.jsonc").read_text(encoding="utf-8"),
                "{}\n",
            )

    def test_mounted_descendants_make_a_disk_ineligible(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        device = {
            "mountpoints": [None],
            "children": [
                {
                    "mountpoints": [None],
                    "children": [{"mountpoints": ["/run/archiso/bootmnt"]}],
                }
            ],
        }
        self.assertEqual(installer["mounted_paths"](device), ["/run/archiso/bootmnt"])

    def test_every_desktop_requires_its_display_manager_and_session(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for desktop, (display_manager, sessions) in installer[
                "DESKTOP_REQUIREMENTS"
            ].items():
                with self.subTest(desktop=desktop):
                    target = root / desktop
                    unit = target / "usr/lib/systemd/system" / display_manager
                    session = target / sessions[0]
                    unit.parent.mkdir(parents=True)
                    session.parent.mkdir(parents=True)
                    unit.touch()
                    session.touch()
                    self.assertEqual(
                        installer["validate_desktop_target"](target, desktop),
                        display_manager,
                    )

            with self.assertRaisesRegex(RuntimeError, "unsupported installed desktop"):
                installer["validate_desktop_target"](root, "unknown")

    def test_multilib_is_available_for_custom_packages(self) -> None:
        config = self.generate("--use-case", "minimal", "--extra-packages", "steam")
        self.assertIn("multilib", config["mirror_config"]["optional_repositories"])

    def test_everything_selects_every_application_group(self) -> None:
        config = self.generate("--use-case", "everything")
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(set(config["najs"]["bundles"]), set(catalog["bundles"]))
        self.assertIn("libvirtd", config["services"])
        self.assertIn("blender", config["packages"])
        self.assertIn("code", config["packages"])

    def test_custom_packages_are_preserved(self) -> None:
        config = self.generate("--extra-packages", "htop,neovim")
        self.assertIn("htop", config["packages"])
        self.assertIn("neovim", config["packages"])
        self.assertEqual(config["najs"]["extra_packages"], ["htop", "neovim"])

    def test_complete_silent_btrfs_encryption_config(self) -> None:
        disk_size = 80 * 1024**3
        config = self.generate(
            "--disk",
            "/dev/vda",
            "--disk-size",
            str(disk_size),
            "--filesystem",
            "btrfs",
            "--encrypt",
            "--kernel",
            "linux-lts",
            "--locale",
            "pl_PL",
            "--keyboard",
            "pl",
            "--timezone",
            "Europe/Warsaw",
        )
        self.assertTrue(config["silent"])
        self.assertEqual(config["kernels"], ["linux-lts"])
        self.assertEqual(config["locale_config"]["sys_lang"], "pl_PL")
        self.assertEqual(config["timezone"], "Europe/Warsaw")

        disk = config["disk_config"]
        self.assertEqual(disk["config_type"], "default_layout")
        modification = disk["device_modifications"][0]
        self.assertEqual(modification["device"], "/dev/vda")
        self.assertTrue(modification["wipe"])
        boot, root = modification["partitions"]
        self.assertEqual(boot["mountpoint"], "/boot")
        self.assertEqual(boot["flags"], ["boot", "esp"])
        self.assertEqual(root["fs_type"], "btrfs")
        self.assertEqual(root["mountpoint"], None)
        self.assertEqual(root["mount_options"], ["compress=zstd"])
        self.assertEqual(
            {entry["mountpoint"] for entry in root["btrfs"]},
            {"/", "/home", "/var/log", "/var/cache", "/var/tmp", "/snapshots"},
        )
        self.assertEqual(root["btrfs"][0]["name"], "roots/initial")
        self.assertEqual(disk["disk_encryption"]["partitions"], [root["obj_id"]])
        self.assertNotIn("encryption_password", config)

    def test_ext4_and_xfs_use_a_plain_root_mount(self) -> None:
        for filesystem in ("ext4", "xfs"):
            with self.subTest(filesystem=filesystem):
                config = self.generate(
                    "--disk",
                    "/dev/vda",
                    "--disk-size",
                    str(40 * 1024**3),
                    "--filesystem",
                    filesystem,
                    "--bootloader",
                    "Grub",
                    "--no-swap",
                )
                root = config["disk_config"]["device_modifications"][0]["partitions"][1]
                self.assertEqual(root["mountpoint"], "/")
                self.assertEqual(root["btrfs"], [])
                self.assertEqual(config["bootloader_config"]["bootloader"], "Grub")
                self.assertFalse(config["bootloader_config"]["uki"])
                self.assertFalse(config["swap"]["enabled"])

    def test_credentials_are_written_for_root_only(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "credentials.json"
            path.write_text("old", encoding="utf-8")
            path.chmod(0o644)
            installer["write_credentials"](path, {"users": []})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_installation_password_is_entered_once_with_four_character_minimum(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        password_dialog = mock.Mock(side_effect=["abc", "abcd"])
        input_error = mock.Mock()
        with mock.patch.dict(
            installer["prompt_password"].__globals__,
            {"run_dialog": password_dialog, "show_error": input_error},
        ):
            self.assertEqual(installer["prompt_password"]("Password", "Enter it"), "abcd")
        self.assertEqual(password_dialog.call_count, 2)
        input_error.assert_called_once_with("The password must contain at least 4 characters.")

    def test_installation_progress_reports_backend_stages(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        progress = mock.Mock()
        progress.stdin = mock.Mock()
        backend = mock.Mock()
        backend.stdout = mock.Mock()
        backend.stdout.fileno.return_value = 42
        backend.poll.return_value = 0
        backend.wait.return_value = 0
        output = [
            b"[1/3] Preparing package keys...\n",
            b"[2/3] Installing Najs...\n",
            b"[3/3] Applying the Najs platform layer...\n",
            b"Installation completed.\n",
            b"",
            b"",
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            log = Path(temporary_directory) / "install.log"
            globals_ = installer["install_with_progress"].__globals__
            with (
                mock.patch.dict(globals_, {"INSTALL_LOG": log}),
                mock.patch.object(
                    globals_["subprocess"], "Popen", side_effect=[progress, backend]
                ),
                mock.patch.object(
                    globals_["select"],
                    "select",
                    return_value=([backend.stdout], [], []),
                ),
                mock.patch.object(globals_["os"], "read", side_effect=output),
            ):
                installer["install_with_progress"](
                    Path("config.json"), Path("credentials.json"), Path("/mnt")
                )

            updates = "".join(call.args[0] for call in progress.stdin.write.call_args_list)
            for percentage in ("5", "15", "90", "100"):
                self.assertIn(f"\n{percentage}\n", updates)
            self.assertEqual(log.read_bytes(), b"".join(output[:-2]))

    def test_systemd_boot_entries_are_rebranded_after_installation(self) -> None:
        installer = runpy.run_path(str(INSTALLER))
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory)
            entries = target / "boot/loader/entries"
            entries.mkdir(parents=True)
            entry = entries / "linux.conf"
            entry.write_text(
                "title   Arch Linux\nlinux   /vmlinuz-linux\noptions root=UUID=test\n",
                encoding="utf-8",
            )
            installer["brand_systemd_boot_entries"](target)
            self.assertEqual(
                entry.read_text(encoding="utf-8"),
                "title   Najs\nlinux   /vmlinuz-linux\noptions root=UUID=test\n",
            )


if __name__ == "__main__":
    unittest.main()
