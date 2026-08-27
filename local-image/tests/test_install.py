import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install import PROGRAM_NAME, install  # noqa: E402


BASE_CONFIG = """\
[supervisord]
nodaemon=true

[group:runtime]
programs=bootstrap,database-manager,rest,next,nginx,watchdog

[program:rest]
command=rest
"""

FRAGMENT = f"""\
[program:{PROGRAM_NAME}]
command=python /opt/autogpt-local/proxy.py
"""


class InstallTests(unittest.TestCase):
    def run_install(
        self,
        config: str = BASE_CONFIG,
        fragment: str = FRAGMENT,
        healthcheck: str | None = None,
    ) -> tuple[str, str | None]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "supervisord.conf"
            fragment_path = root / "fragment.conf"
            config_path.write_text(config, encoding="utf-8")
            fragment_path.write_text(fragment, encoding="utf-8")
            healthcheck_path = root / "healthcheck.sh"
            if healthcheck is not None:
                healthcheck_path.write_text(healthcheck, encoding="utf-8")
            install(
                config_path,
                fragment_path,
                healthcheck_path if healthcheck is not None else None,
            )
            return (
                config_path.read_text(encoding="utf-8"),
                healthcheck_path.read_text(encoding="utf-8")
                if healthcheck is not None
                else None,
            )

    def test_adds_adapter_to_runtime_group_and_appends_fragment(self) -> None:
        result, _ = self.run_install()
        self.assertIn(
            "programs=bootstrap,database-manager,rest,next,nginx,watchdog,"
            f"{PROGRAM_NAME}",
            result,
        )
        self.assertEqual(result.count(f"[program:{PROGRAM_NAME}]"), 1)

    def test_rejects_missing_runtime_group(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing"):
            self.run_install("[supervisord]\nnodaemon=true\n")

    def test_rejects_changed_runtime_contract(self) -> None:
        config = BASE_CONFIG.replace(",watchdog", "")
        with self.assertRaisesRegex(RuntimeError, "watchdog"):
            self.run_install(config)

    def test_rejects_duplicate_install(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "already installed"):
            self.run_install(BASE_CONFIG + "\n" + FRAGMENT)

    def test_rejects_wrong_fragment(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "wrong program name"):
            self.run_install(fragment="[program:other]\ncommand=true\n")

    def test_adds_adapter_to_healthcheck_process_list(self) -> None:
        healthcheck = """\
  local programs=(
    runtime:rest runtime:next runtime:nginx runtime:watchdog
  )
"""
        _, result = self.run_install(healthcheck=healthcheck)
        self.assertIn(f"    runtime:{PROGRAM_NAME}\n", result)

    def test_rejects_changed_healthcheck_contract(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "healthcheck process list"):
            self.run_install(healthcheck="local programs=(runtime:rest)\n")


if __name__ == "__main__":
    unittest.main()
