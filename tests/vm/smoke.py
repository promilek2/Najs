#!/usr/bin/env python3
"""Boot a Najs ISO through OVMF and capture its framebuffer."""

from __future__ import annotations

import argparse
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


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    monitor = args.output / "monitor.sock"
    screenshot = args.output / "boot.ppm"
    serial = args.output / "serial.log"
    for stale in (monitor, screenshot, serial):
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
        "-monitor",
        f"unix:{monitor},server=on,wait=off",
        "-serial",
        f"file:{serial}",
        "-cdrom",
        str(args.iso),
        "-boot",
        "d",
        "-no-reboot",
    ]

    process = subprocess.Popen(command)
    try:
        wait_for_socket(monitor, process)
        if args.login_after:
            time.sleep(args.login_after)
            monitor_command(monitor, "sendkey ret")
        time.sleep(args.wait - args.login_after)
        if process.poll() is not None:
            raise RuntimeError(f"QEMU exited during boot: {process.returncode}")
        response = monitor_command(monitor, f"screendump {screenshot}")
        if b"Error" in response:
            raise RuntimeError(response.decode("utf-8", errors="replace"))
        if not screenshot.exists() or screenshot.stat().st_size < 10_000:
            raise RuntimeError("QEMU did not produce a usable framebuffer capture")
        serial_text = serial.read_text(encoding="utf-8", errors="replace")
        required_markers = (
            "NAJS_VM_HEALTH_OK",
            "Session started true",
            "Starting Wayland user session",
            "NetworkManager: active",
            "network: connected",
            "najs-cli: ok",
            "najs-installer: ok",
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


if __name__ == "__main__":
    main()
