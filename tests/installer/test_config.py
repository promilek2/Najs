from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
