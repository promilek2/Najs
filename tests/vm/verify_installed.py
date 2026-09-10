#!/usr/bin/env python3
"""Boot an installed Najs disk and verify it through QEMU Guest Agent."""

from __future__ import annotations

import argparse
import base64
import json
import socket
import subprocess
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--ovmf", required=True, type=Path)
    parser.add_argument("--disk", required=True, type=Path)
    parser.add_argument("--format", choices=("raw", "qcow2"), required=True)
    parser.add_argument(
        "--desktop",
        choices=("plasma", "gnome", "hyprland", "xfce", "cinnamon"),
        default="plasma",
    )
    parser.add_argument("--password")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=300)
    return parser.parse_args()


def monitor_command(path: Path, command: str) -> bytes:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        connection.recv(4096)
        connection.sendall(command.encode("ascii") + b"\n")
        time.sleep(1)
        return connection.recv(16384)


def type_in_guest(path: Path, text: str) -> None:
    key_names = {" ": "spc", "/": "slash", "-": "minus"}
    commands = [f"sendkey {key_names.get(character, character)}" for character in text]
    commands.append("sendkey ret")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        connection.recv(4096)
        connection.sendall(("\n".join(commands) + "\n").encode("ascii"))
        time.sleep(2)
        connection.recv(16384)


def agent_call(path: Path, request: dict[str, object]) -> dict[str, object]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        connection.sendall(json.dumps(request).encode("ascii") + b"\n")
        response = b""
        while b"\n" not in response:
            response += connection.recv(65536)
    value = json.loads(response.splitlines()[0].lstrip(b"\xff"))
    if "error" in value:
        raise RuntimeError(f"guest agent error: {value['error']}")
    return value


def wait_for_agent(path: Path, process: subprocess.Popen[bytes], timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"QEMU exited before guest agent startup: {process.returncode}")
        if path.exists():
            try:
                agent_call(path, {"execute": "guest-ping"})
                return
            except (ConnectionError, OSError, TimeoutError, RuntimeError):
                pass
        time.sleep(2)
    raise TimeoutError("QEMU guest agent did not become available")


def run_health_check(path: Path, desktop: str, timeout: int) -> str:
    display_manager = {
        "plasma": "sddm",
        "gnome": "gdm",
        "hyprland": "sddm",
        "xfce": "lightdm",
        "cinnamon": "lightdm",
    }[desktop]
    desktop_checks = {
        "plasma": (
            'check packages "pacman -Q plasma-meta sddm dolphin konsole lib32-mesa >/dev/null"\n'
            'check desktop-manifest "grep -qx \'environment = \\"plasma\\"\' '
            '/etc/najs/manifest.toml"'
        ),
        "hyprland": (
            'check packages "pacman -Q hyprland kitty mako thunar waybar wofi '
            'xdg-desktop-portal-hyprland lib32-mesa >/dev/null"\n'
            'check desktop-manifest "grep -qx \'environment = \\"hyprland\\"\' '
            '/etc/najs/manifest.toml"\n'
            'check hyprland-config "find /home -path \'*/.config/hypr/hyprland.conf\' '
            '-type f -exec grep -q \'exec-once = waybar\' {} \\;"\n'
            'check waybar-config "find /home -path \'*/.config/waybar/config.jsonc\' '
            '-type f -print -quit | grep -q ."'
        ),
        "gnome": (
            'check packages "pacman -Q gnome-shell gdm nautilus gnome-console '
            'gnome-control-center gnome-software xdg-desktop-portal-gnome '
            'lib32-mesa >/dev/null"\n'
            'check desktop-manifest "grep -qx \'environment = \\"gnome\\"\' '
            '/etc/najs/manifest.toml"'
        ),
        "xfce": (
            'check packages "pacman -Q xfce4-session xfce4-panel xfce4-terminal thunar '
            'lightdm gvfs pavucontrol xdg-desktop-portal-xapp lib32-mesa >/dev/null"\n'
            'check desktop-manifest "grep -qx \'environment = \\"xfce\\"\' '
            '/etc/najs/manifest.toml"'
        ),
        "cinnamon": (
            'check packages "pacman -Q cinnamon nemo gnome-terminal lightdm '
            'xdg-desktop-portal-xapp lib32-mesa >/dev/null"\n'
            'check desktop-manifest "grep -qx \'environment = \\"cinnamon\\"\' '
            '/etc/najs/manifest.toml"'
        ),
    }[desktop]
    script = r'''
set -u
health=ok
check() {
    if eval "$2"; then
        printf '%s: ok\n' "$1"
    else
        printf '%s: failed\n' "$1"
        health=failed
    fi
}
echo NAJS_CALAMARES_BOOT_HEALTH_BEGIN
check os-release "grep -qx ID=najs /etc/os-release"
check hostname "grep -qx najs-vm /etc/hostname"
check btrfs-root "test \"\$(findmnt -n -o FSTYPE /)\" = btrfs"
check btrfs-generation "test \"\$(findmnt -n -o FSROOT /)\" = /roots/initial"
check systemd-boot "bootctl is-installed >/dev/null"
check boot-branding "bootctl list --no-pager | grep -q Najs"
check network "systemctl is-active --quiet NetworkManager.service"
check display-manager "systemctl is-active --quiet @DISPLAY_MANAGER@.service"
check firewall "systemctl is-active --quiet firewalld.service"
@DESKTOP_CHECKS@
check najs-cli "najs validate --manifest /etc/najs/manifest.toml >/dev/null"
check branding "test -r /usr/share/wallpapers/Najs/contents/images/2560x1600.png"
check official-repositories "! grep -REiq --include='*.conf' --include='mirrorlist' 'cachyos' /etc/pacman.conf /etc/pacman.d"
check official-packages "! pacman -Qq | grep -Eiq 'cachyos|linux-cachyos'"
if test "$health" = ok; then
    echo NAJS_CALAMARES_BOOT_HEALTH_OK
else
    echo NAJS_CALAMARES_BOOT_HEALTH_FAILED
fi
'''.replace("@DESKTOP_CHECKS@", desktop_checks).replace(
        "@DISPLAY_MANAGER@", display_manager
    )
    started = agent_call(
        path,
        {
            "execute": "guest-exec",
            "arguments": {
                "path": "/usr/bin/bash",
                "arg": ["-lc", script],
                "capture-output": True,
            },
        },
    )
    pid = started["return"]["pid"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = agent_call(
            path,
            {"execute": "guest-exec-status", "arguments": {"pid": pid}},
        )["return"]
        if status.get("exited"):
            output = base64.b64decode(status.get("out-data", "")).decode(
                "utf-8", errors="replace"
            )
            errors = base64.b64decode(status.get("err-data", "")).decode(
                "utf-8", errors="replace"
            )
            if status.get("exitcode") != 0:
                raise RuntimeError(f"health command failed:\n{output}{errors}")
            return output + errors
        time.sleep(1)
    raise TimeoutError("installed-system health check timed out")


def run_session_check(path: Path, timeout: int) -> str:
    script = r'''
sleep 20
health=ok
echo NAJS_HYPRLAND_SESSION_BEGIN
for process in Hyprland waybar swaybg; do
    if pgrep -x "$process" >/dev/null; then
        printf '%s: active\n' "$process"
    else
        printf '%s: failed\n' "$process"
        health=failed
    fi
done
user="$(find /home -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | head -n 1)"
uid="$(id -u "$user")"
runtime="/run/user/$uid"
signature="$(basename "$(find "$runtime/hypr" -mindepth 1 -maxdepth 1 -type d | head -n 1)")"
errors="$(runuser -u "$user" -- env XDG_RUNTIME_DIR="$runtime" HYPRLAND_INSTANCE_SIGNATURE="$signature" hyprctl configerrors)"
if test -z "$errors"; then
    echo config-errors: none
else
    printf 'config-errors: %s\n' "$errors"
    health=failed
fi
if test "$health" = ok; then
    echo NAJS_HYPRLAND_SESSION_OK
else
    echo NAJS_HYPRLAND_SESSION_FAILED
fi
'''
    started = agent_call(
        path,
        {
            "execute": "guest-exec",
            "arguments": {
                "path": "/usr/bin/bash",
                "arg": ["-lc", script],
                "capture-output": True,
            },
        },
    )
    pid = started["return"]["pid"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = agent_call(
            path,
            {"execute": "guest-exec-status", "arguments": {"pid": pid}},
        )["return"]
        if status.get("exited"):
            return base64.b64decode(status.get("out-data", "")).decode(
                "utf-8", errors="replace"
            )
        time.sleep(1)
    raise TimeoutError("Hyprland session health check timed out")


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    monitor = args.output / "installed-monitor.sock"
    agent = args.output / "installed-agent.sock"
    serial = args.output / "installed-serial.log"
    screenshot = args.output / "installed-boot.ppm"
    report = args.output / "installed-health.log"
    for stale in (monitor, agent, serial, screenshot, report):
        stale.unlink(missing_ok=True)

    command = [
        args.qemu,
        "-enable-kvm",
        "-machine",
        "q35",
        "-cpu",
        "host",
        "-m",
        "4096",
        "-smp",
        "4",
        "-bios",
        str(args.ovmf),
        "-device",
        "virtio-vga",
        "-display",
        "none",
        "-nic",
        "user,model=virtio-net-pci",
        "-drive",
        f"file={args.disk},if=none,id=testdisk,format={args.format},discard=unmap",
        "-device",
        "virtio-blk-pci,drive=testdisk,serial=NAJS_CALAMARES_DISK",
        "-chardev",
        f"socket,path={agent},server=on,wait=off,id=qga0",
        "-device",
        "virtio-serial",
        "-device",
        "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
        "-monitor",
        f"unix:{monitor},server=on,wait=off",
        "-serial",
        f"file:{serial}",
        "-boot",
        "c",
        "-no-reboot",
    ]
    process = subprocess.Popen(command)
    try:
        wait_for_agent(agent, process, args.timeout)
        health = run_health_check(agent, args.desktop, 60)
        if args.desktop == "hyprland" and args.password:
            type_in_guest(monitor, args.password)
            health += run_session_check(agent, 60)
        report.write_text(health, encoding="utf-8")
        response = monitor_command(monitor, f"screendump {screenshot}")
        if b"Error" in response or screenshot.stat().st_size < 10_000:
            raise RuntimeError("QEMU did not produce an installed-system framebuffer")
        print(health, end="")
        if "NAJS_CALAMARES_BOOT_HEALTH_OK" not in health:
            raise RuntimeError(f"installed Najs health check failed; inspect {report}")
        if args.desktop == "hyprland" and args.password:
            if "NAJS_HYPRLAND_SESSION_OK" not in health:
                raise RuntimeError(f"Hyprland session health check failed; inspect {report}")
        print(f"installed framebuffer: {screenshot}")
        print(f"installed health report: {report}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
