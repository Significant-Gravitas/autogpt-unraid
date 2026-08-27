#!/usr/bin/env python3
"""Install the local-model adapter into AutoGPT's existing Supervisor tree."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PROGRAM_NAME = "local-model-adapter"
RUNTIME_SECTION = "group:runtime"
REQUIRED_RUNTIME_PROGRAMS = {
    "bootstrap",
    "database-manager",
    "rest",
    "next",
    "nginx",
    "watchdog",
}


def install(
    config_path: Path,
    fragment_path: Path,
    healthcheck_path: Path | None = None,
) -> None:
    config = config_path.read_text(encoding="utf-8")
    fragment = fragment_path.read_text(encoding="utf-8").strip()

    if f"[program:{PROGRAM_NAME}]" in config or PROGRAM_NAME in config:
        raise RuntimeError(f"{PROGRAM_NAME} is already installed")
    if f"[program:{PROGRAM_NAME}]" not in fragment:
        raise RuntimeError("adapter fragment has the wrong program name")

    section_pattern = re.compile(
        rf"(?ms)^\[{re.escape(RUNTIME_SECTION)}\]\s*$"
        rf"(?P<body>.*?)(?=^\[|\Z)"
    )
    section_match = section_pattern.search(config)
    if section_match is None:
        raise RuntimeError(f"missing [{RUNTIME_SECTION}] section")

    body = section_match.group("body")
    programs_matches = list(
        re.finditer(r"(?m)^programs\s*=\s*(?P<value>[^\r\n]+)\s*$", body)
    )
    if len(programs_matches) != 1:
        raise RuntimeError(
            f"expected one programs entry in [{RUNTIME_SECTION}], "
            f"found {len(programs_matches)}"
        )

    programs_match = programs_matches[0]
    programs = [item.strip() for item in programs_match.group("value").split(",")]
    if any(not item for item in programs) or len(programs) != len(set(programs)):
        raise RuntimeError(f"invalid programs entry in [{RUNTIME_SECTION}]")
    missing = sorted(REQUIRED_RUNTIME_PROGRAMS.difference(programs))
    if missing:
        raise RuntimeError(
            f"unexpected AutoGPT runtime group; missing: {', '.join(missing)}"
        )

    replacement = "programs=" + ",".join([*programs, PROGRAM_NAME])
    body_start = section_match.start("body")
    value_start = body_start + programs_match.start()
    value_end = body_start + programs_match.end()
    updated = config[:value_start] + replacement + config[value_end:]
    updated = updated.rstrip() + "\n\n" + fragment + "\n"
    config_path.write_text(updated, encoding="utf-8")

    if healthcheck_path is not None:
        healthcheck = healthcheck_path.read_text(encoding="utf-8")
        health_program = f"runtime:{PROGRAM_NAME}"
        if health_program in healthcheck:
            raise RuntimeError(f"{health_program} is already installed")
        anchor = "    runtime:rest runtime:next runtime:nginx runtime:watchdog"
        if healthcheck.count(anchor) != 1:
            raise RuntimeError("unexpected AutoGPT healthcheck process list")
        healthcheck = healthcheck.replace(
            anchor,
            anchor + f"\n    {health_program}",
        )
        healthcheck_path.write_text(healthcheck, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--healthcheck", type=Path, required=True)
    args = parser.parse_args()
    install(args.config, args.fragment, args.healthcheck)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
