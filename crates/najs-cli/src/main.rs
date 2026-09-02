use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use anyhow::{Context, Result, bail};
use clap::{Parser, Subcommand};
use serde::Deserialize;

const DEFAULT_MANIFEST: &str = "/etc/najs/manifest.toml";

#[derive(Debug, Parser)]
#[command(name = "najs", version, about = "Manage a Najs system")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Subcommand)]
enum Commands {
    /// Show release and runtime information.
    Info,
    /// Show whether core Najs facilities are available.
    Status,
    /// Diagnose the running Najs platform without changing it.
    Doctor,
    /// Validate a system manifest without changing the system.
    Validate {
        #[arg(short, long, default_value = DEFAULT_MANIFEST)]
        manifest: PathBuf,
    },
    /// Compare a manifest with the running system without changing it.
    Diff {
        #[arg(short, long, default_value = DEFAULT_MANIFEST)]
        manifest: PathBuf,
    },
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    version: u32,
    #[serde(default)]
    system: System,
    #[serde(default)]
    desktop: Desktop,
    #[serde(default)]
    features: Features,
    #[serde(default)]
    profiles: Profiles,
    #[serde(default)]
    packages: Packages,
    #[serde(default)]
    services: Services,
}

#[derive(Debug, Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct System {
    hostname: Option<String>,
    locale: Option<String>,
}

#[derive(Debug, Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct Desktop {
    environment: Option<String>,
    session: Option<String>,
}

#[derive(Debug, Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct Features {
    bluetooth: Option<bool>,
    printing: Option<bool>,
}

#[derive(Debug, Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct Profiles {
    enabled: Vec<String>,
}

#[derive(Debug, Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct Packages {
    install: Vec<String>,
    remove: Vec<String>,
}

#[derive(Debug, Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct Services {
    enable: Vec<String>,
    disable: Vec<String>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Info => info(),
        Commands::Status => status(),
        Commands::Doctor => doctor(),
        Commands::Validate { manifest } => {
            let manifest = load_manifest(&manifest)?;
            validate_manifest(&manifest)?;
            println!("manifest is valid (schema version {})", manifest.version);
            Ok(())
        }
        Commands::Diff { manifest } => diff(&manifest),
    }
}

fn info() -> Result<()> {
    println!("Najs CLI {}", env!("CARGO_PKG_VERSION"));
    let release =
        fs::read_to_string("/etc/najs-release").or_else(|_| fs::read_to_string("/etc/os-release"));
    match release {
        Ok(contents) => {
            for line in contents.lines().filter(|line| {
                line.starts_with("PRETTY_NAME=") || line.starts_with("NAJS_GENERATION=")
            }) {
                println!("{}", line.replace('"', ""));
            }
        }
        Err(_) => println!("PRETTY_NAME=unknown development host"),
    }
    Ok(())
}

fn status() -> Result<()> {
    println!(
        "system: {}",
        if Path::new("/etc/najs-release").exists() {
            "Najs"
        } else {
            "development host"
        }
    );
    println!(
        "manifest: {}",
        availability(Path::new(DEFAULT_MANIFEST).exists())
    );
    println!("btrfs tools: {}", command_exists("btrfs"));
    println!("pacman: {}", command_exists("pacman"));
    println!("systemd: {}", command_exists("systemctl"));
    Ok(())
}

fn doctor() -> Result<()> {
    let mut failures = 0;
    let release = fs::read_to_string("/etc/najs-release").unwrap_or_default();
    let generation = release_value(&release, "NAJS_GENERATION").unwrap_or("unknown");

    doctor_check(
        &mut failures,
        "release metadata",
        Path::new("/etc/najs-release").is_file(),
    );
    doctor_check(
        &mut failures,
        "system manifest",
        load_manifest(Path::new(DEFAULT_MANIFEST))
            .and_then(|manifest| validate_manifest(&manifest))
            .is_ok(),
    );
    doctor_check(&mut failures, "pacman backend", command_available("pacman"));
    doctor_check(&mut failures, "systemd", command_available("systemctl"));
    doctor_check(
        &mut failures,
        "NetworkManager",
        command_success("systemctl", &["is-active", "NetworkManager.service"]),
    );
    doctor_check(
        &mut failures,
        "display manager",
        command_success("systemctl", &["is-active", "display-manager.service"]),
    );
    doctor_check(
        &mut failures,
        "UEFI runtime",
        Path::new("/sys/firmware/efi").is_dir(),
    );
    doctor_check(
        &mut failures,
        "Najs Fold assets",
        Path::new("/usr/share/icons/hicolor/scalable/apps/najs.svg").is_file()
            && Path::new("/usr/share/wallpapers/Najs/contents/images/2560x1600.png").is_file(),
    );
    doctor_check(
        &mut failures,
        "Fastfetch integration",
        command_available("fastfetch") && Path::new("/etc/xdg/fastfetch/config.jsonc").is_file(),
    );

    if generation == "initial" {
        let root_is_initial =
            command_output("findmnt", &["--noheadings", "--output", "FSROOT", "/"])
                .is_some_and(|root| root.trim() == "/roots/initial");
        doctor_check(&mut failures, "generation root", root_is_initial);
    } else {
        println!("[info] generation: {generation}");
    }

    if failures == 0 {
        println!("doctor: all checks passed");
        Ok(())
    } else {
        bail!("doctor found {failures} failed check(s)")
    }
}

fn doctor_check(failures: &mut usize, name: &str, passed: bool) {
    if passed {
        println!("[ok]   {name}");
    } else {
        println!("[fail] {name}");
        *failures += 1;
    }
}

fn release_value<'a>(contents: &'a str, key: &str) -> Option<&'a str> {
    let prefix = format!("{key}=");
    contents
        .lines()
        .find_map(|line| line.strip_prefix(&prefix))
        .map(|value| value.trim_matches('"'))
}

fn diff(path: &Path) -> Result<()> {
    let manifest = load_manifest(path)?;
    validate_manifest(&manifest)?;

    let installed = command_lines("pacman", &["-Qq"]);
    let enabled_services = manifest
        .services
        .enable
        .iter()
        .filter(|service| !command_success("systemctl", &["is-enabled", service]))
        .collect::<Vec<_>>();

    let installed = installed
        .unwrap_or_default()
        .into_iter()
        .collect::<BTreeSet<_>>();
    let missing_packages = manifest
        .packages
        .install
        .iter()
        .filter(|package| !installed.contains(*package))
        .collect::<Vec<_>>();
    let packages_to_remove = manifest
        .packages
        .remove
        .iter()
        .filter(|package| installed.contains(*package))
        .collect::<Vec<_>>();

    let hostname_change = manifest.system.hostname.as_ref().filter(|wanted| {
        fs::read_to_string("/etc/hostname")
            .map(|current| current.trim() != wanted.as_str())
            .unwrap_or(true)
    });

    if missing_packages.is_empty()
        && packages_to_remove.is_empty()
        && enabled_services.is_empty()
        && hostname_change.is_none()
    {
        println!("no managed changes");
        return Ok(());
    }

    if let Some(hostname) = hostname_change {
        println!("hostname: -> {hostname}");
    }
    for package in missing_packages {
        println!("package: +{package}");
    }
    for package in packages_to_remove {
        println!("package: -{package}");
    }
    for service in enabled_services {
        println!("service: enable {service}");
    }
    Ok(())
}

fn load_manifest(path: &Path) -> Result<Manifest> {
    let contents = fs::read_to_string(path)
        .with_context(|| format!("failed to read manifest {}", path.display()))?;
    toml::from_str(&contents).with_context(|| format!("invalid manifest {}", path.display()))
}

fn validate_manifest(manifest: &Manifest) -> Result<()> {
    if manifest.version != 1 {
        bail!(
            "unsupported manifest version {}; expected 1",
            manifest.version
        );
    }
    validate_names(
        "package",
        manifest
            .packages
            .install
            .iter()
            .chain(&manifest.packages.remove),
    )?;
    validate_names(
        "service",
        manifest
            .services
            .enable
            .iter()
            .chain(&manifest.services.disable),
    )?;
    validate_names("profile", manifest.profiles.enabled.iter())?;
    if let Some(environment) = &manifest.desktop.environment
        && !["plasma", "gnome", "hyprland", "xfce", "cinnamon"].contains(&environment.as_str())
    {
        bail!("unsupported desktop environment: {environment}");
    }
    if let Some(session) = &manifest.desktop.session
        && !["wayland", "xorg"].contains(&session.as_str())
    {
        bail!("unsupported desktop session: {session}");
    }
    if let Some(locale) = &manifest.system.locale
        && locale.trim().is_empty()
    {
        bail!("locale cannot be empty");
    }
    let _ = (manifest.features.bluetooth, manifest.features.printing);
    Ok(())
}

fn validate_names<'a>(kind: &str, names: impl Iterator<Item = &'a String>) -> Result<()> {
    for name in names {
        if name.is_empty()
            || !name
                .chars()
                .all(|ch| ch.is_ascii_alphanumeric() || ".+_@:-".contains(ch))
        {
            bail!("invalid {kind} name: {name:?}");
        }
    }
    Ok(())
}

fn availability(available: bool) -> &'static str {
    if available {
        "available"
    } else {
        "unavailable"
    }
}

fn command_exists(command: &str) -> &'static str {
    availability(command_available(command))
}

fn command_available(command: &str) -> bool {
    command_success("sh", &["-c", &format!("command -v {command} >/dev/null")])
}

fn command_success(command: &str, args: &[&str]) -> bool {
    Command::new(command)
        .args(args)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

fn command_lines(command: &str, args: &[&str]) -> Option<Vec<String>> {
    let output = Command::new(command).args(args).output().ok()?;
    output.status.success().then(|| {
        String::from_utf8_lossy(&output.stdout)
            .lines()
            .map(str::to_owned)
            .collect()
    })
}

fn command_output(command: &str, args: &[&str]) -> Option<String> {
    let output = Command::new(command).args(args).output().ok()?;
    output
        .status
        .success()
        .then(|| String::from_utf8_lossy(&output.stdout).into_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_reference_manifest() {
        let manifest: Manifest = toml::from_str(
            r#"
                version = 1
                [system]
                hostname = "najs-pc"
                [desktop]
                environment = "plasma"
                session = "wayland"
                [packages]
                install = ["firefox", "git"]
                [services]
                enable = ["NetworkManager.service"]
            "#,
        )
        .unwrap();
        validate_manifest(&manifest).unwrap();
        assert_eq!(manifest.packages.install.len(), 2);
    }

    #[test]
    fn rejects_unknown_manifest_fields() {
        let result = toml::from_str::<Manifest>("version = 1\nsurprise = true");
        assert!(result.is_err());
    }

    #[test]
    fn rejects_unsupported_version() {
        let manifest: Manifest = toml::from_str("version = 2").unwrap();
        assert!(validate_manifest(&manifest).is_err());
    }

    #[test]
    fn rejects_shell_metacharacters() {
        let manifest: Manifest =
            toml::from_str("version = 1\n[packages]\ninstall = [\"firefox; reboot\"]").unwrap();
        assert!(validate_manifest(&manifest).is_err());
    }

    #[test]
    fn accepts_supported_desktops() {
        for (environment, session) in [
            ("plasma", "wayland"),
            ("gnome", "wayland"),
            ("hyprland", "wayland"),
            ("xfce", "xorg"),
            ("cinnamon", "xorg"),
        ] {
            let source = format!(
                "version = 1\n[desktop]\nenvironment = {environment:?}\nsession = {session:?}"
            );
            let manifest: Manifest = toml::from_str(&source).unwrap();
            validate_manifest(&manifest).unwrap();
        }
    }

    #[test]
    fn reads_quoted_release_values() {
        let release = "PRETTY_NAME=\"Najs\"\nNAJS_GENERATION=\"initial\"\n";
        assert_eq!(release_value(release, "NAJS_GENERATION"), Some("initial"));
    }

    #[test]
    fn reports_missing_release_values() {
        assert_eq!(release_value("PRETTY_NAME=Najs\n", "NAJS_GENERATION"), None);
    }
}
