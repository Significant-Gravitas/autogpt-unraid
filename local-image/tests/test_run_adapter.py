import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_adapter import INTERNAL_VARIABLES, validation_errors  # noqa: E402


VALID_ENV = {
    **INTERNAL_VARIABLES,
    "CHAT_UPSTREAM": "http://host.docker.internal:8099",
    "EMBED_UPSTREAM": "http://192.168.1.42:8100/",
    "CHAT_FAST_STANDARD_MODEL": "ornith-1.5-9b",
    "GRAPHITI_LLM_MODEL": "ornith-1.5-9b",
    "GRAPHITI_RERANKER_MODEL": "ornith-1.5-9b",
}


class AdapterValidationTests(unittest.TestCase):
    def test_accepts_same_host_and_lan_origins(self) -> None:
        self.assertEqual(validation_errors(VALID_ENV), [])

    def test_requires_every_public_input(self) -> None:
        self.assertEqual(len(validation_errors(INTERNAL_VARIABLES)), 5)

    def test_rejects_internal_transport_override(self) -> None:
        env = {**VALID_ENV, "CHAT_BASE_URL": "http://other.example/v1"}
        self.assertTrue(any("managed" in item for item in validation_errors(env)))

    def test_rejects_v1_path(self) -> None:
        env = {**VALID_ENV, "CHAT_UPSTREAM": "http://model.example:8099/v1"}
        self.assertTrue(any("without /v1" in item for item in validation_errors(env)))

    def test_rejects_credentials_in_origin(self) -> None:
        env = {
            **VALID_ENV,
            "EMBED_UPSTREAM": "http://user:secret@model.example:8100",
        }
        self.assertTrue(any("credentials" in item for item in validation_errors(env)))

    def test_rejects_container_loopback(self) -> None:
        for origin in (
            "http://localhost:8099",
            "http://127.0.0.1:8099",
            "http://[::1]:8099",
        ):
            with self.subTest(origin=origin):
                env = {**VALID_ENV, "CHAT_UPSTREAM": origin}
                self.assertTrue(any("loopback" in item for item in validation_errors(env)))


if __name__ == "__main__":
    unittest.main()
