use std::collections::BTreeSet;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use anyhow::{Context, Result, bail};
use clap::{CommandFactory, Parser, Subcommand};
use clap_complete::{Shell, generate};
use serde::{Deserialize, Serialize};

const DEFAULT_MANIFEST: &str = "/etc/najs/manifest.toml";
const SUPPORTED_PROFILES: &[&str] = &[
    "communication",
    "creator",
    "desktop",
    "development",
    "gaming",
    "media",
    "office",
    "virtualization",
];

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
    Doctor {
        /// Emit a machine-readable report.
        #[arg(long)]
        json: bool,
    },
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
    /// Generate shell completion definitions.
    Completions {
        #[arg(value_enum)]
        shell: Shell,
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
        Commands::Doctor { json } => doctor(json),
        Commands::Validate { manifest } => {
            let manifest = load_manifest(&manifest)?;
            validate_manifest(&manifest)?;
            println!("manifest is valid (schema version {})", manifest.version);
            Ok(())
        }
        Commands::Diff { manifest } => diff(&manifest),
        Commands::Completions { shell } => {
            write_completions(shell, &mut std::io::stdout());
            Ok(())
        }
    }
}

fn write_completions<W: Write>(shell: Shell, writer: &mut W) {
    generate(shell, &mut Cli::command(), "najs", writer);
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
    let root_filesystem = command_output("findmnt", &["--noheadings", "--output", "FSTYPE", "/"])
        .map(|value| value.trim().to_owned())
        .unwrap_or_else(|| "unknown".to_owned());
    let root_subvolume = command_output("findmnt", &["--noheadings", "--output", "FSROOT", "/"])
        .map(|value| value.trim().to_owned())
        .unwrap_or_else(|| "unknown".to_owned());
    let boot_manager = detect_boot_manager();
    let release = fs::read_to_string("/etc/najs-release").unwrap_or_default();
    let generation = release_value(&release, "NAJS_GENERATION").unwrap_or("unknown");

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
    println!("root filesystem: {root_filesystem}");
    println!("root subvolume: {root_subvolume}");
    println!("boot manager: {boot_manager}");
    println!("generation: {generation}");
    let readiness = generation_readiness(&root_filesystem, &root_subvolume, boot_manager);
    println!("generation prerequisites: {readiness}");
    println!("transactions: unavailable (planned for M3)");
    Ok(())
}

#[derive(Serialize)]
struct DoctorCheck {
    name: &'static str,
    passed: bool,
}

#[derive(Serialize)]
struct DoctorReport<'a> {
    system: &'a str,
    generation: &'a str,
    ok: bool,
    checks: Vec<DoctorCheck>,
}

fn doctor(json: bool) -> Result<()> {
    let release = fs::read_to_string("/etc/najs-release").unwrap_or_default();
    let generation = release_value(&release, "NAJS_GENERATION").unwrap_or("unknown");
    let mut checks = vec![
        DoctorCheck {
            name: "release metadata",
            passed: Path::new("/etc/najs-release").is_file(),
        },
        DoctorCheck {
            name: "system manifest",
            passed: load_manifest(Path::new(DEFAULT_MANIFEST))
                .and_then(|manifest| validate_manifest(&manifest))
                .is_ok(),
        },
        DoctorCheck {
            name: "pacman backend",
            passed: command_available("pacman"),
        },
        DoctorCheck {
            name: "systemd",
            passed: command_available("systemctl"),
        },
        DoctorCheck {
            name: "NetworkManager",
            passed: command_success("systemctl", &["is-active", "NetworkManager.service"]),
        },
        DoctorCheck {
            name: "display manager",
            passed: command_success("systemctl", &["is-active", "display-manager.service"]),
        },
        DoctorCheck {
            name: "UEFI runtime",
            passed: Path::new("/sys/firmware/efi").is_dir(),
        },
        DoctorCheck {
            name: "Najs Fold assets",
            passed: Path::new("/usr/share/icons/hicolor/scalable/apps/najs.svg").is_file()
                && Path::new("/usr/share/wallpapers/Najs/contents/images/2560x1600.png").is_file(),
        },
        DoctorCheck {
            name: "Fastfetch integration",
            passed: command_available("fastfetch")
                && Path::new("/etc/xdg/fastfetch/config.jsonc").is_file()
                && Path::new("/usr/share/najs/fastfetch/logo.txt").is_file(),
        },
    ];

    if generation == "initial" {
        let root_is_initial =
            command_output("findmnt", &["--noheadings", "--output", "FSROOT", "/"])
                .is_some_and(|root| root.trim() == "/roots/initial");
        checks.push(DoctorCheck {
            name: "generation root",
            passed: root_is_initial,
        });
    }

    let failures = checks.iter().filter(|check| !check.passed).count();
    if json {
        let report = DoctorReport {
            system: if release.is_empty() {
                "development host"
            } else {
                "Najs"
            },
            generation,
            ok: failures == 0,
            checks,
        };
        serde_json::to_writer_pretty(std::io::stdout(), &report)?;
        println!();
    } else {
        for check in checks {
            doctor_check(check.name, check.passed);
        }
        if generation != "initial" {
            println!("[info] generation: {generation}");
        }
    }

    if failures == 0 {
        if !json {
            println!("doctor: all checks passed");
        }
        Ok(())
    } else {
        bail!("doctor found {failures} failed check(s)")
    }
}

fn doctor_check(name: &str, passed: bool) {
    if passed {
        println!("[ok]   {name}");
    } else {
        println!("[fail] {name}");
    }
}

fn release_value<'a>(contents: &'a str, key: &str) -> Option<&'a str> {
    let prefix = format!("{key}=");
    contents
        .lines()
        .find_map(|line| line.strip_prefix(&prefix))
        .map(|value| value.trim_matches('"'))
}

fn detect_boot_manager() -> &'static str {
    if Path::new("/boot/loader/loader.conf").is_file() || Path::new("/boot/loader/entries").is_dir()
    {
        "systemd-boot"
    } else if Path::new("/boot/grub/grub.cfg").is_file() {
        "GRUB"
    } else {
        "unknown"
    }
}

fn generation_readiness(
    root_filesystem: &str,
    root_subvolume: &str,
    boot_manager: &str,
) -> &'static str {
    if root_filesystem != "btrfs" {
        "unavailable (root filesystem is not Btrfs)"
    } else if !root_subvolume.starts_with("/roots/") {
        "unavailable (root is not a Najs generation subvolume)"
    } else if boot_manager != "systemd-boot" {
        "unavailable (systemd-boot is required)"
    } else {
        "available"
    }
}

fn diff(path: &Path) -> Result<()> {
    let manifest = load_manifest(path)?;
    validate_manifest(&manifest)?;

    let manages_services = !manifest.services.enable.is_empty()
        || !manifest.services.disable.is_empty()
        || manifest.features.bluetooth.is_some()
        || manifest.features.printing.is_some();
    if manages_services && !command_available("systemctl") {
        bail!("systemctl is unavailable; cannot compare managed services");
    }
    if (!manifest.packages.install.is_empty() || !manifest.packages.remove.is_empty())
        && !command_available("pacman")
    {
        bail!("pacman is unavailable; cannot compare managed packages");
    }

    let installed =
        if manifest.packages.install.is_empty() && manifest.packages.remove.is_empty() {
            Vec::new()
        } else {
            command_lines("pacman", &["-Qq"])
                .context("pacman query failed; package differences are unknown")?
        }
        .into_iter()
        .collect::<BTreeSet<_>>();
    let mut services_to_enable = manifest
        .services
        .enable
        .iter()
        .filter(|service| !command_success("systemctl", &["is-enabled", service]))
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    let mut services_to_disable = manifest
        .services
        .disable
        .iter()
        .filter(|service| command_success("systemctl", &["is-enabled", service]))
        .map(String::as_str)
        .collect::<BTreeSet<_>>();

    for (feature, service) in [
        (manifest.features.bluetooth, "bluetooth.service"),
        (manifest.features.printing, "cups.service"),
    ] {
        match feature {
            Some(true) if !command_success("systemctl", &["is-enabled", service]) => {
                services_to_enable.insert(service);
            }
            Some(false) if command_success("systemctl", &["is-enabled", service]) => {
                services_to_disable.insert(service);
            }
            _ => {}
        }
    }

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
    let locale_change = manifest.system.locale.as_ref().filter(|wanted| {
        fs::read_to_string("/etc/locale.conf")
            .ok()
            .and_then(|current| release_value(&current, "LANG").map(str::to_owned))
            .is_none_or(|current| current != wanted.as_str())
    });

    let current_manifest =
        if path != Path::new(DEFAULT_MANIFEST) && Path::new(DEFAULT_MANIFEST).is_file() {
            let current = load_manifest(Path::new(DEFAULT_MANIFEST))
                .context("failed to load the active Najs manifest")?;
            validate_manifest(&current).context("the active Najs manifest is invalid")?;
            Some(current)
        } else {
            None
        };
    let desktop_change = current_manifest.as_ref().is_some_and(|current| {
        current.desktop.environment != manifest.desktop.environment
            || current.desktop.session != manifest.desktop.session
    });
    let (profiles_to_enable, profiles_to_disable) = if let Some(current) = &current_manifest {
        let current_profiles = current.profiles.enabled.iter().collect::<BTreeSet<_>>();
        let wanted_profiles = manifest.profiles.enabled.iter().collect::<BTreeSet<_>>();
        (
            wanted_profiles
                .difference(&current_profiles)
                .copied()
                .collect::<Vec<_>>(),
            current_profiles
                .difference(&wanted_profiles)
                .copied()
                .collect::<Vec<_>>(),
        )
    } else {
        (Vec::new(), Vec::new())
    };

    if missing_packages.is_empty()
        && packages_to_remove.is_empty()
        && services_to_enable.is_empty()
        && services_to_disable.is_empty()
        && hostname_change.is_none()
        && locale_change.is_none()
        && !desktop_change
        && profiles_to_enable.is_empty()
        && profiles_to_disable.is_empty()
    {
        println!("no managed changes");
        return Ok(());
    }

    if let Some(hostname) = hostname_change {
        println!("hostname: -> {hostname}");
    }
    if let Some(locale) = locale_change {
        println!("locale: -> {locale}");
    }
    if desktop_change {
        let environment = manifest
            .desktop
            .environment
            .as_deref()
            .unwrap_or("unchanged");
        let session = manifest.desktop.session.as_deref().unwrap_or("unchanged");
        println!("desktop: -> {environment}/{session}");
    }
    for profile in profiles_to_enable {
        println!("profile: +{profile}");
    }
    for profile in profiles_to_disable {
        println!("profile: -{profile}");
    }
    for package in missing_packages {
        println!("package: +{package}");
    }
    for package in packages_to_remove {
        println!("package: -{package}");
    }
    for service in services_to_enable {
        println!("service: enable {service}");
    }
    for service in services_to_disable {
        println!("service: disable {service}");
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
    validate_unique("installed package", &manifest.packages.install)?;
    validate_unique("removed package", &manifest.packages.remove)?;
    validate_unique("enabled service", &manifest.services.enable)?;
    validate_unique("disabled service", &manifest.services.disable)?;
    validate_unique("profile", &manifest.profiles.enabled)?;
    validate_disjoint(
        "package",
        "install",
        &manifest.packages.install,
        "remove",
        &manifest.packages.remove,
    )?;
    validate_disjoint(
        "service",
        "enable",
        &manifest.services.enable,
        "disable",
        &manifest.services.disable,
    )?;
    for profile in &manifest.profiles.enabled {
        if !SUPPORTED_PROFILES.contains(&profile.as_str()) {
            bail!("unsupported profile: {profile}");
        }
    }
    if let Some(hostname) = &manifest.system.hostname
        && !valid_hostname(hostname)
    {
        bail!("invalid hostname: {hostname:?}");
    }
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
        && (locale.is_empty()
            || !locale
                .chars()
                .all(|ch| ch.is_ascii_alphanumeric() || "_.@-".contains(ch)))
    {
        bail!("invalid locale: {locale:?}");
    }
    for (feature, service) in [
        (manifest.features.bluetooth, "bluetooth.service"),
        (manifest.features.printing, "cups.service"),
    ] {
        if feature == Some(false)
            && manifest
                .services
                .enable
                .iter()
                .any(|enabled| enabled == service)
        {
            bail!("feature disables {service}, but the service is also enabled");
        }
        if feature == Some(true)
            && manifest
                .services
                .disable
                .iter()
                .any(|disabled| disabled == service)
        {
            bail!("feature enables {service}, but the service is also disabled");
        }
    }
    Ok(())
}

fn validate_unique(kind: &str, values: &[String]) -> Result<()> {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert(value) {
            bail!("duplicate {kind}: {value}");
        }
    }
    Ok(())
}

fn validate_disjoint(
    kind: &str,
    left_action: &str,
    left: &[String],
    right_action: &str,
    right: &[String],
) -> Result<()> {
    let right = right.iter().collect::<BTreeSet<_>>();
    if let Some(conflict) = left.iter().find(|value| right.contains(value)) {
        bail!("cannot {left_action} and {right_action} the same {kind}: {conflict}");
    }
    Ok(())
}

fn valid_hostname(hostname: &str) -> bool {
    (1..=63).contains(&hostname.len())
        && hostname
            .bytes()
            .all(|ch| ch.is_ascii_alphanumeric() || ch == b'-')
        && hostname
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_alphanumeric)
        && hostname
            .as_bytes()
            .last()
            .is_some_and(u8::is_ascii_alphanumeric)
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
    fn rejects_unknown_and_duplicate_profiles() {
        let unknown: Manifest =
            toml::from_str("version = 1\n[profiles]\nenabled = [\"magic\"]").unwrap();
        assert!(validate_manifest(&unknown).is_err());

        let duplicate: Manifest =
            toml::from_str("version = 1\n[profiles]\nenabled = [\"development\", \"development\"]")
                .unwrap();
        assert!(validate_manifest(&duplicate).is_err());
    }

    #[test]
    fn rejects_conflicting_package_and_service_operations() {
        let packages: Manifest = toml::from_str(
            "version = 1\n[packages]\ninstall = [\"firefox\"]\nremove = [\"firefox\"]",
        )
        .unwrap();
        assert!(validate_manifest(&packages).is_err());

        let services: Manifest = toml::from_str(
            "version = 1\n[services]\nenable = [\"cups.service\"]\ndisable = [\"cups.service\"]",
        )
        .unwrap();
        assert!(validate_manifest(&services).is_err());
    }

    #[test]
    fn rejects_feature_service_conflicts() {
        let manifest: Manifest = toml::from_str(
            "version = 1\n[features]\nprinting = false\n[services]\nenable = [\"cups.service\"]",
        )
        .unwrap();
        assert!(validate_manifest(&manifest).is_err());
    }

    #[test]
    fn validates_hostnames() {
        for hostname in ["najs", "gaming-pc", "najs42"] {
            assert!(valid_hostname(hostname));
        }
        for hostname in ["", "-najs", "najs-", "najs.local", "najs pc"] {
            assert!(!valid_hostname(hostname));
        }
    }

    #[test]
    fn reports_generation_prerequisite_reasons() {
        assert_eq!(
            generation_readiness("btrfs", "/roots/initial", "systemd-boot"),
            "available"
        );
        assert!(generation_readiness("ext4", "/", "systemd-boot").contains("not Btrfs"));
        assert!(generation_readiness("btrfs", "/", "systemd-boot").contains("subvolume"));
        assert!(generation_readiness("btrfs", "/roots/initial", "GRUB").contains("systemd-boot"));
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

    #[test]
    fn generates_completions_for_supported_shells() {
        for shell in [Shell::Bash, Shell::Zsh, Shell::Fish] {
            let mut output = Vec::new();
            write_completions(shell, &mut output);
            let output = String::from_utf8(output).unwrap();
            assert!(output.contains("najs"));
            assert!(output.contains("doctor"));
            assert!(output.contains("completions"));
        }
    }
}
