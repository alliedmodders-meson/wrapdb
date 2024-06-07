import subprocess
import configparser

from packaging import version as pkgversion


def get_provision(config: configparser.ConfigParser) -> dict[str, list[str]] | None:
    if 'provide' not in config.sections():
        return None

    provision: dict[str, list[str]] = {}

    for k, v in config['provide'].items():
        if k in ['program_names', 'dependency_names']:
            provision.setdefault(k, []).extend([item.strip() for item in v.split(',')])
            continue

        provision.setdefault('dependency_names', []).append(k)

    return provision


def get_releases() -> dict[str, list[pkgversion.Version]]:
    tags = [t.strip() for t in subprocess.check_output(['git', 'tag']).decode().splitlines()]
    releases: dict[str, list[pkgversion.Version]] = {}

    for tag in tags:
        parts = tag.split('_', 1)

        if len(parts) != 2:
            continue

        try:
            parsed_version = pkgversion.Version(parts[1])
        except pkgversion.InvalidVersion:
            continue

        releases.setdefault(parts[0], []).append(parsed_version)

    for k, v in releases.items():
        v.sort(reverse=True)

    return releases


def get_download_url(repo: str, tag: str, filename: str) -> str:
    return f'https://github.com/{repo}/releases/download/{tag}/{filename}'


def is_updated_package(name: str, version: pkgversion.Version, source: dict[str, list[pkgversion.Version]]) -> bool:
    return name not in source or version > source[name][0]
