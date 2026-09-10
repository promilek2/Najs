#!/usr/bin/env python3
"""Boot a Najs ISO through OVMF and capture its framebuffer."""

from __future__ import annotations

import argparse
import json
import math
import socket
import subprocess
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--ovmf", required=True, type=Path)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wait", type=int, default=120)
    parser.add_argument("--login-after", type=int, default=0)
    parser.add_argument("--launch-installer-after", type=int, default=0)
    parser.add_argument("--installer-command", default="sudo /usr/local/bin/najs-calamares")
    parser.add_argument("--walk-installer-pages", type=int, default=0)
    parser.add_argument("--installer-keys", default="")
    parser.add_argument("--keep-installer-disk", type=int, default=0)
    return parser.parse_args()


def wait_for_socket(path: Path, process: subprocess.Popen[bytes], timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"QEMU exited before opening its monitor: {process.returncode}")
        if path.exists():
            return
        time.sleep(0.2)
    raise TimeoutError("QEMU monitor did not become available")


def monitor_command(path: Path, command: str) -> bytes:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        connection.recv(4096)
        connection.sendall(command.encode("ascii") + b"\n")
        time.sleep(1)
        return connection.recv(16384)


def type_in_guest(path: Path, text: str, *, submit: bool = True) -> None:
    key_names = {" ": "spc", "/": "slash", "-": "minus"}
    commands = [
        f"sendkey {key_names.get(character, f'shift-{character.lower()}' if character.isupper() else character)}"
        for character in text
    ]
    if submit:
        commands.append("sendkey ret")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        connection.recv(4096)
        connection.sendall(("\n".join(commands) + "\n").encode("ascii"))
        time.sleep(5)
        connection.recv(16384)


def click_in_guest(path: Path, x: int, y: int) -> None:
    position = [
        {"type": "abs", "data": {"axis": "x", "value": round(x / 1280 * 32767)}},
        {"type": "abs", "data": {"axis": "y", "value": round(y / 800 * 32767)}},
    ]
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        stream = connection.makefile("rwb", buffering=0)
        json.loads(stream.readline())
        stream.write(b'{"execute":"qmp_capabilities"}\n')
        capabilities = json.loads(stream.readline())
        if "error" in capabilities:
            raise RuntimeError(f"QMP capabilities failed: {capabilities['error']}")

        for events in (
            position,
            [{"type": "btn", "data": {"down": True, "button": "left"}}],
            [{"type": "btn", "data": {"down": False, "button": "left"}}],
        ):
            request = {"execute": "input-send-event", "arguments": {"events": events}}
            stream.write(json.dumps(request).encode("ascii") + b"\n")
            response = json.loads(stream.readline())
            if "error" in response:
                raise RuntimeError(f"QMP input failed: {response['error']}")
            time.sleep(0.2)
        time.sleep(1)


def wait_for_installer(serial: Path, timeout: int) -> int:
    started = time.monotonic()
    deadline = started + timeout
    failure_markers = ("completion: failed", "Installation failed:", "onInstallationFailed")
    while time.monotonic() < deadline:
        text = serial.read_text(encoding="utf-8", errors="replace") if serial.exists() else ""
        if "completion: succeeded" in text:
            return math.ceil(time.monotonic() - started)
        if any(marker in text for marker in failure_markers):
            raise RuntimeError(f"Calamares reported an installation failure; inspect {serial}")
        time.sleep(2)
    raise TimeoutError(f"Calamares did not finish within {timeout} seconds; inspect {serial}")


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    monitor = args.output / "monitor.sock"
    qmp = args.output / "qmp.sock"
    screenshot = args.output / "boot.ppm"
    installer_screenshot = args.output / "installer.ppm"
    installer_disk = args.output / "installer-disk.raw"
    serial = args.output / "serial.log"
    for stale in (monitor, qmp, screenshot, installer_screenshot, installer_disk, serial):
        stale.unlink(missing_ok=True)
    for stale in args.output.glob("installer-page-*.ppm"):
        stale.unlink()
    for stale in args.output.glob("installer-key-*.ppm"):
        stale.unlink()

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
        "-device",
        "qemu-xhci",
        "-device",
        "usb-tablet",
        "-display",
        "none",
        "-nic",
        "user,model=virtio-net-pci",
        "-monitor",
        f"unix:{monitor},server=on,wait=off",
        "-qmp",
        f"unix:{qmp},server=on,wait=off",
        "-serial",
        f"file:{serial}",
        "-cdrom",
        str(args.iso),
        "-boot",
        "d",
        "-no-reboot",
    ]
    if args.launch_installer_after:
        with installer_disk.open("wb") as disk_file:
            disk_file.truncate(40 * 1024**3)
        command.extend(
            [
                "-drive",
                f"file={installer_disk},if=none,id=installerdisk,format=raw,discard=unmap",
                "-device",
                "virtio-blk-pci,drive=installerdisk,serial=NAJS_INSTALLER_SMOKE_DISK",
                "-fw_cfg",
                "name=opt/najs/calamares-smoke,string=1",
            ]
        )

    process = subprocess.Popen(command)
    try:
        wait_for_socket(monitor, process)
        wait_for_socket(qmp, process)
        if args.login_after:
            time.sleep(args.login_after)
            monitor_command(monitor, "sendkey ret")
        elapsed = args.login_after
        if args.launch_installer_after:
            time.sleep(args.launch_installer_after - elapsed)
            monitor_command(monitor, "sendkey ctrl-alt-t")
            time.sleep(3)
            type_in_guest(monitor, args.installer_command)
            elapsed = args.launch_installer_after + 8
            for page_index in range(args.walk_installer_pages):
                page_screenshot = args.output / f"installer-page-{page_index}.ppm"
                response = monitor_command(monitor, f"screendump {page_screenshot}")
                if b"Error" in response:
                    raise RuntimeError(response.decode("utf-8", errors="replace"))
                if page_index + 1 < args.walk_installer_pages:
                    monitor_command(monitor, "sendkey alt-n")
                    time.sleep(4)
                    elapsed += 5
                elapsed += 1
            for key_index, key_name in enumerate(filter(None, args.installer_keys.split(","))):
                if key_name.startswith("text-submit:"):
                    type_in_guest(monitor, key_name.removeprefix("text-submit:"))
                    delay = 4
                elif key_name.startswith("text:"):
                    type_in_guest(monitor, key_name.removeprefix("text:"), submit=False)
                    delay = 4
                elif key_name.startswith("click:"):
                    _, x, y = key_name.split(":")
                    click_in_guest(qmp, int(x), int(y))
                    delay = 2
                elif key_name.startswith("wait:"):
                    delay = int(key_name.removeprefix("wait:"))
                elif key_name.startswith("wait-install:"):
                    elapsed += wait_for_installer(
                        serial, int(key_name.removeprefix("wait-install:"))
                    )
                    delay = 0
                else:
                    monitor_command(monitor, f"sendkey {key_name}")
                    delay = 4
                time.sleep(delay)
                elapsed += delay + 1
                key_screenshot = args.output / f"installer-key-{key_index}.ppm"
                response = monitor_command(monitor, f"screendump {key_screenshot}")
                if b"Error" in response:
                    raise RuntimeError(response.decode("utf-8", errors="replace"))
                elapsed += 1
        time.sleep(max(0, args.wait - elapsed))
        if process.poll() is not None:
            raise RuntimeError(f"QEMU exited during boot: {process.returncode}")
        response = monitor_command(monitor, f"screendump {screenshot}")
        if b"Error" in response:
            raise RuntimeError(response.decode("utf-8", errors="replace"))
        if not screenshot.exists() or screenshot.stat().st_size < 10_000:
            raise RuntimeError("QEMU did not produce a usable framebuffer capture")
        if args.launch_installer_after:
            screenshot.replace(installer_screenshot)
            screenshot = installer_screenshot
        serial_text = serial.read_text(encoding="utf-8", errors="replace")
        required_markers = (
            "NAJS_VM_HEALTH_OK",
            "Session started true",
            "Starting Wayland user session",
            "NetworkManager: active",
            "network: connected",
            "najs-cli: ok",
            "najs-status: ok",
            "najs-completions: ok",
            "najs-installer: ok",
            "cocky-installer: ok",
            "calamares-installer: ok",
            "branding: ok",
            "fastfetch: ok",
            "najs-welcome: ok",
            "desktop-branding: ok",
            "najs-doctor: ok",
            "plasma-session: active",
            "audio-session: active",
        )
        missing = [marker for marker in required_markers if marker not in serial_text]
        if missing:
            raise RuntimeError(f"VM health markers missing: {', '.join(missing)}")
        print(f"framebuffer: {screenshot}")
        print(f"serial log: {serial}")
        print("health: UEFI, Najs branding, network, audio, CLI, and Plasma Wayland passed")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if not args.keep_installer_disk:
            installer_disk.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
