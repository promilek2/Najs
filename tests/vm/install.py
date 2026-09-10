#!/usr/bin/env python3
"""Install Najs to an isolated QCOW2 disk and verify its first boot."""

from __future__ import annotations

import argparse
import json
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--qemu-img", required=True)
    parser.add_argument("--openssl", required=True)
    parser.add_argument("--ovmf", required=True, type=Path)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def password_hash(openssl: str) -> str:
    ephemeral_password = secrets.token_urlsafe(32)
    result = subprocess.run(
        [openssl, "passwd", "-6", ephemeral_password],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def write_inputs(output: Path, openssl: str) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[2]
    installer = root / "installer/najs-install"
    config_path = output / "config.json"
    subprocess.run(
        [
            sys.executable,
            str(installer),
            "--generate-config",
            str(config_path),
            "--base-config",
            str(root / "installer/archinstall/config.json"),
            "--catalog",
            str(root / "installer/catalog.json"),
            "--desktop",
            "kde",
            "--use-case",
            "standard",
            "--gpu",
            "auto",
            "--hostname",
            "najs-vm",
            "--disk",
            "/dev/vda",
            "--disk-size",
            str(40 * 1024**3),
            "--sector-size",
            "512",
            "--filesystem",
            "btrfs",
        ],
        check=True,
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    hashed_password = password_hash(openssl)
    credentials = {
        "root_enc_password": hashed_password,
        "users": [
            {
                "username": "najs-test",
                "enc_password": hashed_password,
                "sudo": True,
            }
        ],
    }
    credentials_path = output / "credentials.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    credentials_path.write_text(json.dumps(credentials), encoding="utf-8")
    credentials_path.chmod(0o600)
    return config_path, credentials_path


def monitor_command(path: Path, command: str) -> bytes:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(str(path))
        connection.recv(4096)
        connection.sendall(command.encode("ascii") + b"\n")
        time.sleep(1)
        return connection.recv(16384)


def run_until_marker(
    command: list[str],
    serial: Path,
    monitor: Path,
    marker: str,
    failure_marker: str,
    timeout: int,
    screenshot: Path | None = None,
) -> None:
    serial.unlink(missing_ok=True)
    monitor.unlink(missing_ok=True)
    if screenshot:
        screenshot.unlink(missing_ok=True)
    process = subprocess.Popen(command)
    deadline = time.monotonic() + timeout
    found = False
    try:
        while time.monotonic() < deadline:
            text = serial.read_text(encoding="utf-8", errors="replace") if serial.exists() else ""
            if failure_marker in text:
                raise RuntimeError(f"guest reported failure; inspect {serial}")
            if marker in text:
                found = True
                if screenshot and monitor.exists():
                    monitor_command(monitor, f"screendump {screenshot}")
                break
            if process.poll() is not None:
                raise RuntimeError(
                    f"QEMU exited with {process.returncode} before {marker}; inspect {serial}"
                )
            time.sleep(2)
        if not found:
            raise TimeoutError(f"timed out waiting for {marker}; inspect {serial}")
        try:
            process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def qemu_base(args: argparse.Namespace, disk: Path, serial: Path, monitor: Path) -> list[str]:
    return [
        args.qemu,
        "-enable-kvm",
        "-machine",
        "q35",
        "-cpu",
        "host",
        "-m",
        "6144",
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
        f"file={disk},if=none,id=testdisk,format=qcow2,discard=unmap",
        "-device",
        "virtio-blk-pci,drive=testdisk,serial=NAJS_TEST_DISK",
        "-serial",
        f"file:{serial}",
        "-monitor",
        f"unix:{monitor},server=on,wait=off",
        "-no-reboot",
    ]


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    disk = args.output / "najs-installed.qcow2"
    disk.unlink(missing_ok=True)
    subprocess.run([args.qemu_img, "create", "-f", "qcow2", str(disk), "40G"], check=True)
    config, credentials = write_inputs(args.output, args.openssl)

    install_serial = args.output / "install-serial.log"
    install_monitor = args.output / "install-monitor.sock"
    install_command = qemu_base(args, disk, install_serial, install_monitor) + [
        "-cdrom",
        str(args.iso),
        "-boot",
        "d",
        "-fw_cfg",
        f"name=opt/najs/install-config,file={config}",
        "-fw_cfg",
        f"name=opt/najs/install-creds,file={credentials}",
    ]
    print("stage 1: installing to isolated QCOW2", flush=True)
    run_until_marker(
        install_command,
        install_serial,
        install_monitor,
        "NAJS_VM_INSTALL_OK",
        "NAJS_VM_INSTALL_FAILED",
        2400,
    )

    boot_serial = args.output / "boot-serial.log"
    boot_monitor = args.output / "boot-monitor.sock"
    screenshot = args.output / "installed.ppm"
    boot_command = qemu_base(args, disk, boot_serial, boot_monitor) + ["-boot", "c"]
    print("stage 2: booting installed Najs", flush=True)
    run_until_marker(
        boot_command,
        boot_serial,
        boot_monitor,
        "NAJS_INSTALLED_HEALTH_OK",
        "NAJS_INSTALLED_HEALTH_FAILED",
        300,
        screenshot,
    )
    print(f"installed disk: {disk}")
    print(f"installed framebuffer: {screenshot}")
    print("installation health: Najs boot branding, Btrfs, Fastfetch, network, CLI, and Plasma passed")


if __name__ == "__main__":
    main()
