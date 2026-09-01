# ADR-001: Arch Linux as v1 upstream

- Status: accepted for v1
- Date: 2026-08-31

## Problem

Najs needs a maintained package ecosystem while retaining local package changes
and building a distinct state-management layer.

## Options

Arch/archiso, Fedora bootc, Debian, Alpine, Void, Chimera, Gentoo, and an
independent userspace were reviewed against desktop package coverage, gaming,
NVIDIA, build tooling, transactionality, and small-team maintenance.

## Decision

Use Arch Linux packages and archiso as v1 upstream/bootstrap. Pacman is the only
supported low-level adapter initially.

## Rationale

Arch provides current kernels, Mesa, Plasma, Steam/multilib, NVIDIA packages,
simple packaging, and a direct live-image path. Fedora bootc offers stronger
ready-made atomic deployments, but its image-first package model conflicts with
the intended local `najs install` transaction workflow and would make Najs less
distinct at the system-state layer.

## Consequences

Najs must operate its own staged channels and substantial update QA rather than
passing raw rolling updates directly to users. Arch branding is replaced only
where legally and technically appropriate; licenses and upstream attribution
remain intact. Base migration remains possible because manifest semantics are
kept above the pacman adapter.

## Sources

- https://wiki.archlinux.org/title/Archiso
- https://wiki.archlinux.org/title/Pacman
- https://wiki.archlinux.org/title/Steam
- https://bootc-dev.github.io/bootc/
- https://live-team.pages.debian.net/live-manual/html/live-manual/index.en.html
