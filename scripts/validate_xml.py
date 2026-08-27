#!/usr/bin/env python3
"""Validate the exact two-variant Unraid XML contract without external tools."""

from __future__ import annotations

import sys
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SUPPORT_URL = "https://github.com/Significant-Gravitas/autogpt-unraid/issues"
TEMPLATE_BASE_URL = (
    "https://raw.githubusercontent.com/Significant-Gravitas/"
    "autogpt-unraid/main/templates"
)
ICON_URL = (
    "https://raw.githubusercontent.com/Significant-Gravitas/"
    "autogpt-unraid/main/images/autogpt.png"
)
HOSTED_REPOSITORY = "significantgravitas/autogpt:latest"
LOCAL_REPOSITORY = "ghcr.io/significant-gravitas/autogpt-unraid-local:latest"
HOSTED_EXTRA_PARAMS = (
    "--restart=unless-stopped --stop-timeout 360 --shm-size 2g "
    "--ulimit nofile=65536:65536 --log-driver json-file "
    "--log-opt max-size=50m --log-opt max-file=1"
)
LOCAL_EXTRA_PARAMS = (
    "--restart=unless-stopped --stop-timeout 360 --shm-size 2g "
    "--ulimit nofile=65536:65536 "
    "--add-host=host.docker.internal:host-gateway "
    "--log-driver json-file --log-opt max-size=50m --log-opt max-file=1"
)


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def equal(label: str, expected: object, actual: object) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def child_text(root: ET.Element, name: str) -> str:
    element = root.find(name)
    if element is None:
        fail(f"{name} element is missing")
    return element.text or ""


def parse(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        fail(f"cannot parse {path.relative_to(ROOT)}: {error}")


def configs(root: ET.Element) -> list[ET.Element]:
    return list(root.findall("Config"))


def config(root: ET.Element, filename: str, target: str) -> ET.Element:
    matches = [item for item in configs(root) if item.get("Target") == target]
    equal(f"{filename} {target} count", 1, len(matches))
    return matches[0]


def assert_config(
    root: ET.Element,
    filename: str,
    target: str,
    display: str,
    required: str,
    mask: str,
) -> ET.Element:
    item = config(root, filename, target)
    equal(f"{filename} {target} Display", display, item.get("Display"))
    equal(f"{filename} {target} Required", required, item.get("Required"))
    equal(f"{filename} {target} Mask", mask, item.get("Mask"))
    return item


def assert_default(
    root: ET.Element,
    filename: str,
    target: str,
    expected_default: str,
    expected_value: str,
) -> None:
    item = config(root, filename, target)
    equal(f"{filename} {target} Default", expected_default, item.get("Default"))
    equal(f"{filename} {target} value", expected_value, item.text or "")


def assert_common(root: ET.Element, filename: str) -> None:
    equal(f"{filename} root", "Container", root.tag)
    equal(f"{filename} schema version", "2", root.get("version"))
    equal(f"{filename} network", "bridge", child_text(root, "Network"))
    equal(f"{filename} privileged", "false", child_text(root, "Privileged"))
    equal(f"{filename} post args", "", child_text(root, "PostArgs"))
    equal(f"{filename} beta", "true", child_text(root, "Beta"))
    equal(f"{filename} support", SUPPORT_URL, child_text(root, "Support"))
    equal(
        f"{filename} TemplateURL",
        f"{TEMPLATE_BASE_URL}/{filename}",
        child_text(root, "TemplateURL"),
    )
    equal(f"{filename} icon", ICON_URL, child_text(root, "Icon"))

    targets = [item.get("Target") for item in configs(root)]
    equal(f"{filename} duplicate Config targets", len(targets), len(set(targets)))
    for item in configs(root):
        description = item.get("Description") or ""
        if "Example" not in description:
            fail(f"{filename} {item.get('Target')} description has no example")


def assert_runtime(
    root: ET.Element,
    filename: str,
    repository: str,
    appdata: str,
    extra_params: str,
) -> None:
    equal(f"{filename} repository", repository, child_text(root, "Repository"))
    equal(f"{filename} shell", "bash", child_text(root, "Shell"))
    equal(f"{filename} ExtraParams", extra_params, child_text(root, "ExtraParams"))
    if "LicenseRef-PolyForm-Shield-1.0.0 AND SSPL-1.0" not in child_text(
        root, "License"
    ):
        fail(f"{filename} image license is missing")

    assert_config(root, filename, "3000", "always", "true", "false")
    data = assert_config(root, filename, "/data", "always", "true", "false")
    equal(f"{filename} appdata default", appdata, data.get("Default"))
    assert_config(
        root, filename, "AUTOGPT_PUBLIC_URL", "always", "true", "false"
    )
    assert_config(
        root, filename, "AUTH_SIGNUP_ALLOWLIST", "always", "true", "false"
    )
    assert_config(
        root, filename, "AUTH_ALLOW_NEW_ACCOUNTS", "always", "true", "false"
    )
    assert_default(
        root, filename, "AUTH_ALLOW_NEW_ACCOUNTS", "true|false", "true"
    )

    requires = child_text(root, "Requires")
    if "Docker Stop Timeout" in requires:
        fail(f"{filename} must not require a host-wide stop-timeout change")
    if any(
        item.get("Target") == "CHAT_THINKING_STANDARD_MODEL"
        for item in configs(root)
    ):
        fail(f"{filename} exposes unsupported local thinking transport")


def validate_hosted(root: ET.Element) -> None:
    filename = "autogpt.xml"
    assert_common(root, filename)
    assert_runtime(
        root,
        filename,
        HOSTED_REPOSITORY,
        "/mnt/user/appdata/autogpt",
        HOSTED_EXTRA_PARAMS,
    )
    equal(f"{filename} Config count", 9, len(configs(root)))
    equal(f"{filename} name", "AutoGPT", child_text(root, "Name"))
    assert_config(root, filename, "OPEN_ROUTER_API_KEY", "always", "true", "true")
    assert_config(root, filename, "OPENAI_API_KEY", "always", "true", "true")
    assert_config(root, filename, "CHAT_USE_LOCAL", "advanced", "true", "false")
    assert_config(
        root, filename, "CHAT_USE_OPENROUTER", "advanced", "true", "false"
    )
    assert_default(root, filename, "OPEN_ROUTER_API_KEY", "", "")
    assert_default(root, filename, "OPENAI_API_KEY", "", "")
    assert_default(root, filename, "CHAT_USE_LOCAL", "true|false", "false")
    assert_default(root, filename, "CHAT_USE_OPENROUTER", "true|false", "true")

    forbidden = {
        "CHAT_UPSTREAM",
        "EMBED_UPSTREAM",
        "CHAT_BASE_URL",
        "CHAT_API_KEY",
        "CHAT_FAST_STANDARD_MODEL",
        "STORE_EMBEDDING_MODEL",
    }
    for item in configs(root):
        target = item.get("Target") or ""
        if target in forbidden or target.startswith("GRAPHITI_"):
            fail(f"{filename} exposes local/custom field {target}")
    if "providers, not AutoGPT, host the models" not in child_text(root, "Overview"):
        fail(f"{filename} provider boundary is missing")


def validate_local(root: ET.Element) -> None:
    filename = "autogpt-local.xml"
    assert_common(root, filename)
    assert_runtime(
        root,
        filename,
        LOCAL_REPOSITORY,
        "/mnt/user/appdata/autogpt-local",
        LOCAL_EXTRA_PARAMS,
    )
    equal(f"{filename} Config count", 10, len(configs(root)))
    equal(f"{filename} name", "AutoGPT-Fully-Local", child_text(root, "Name"))
    equal(
        f"{filename} Registry",
        "https://github.com/Significant-Gravitas/autogpt-unraid/"
        "pkgs/container/autogpt-unraid-local",
        child_text(root, "Registry"),
    )
    if "docs/fully-local.md" not in child_text(root, "ReadMe"):
        fail(f"{filename} fully-local readme is missing")

    public_targets = (
        "CHAT_UPSTREAM",
        "EMBED_UPSTREAM",
        "CHAT_FAST_STANDARD_MODEL",
        "GRAPHITI_LLM_MODEL",
        "GRAPHITI_RERANKER_MODEL",
    )
    for target in public_targets:
        assert_config(root, filename, target, "always", "true", "false")
        assert_default(root, filename, target, "", "")

    hidden = {
        "8098",
        "CHAT_BASE_URL",
        "CHAT_API_KEY",
        "CHAT_USE_LOCAL",
        "GRAPHITI_LLM_BASE_URL",
        "GRAPHITI_LLM_API_KEY",
        "GRAPHITI_EMBEDDER_BASE_URL",
        "GRAPHITI_EMBEDDER_API_KEY",
        "GRAPHITI_EMBEDDER_MODEL",
        "STORE_EMBEDDING_MODEL",
        "OPEN_ROUTER_API_KEY",
        "OPENAI_API_KEY",
    }
    present = hidden.intersection(item.get("Target") for item in configs(root))
    if present:
        fail(f"{filename} exposes internal plumbing: {sorted(present)}")
    chat_description = config(root, filename, "CHAT_UPSTREAM").get("Description") or ""
    for phrase in ("same device", "separate llama.cpp processes and ports"):
        if phrase not in chat_description:
            fail(f"{filename} chat origin does not explain {phrase!r}")


def main() -> int:
    published = sorted(TEMPLATES.glob("*.xml"))
    equal("published template count", 2, len(published))
    equal(
        "published template filenames",
        ["autogpt-local.xml", "autogpt.xml"],
        [item.name for item in published],
    )

    hosted = parse(TEMPLATES / "autogpt.xml")
    local = parse(TEMPLATES / "autogpt-local.xml")
    profile = parse(ROOT / "ca_profile.xml")
    validate_hosted(hosted)
    validate_local(local)
    if HOSTED_REPOSITORY == LOCAL_REPOSITORY:
        fail("hosted and fully-local repositories must be distinct")
    if child_text(hosted, "Name") == child_text(local, "Name"):
        fail("hosted and fully-local names must be distinct")
    equal("ca_profile.xml root", "CommunityApplications", profile.tag)
    equal("ca_profile.xml support URL", SUPPORT_URL, child_text(profile, "Forum"))
    if not child_text(profile, "Profile"):
        fail("ca_profile.xml Profile must be non-empty")
    print("Two published Unraid XML variants passed their exact contracts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
