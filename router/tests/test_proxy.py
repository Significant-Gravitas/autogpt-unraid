import contextlib
import http.server
import io
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest import mock
import urllib.error
import urllib.request


ROUTER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROUTER_DIR))

import healthcheck  # noqa: E402
import proxy  # noqa: E402


PRIVATE_ORIGIN_SENTINEL = "http://router-user:router-secret@192.0.2.10:9999/private"
EXCEPTION_TEXT_SENTINEL = "ConnectionRefusedError: test-only-upstream-detail"


class StubHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        pass

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self._send_bytes(status, body, "application/json")

    def _send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Upstream-Debug", PRIVATE_ORIGIN_SENTINEL)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _record(self, method, payload):
        self.server.requests.append({
            "method": method,
            "path": self.path,
            "payload": payload,
            "headers": {key.lower(): value for key, value in self.headers.items()},
        })

    def _send_forced_error(self, mode):
        if mode == "force-plain-error":
            body = f"{PRIVATE_ORIGIN_SENTINEL}\n{EXCEPTION_TEXT_SENTINEL}".encode()
            self._send_bytes(429, body, "text/plain")
            return True
        if mode == "force-malformed-error":
            self._send_bytes(503, b'{"error":', "application/json")
            return True
        if mode == "force-oversized-error":
            prefix = f"{PRIVATE_ORIGIN_SENTINEL}\n{EXCEPTION_TEXT_SENTINEL}\n".encode()
            body = prefix + b"x" * (proxy.MAX_UPSTREAM_ERROR_BYTES + 1024)
            self._send_bytes(507, body, "text/html")
            return True
        return False

    def _wrong_upstream(self):
        self._send_json(501, {
            "error": {"message": f"wrong upstream role: {self.server.role}"},
        })

    def do_GET(self):
        self._record("GET", None)
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.server.role == "chat" and self.path == "/v1/models":
            self._send_json(200, {
                "object": "list",
                "data": [{"id": self.server.model_id, "object": "model"}],
            })
        elif (self.server.role == "chat"
              and self.path == "/force-oversized-error"):
            self._send_forced_error("force-oversized-error")
        else:
            self._wrong_upstream()

    def do_POST(self):
        payload = self._read_json()
        self._record("POST", payload)
        if self._send_forced_error(payload.get("model")):
            return
        if self.server.role == "chat" and self.path == "/tokenize":
            mapping = {
                "True": 2434,
                "False": 3913,
                " True": 2912,
                " False": 3439,
            }
            content = payload.get("content")
            tokens = [{"id": mapping.get(content, 999), "piece": content}]
            if self.server.invalid_tokenize and payload.get("content") == "True":
                tokens.append({"id": 999, "piece": "extra"})
            self._send_json(200, {"tokens": tokens})
        elif (self.server.role == "chat"
                and self.path == "/v1/chat/completions"):
            if payload.get("chat_template_kwargs") == {"enable_thinking": False}:
                label = "False" if self.server.reranker_mismatch else "True"
                self._send_json(200, {
                    "id": "chatcmpl_reranker",
                    "object": "chat.completion",
                    "model": payload.get("model"),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": label,
                            "reasoning_content": "",
                        },
                        "logprobs": {
                            "content": [{
                                "token": "True",
                                "logprob": -0.2,
                                "top_logprobs": [
                                    {"token": "True", "logprob": -0.2},
                                    {"token": "False", "logprob": -1.7},
                                ],
                            }],
                        },
                        "finish_reason": "stop",
                    }],
                })
            else:
                self._send_json(200, {
                    "id": "chatcmpl_test",
                    "object": "chat.completion",
                    "model": payload.get("model"),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": '{"name":"Ada"}',
                        },
                        "finish_reason": "stop",
                    }],
                    "usage": {
                        "prompt_tokens": 11,
                        "completion_tokens": 5,
                        "total_tokens": 16,
                    },
                })
        elif (self.server.role == "embeddings"
              and self.path == "/v1/embeddings"):
            self._send_json(200, {
                "object": "list",
                "model": payload.get("model"),
                "data": [{
                    "object": "embedding",
                    "index": 0,
                    "embedding": [1.0, -2.0],
                }],
            })
        elif self.server.role == "embeddings" and self.path == "/tokenize":
            self._send_json(200, {
                "tokens": list(range(len(payload.get("content", "")))),
            })
        elif self.server.role == "embeddings" and self.path == "/detokenize":
            self._send_json(200, {"content": "x" * len(payload.get("tokens", []))})
        else:
            self._wrong_upstream()


class QuietProxyHandler(proxy.Handler):
    def log_message(self, _format, *_args):
        pass


class RunningServer:
    def __init__(self, server):
        self.server = server
        self.thread = threading.Thread(target=server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    @property
    def base_url(self):
        host, port = self.server.server_address
        return f"http://{host}:{port}"


def make_stub(role, model_id):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
    server.role = role
    server.model_id = model_id
    server.requests = []
    server.invalid_tokenize = False
    server.reranker_mismatch = False
    return RunningServer(server).start()


def make_request(url, *, method="GET", payload=None, headers=None):
    data = None if payload is None else json.dumps(payload).encode()
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    return urllib.request.Request(
        url, data=data, method=method, headers=request_headers
    )


def request_json(url, *, method="GET", payload=None, headers=None):
    request = make_request(
        url, method=method, payload=payload, headers=headers
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read() or b"{}")


def request_error_json(url, *, method="GET", payload=None, headers=None):
    request = make_request(url, method=method, payload=payload, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as error:
        try:
            raw = error.read()
            response_headers = dict(error.headers.items())
            return error.code, response_headers, raw, json.loads(raw)
        finally:
            error.close()
    response.close()
    raise AssertionError("request unexpectedly succeeded")


def reranker_payload():
    return {
        "model": "ornith-1.5-9b",
        "messages": [
            {
                "role": "system",
                "content": proxy.GRAPHITI_RERANKER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
                    {proxy.GRAPHITI_RERANKER_INSTRUCTION}
                    <PASSAGE>Ada wrote the program.</PASSAGE>
                    <QUERY>Who wrote the program?</QUERY>
                """,
            },
        ],
        "temperature": 0,
        "max_tokens": 16,
        "logit_bias": {"6432": 1, "7983": 1},
        "logprobs": True,
        "top_logprobs": 2,
    }


class RouterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chat = make_stub("chat", "ornith-1.5-9b")
        cls.embeddings = make_stub("embeddings", "nomic-embed-text")
        cls.old_globals = {
            "CHAT_UPSTREAM": proxy.CHAT_UPSTREAM,
            "EMBED_UPSTREAM": proxy.EMBED_UPSTREAM,
            "EMBED_PAD_DIM": proxy.EMBED_PAD_DIM,
            "EMBED_MAX_TOKENS": proxy.EMBED_MAX_TOKENS,
            "GRAPHITI_RERANKER_MODEL": proxy.GRAPHITI_RERANKER_MODEL,
        }
        proxy.CHAT_UPSTREAM = cls.chat.base_url
        proxy.EMBED_UPSTREAM = cls.embeddings.base_url
        proxy.EMBED_PAD_DIM = 4
        proxy.EMBED_MAX_TOKENS = 2048
        proxy.GRAPHITI_RERANKER_MODEL = "ornith-1.5-9b"
        proxy.reset_reranker_token_cache()
        cls.router = RunningServer(
            proxy.ThreadedServer(("127.0.0.1", 0), QuietProxyHandler)
        ).start()

    @classmethod
    def tearDownClass(cls):
        cls.router.close()
        cls.embeddings.close()
        cls.chat.close()
        for name, value in cls.old_globals.items():
            setattr(proxy, name, value)
        proxy.reset_reranker_token_cache()

    def setUp(self):
        self.chat.server.requests.clear()
        self.embeddings.server.requests.clear()
        self.chat.server.invalid_tokenize = False
        self.chat.server.reranker_mismatch = False
        proxy.reset_reranker_token_cache()

    def test_chat_paths_are_passed_through(self):
        status, body = request_json(self.router.base_url + "/v1/models")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"][0]["id"], "ornith-1.5-9b")
        self.assertEqual(
            [(item["method"], item["path"]) for item in self.chat.server.requests],
            [("GET", "/v1/models")],
        )
        self.assertEqual(self.embeddings.server.requests, [])

    def test_router_health_is_local_and_does_not_mask_chat_state(self):
        status, body = request_json(self.router.base_url + "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok"})
        self.assertEqual(self.chat.server.requests, [])
        self.assertEqual(self.embeddings.server.requests, [])

    def test_graphiti_reranker_uses_local_tokens_and_disables_thinking(self):
        status, body = request_json(
            self.router.base_url + "/v1/chat/completions",
            method="POST",
            payload=reranker_payload(),
            headers={"Authorization": "Bearer client-only-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["choices"][0]["message"]["content"], "True")

        tokenize = [
            item for item in self.chat.server.requests
            if item["path"] == "/tokenize"
        ]
        self.assertEqual(
            [item["payload"]["content"] for item in tokenize],
            ["True", "False", " True", " False"],
        )
        completion = next(
            item for item in self.chat.server.requests
            if item["path"] == "/v1/chat/completions"
        )
        self.assertNotIn("authorization", completion["headers"])
        completion = completion["payload"]
        self.assertEqual(completion["logit_bias"], {"2434": 1, "3913": 1})
        self.assertEqual(
            completion["chat_template_kwargs"],
            {"enable_thinking": False},
        )

        request_json(
            self.router.base_url + "/v1/chat/completions",
            method="POST",
            payload=reranker_payload(),
        )
        self.assertEqual(
            len([item for item in self.chat.server.requests
                 if item["path"] == "/tokenize"]),
            4,
        )

    def test_graphiti_reranker_mismatch_fails_closed(self):
        self.chat.server.reranker_mismatch = True
        status, headers, raw, body = request_error_json(
            self.router.base_url + "/v1/chat/completions",
            method="POST",
            payload=reranker_payload(),
        )
        self.assertEqual(status, 502)
        self.assert_safe_upstream_error(headers, raw, body)

    def test_graphiti_reranker_tokenization_failure_fails_closed(self):
        self.chat.server.invalid_tokenize = True
        status, headers, raw, body = request_error_json(
            self.router.base_url + "/v1/chat/completions",
            method="POST",
            payload=reranker_payload(),
        )
        self.assertEqual(status, 502)
        self.assert_safe_upstream_error(headers, raw, body)
        self.assertEqual(
            [item["path"] for item in self.chat.server.requests],
            ["/tokenize"],
        )

    def test_reranker_lookalike_is_ordinary_passthrough(self):
        payload = reranker_payload()
        payload["messages"][0]["content"] += "."
        status, body = request_json(
            self.router.base_url + "/v1/chat/completions",
            method="POST",
            payload=payload,
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["choices"][0]["message"]["content"], '{"name":"Ada"}')
        self.assertEqual(
            [item["path"] for item in self.chat.server.requests],
            ["/v1/chat/completions"],
        )
        self.assertEqual(
            self.chat.server.requests[0]["payload"]["logit_bias"],
            proxy.GRAPHITI_OPENAI_BIAS,
        )

    def test_embedding_route_forces_float_and_pads_for_search(self):
        status, body = request_json(
            self.router.base_url + "/v1/embeddings",
            method="POST",
            payload={
                "model": "nomic-embed-text",
                "input": "hello",
                "encoding_format": "base64",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"][0]["embedding"], [1.0, -2.0, 0.0, 0.0])
        self.assertEqual(self.chat.server.requests, [])
        upstream = next(
            item["payload"] for item in self.embeddings.server.requests
            if item["method"] == "POST" and item["path"] == "/v1/embeddings"
        )
        self.assertEqual(upstream["encoding_format"], "float")

    def test_raw_embedding_route_preserves_native_width(self):
        status, body = request_json(
            self.router.base_url + "/raw/v1/embeddings",
            method="POST",
            payload={"model": "nomic-embed-text", "input": "hello"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"][0]["embedding"], [1.0, -2.0])
        self.assertEqual(self.chat.server.requests, [])
        self.assertEqual(
            [item["path"] for item in self.embeddings.server.requests],
            ["/v1/embeddings"],
        )

    def test_responses_route_translates_schema_and_wraps_reply(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        status, body = request_json(
            self.router.base_url + "/v1/responses",
            method="POST",
            payload={
                "model": "ornith-1.5-9b",
                "instructions": "Return one entity.",
                "input": [{
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Ada"}],
                }],
                "text": {"format": {
                    "type": "json_schema",
                    "name": "entity",
                    "strict": True,
                    "schema": schema,
                }},
                "max_output_tokens": 128,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["object"], "response")
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["output_text"], '{"name":"Ada"}')
        self.assertEqual(body["usage"]["total_tokens"], 16)

        self.assertEqual(self.embeddings.server.requests, [])
        upstream = next(
            item["payload"] for item in self.chat.server.requests
            if (item["method"] == "POST"
                and item["path"] == "/v1/chat/completions")
        )
        self.assertFalse(upstream["stream"])
        self.assertEqual(upstream["max_tokens"], 128)
        self.assertEqual(upstream["messages"][0], {
            "role": "system",
            "content": "Return one entity.",
        })
        self.assertEqual(upstream["response_format"]["type"], "json_schema")
        self.assertEqual(
            upstream["response_format"]["json_schema"]["schema"], schema
        )

    def test_bad_json_is_rejected_without_reaching_upstream(self):
        request = urllib.request.Request(
            self.router.base_url + "/v1/responses",
            data=b"not json",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(raised.exception.code, 400)
        self.assertEqual(self.chat.server.requests, [])
        self.assertEqual(self.embeddings.server.requests, [])

    def test_authorization_is_stripped_from_every_upstream_route(self):
        headers = {"Authorization": "Bearer client-only-secret"}
        request_json(
            self.router.base_url + "/v1/models",
            headers=headers,
        )
        request_json(
            self.router.base_url + "/v1/responses",
            method="POST",
            headers=headers,
            payload={"model": "ornith-1.5-9b", "input": "hello"},
        )
        request_json(
            self.router.base_url + "/v1/embeddings",
            method="POST",
            headers=headers,
            payload={"model": "nomic-embed-text", "input": "hello"},
        )

        forwarded = self.chat.server.requests + self.embeddings.server.requests
        self.assertEqual(len(forwarded), 3)
        for item in forwarded:
            self.assertNotIn("authorization", item["headers"])
            self.assertNotIn(
                "client-only-secret",
                "\n".join(item["headers"].values()),
            )

    def assert_safe_upstream_error(self, headers, raw, body):
        self.assertEqual(body, proxy.UPSTREAM_ERROR)
        self.assertLess(len(raw), 512)
        self.assertEqual(headers["Content-Type"], "application/json")
        text = raw.decode("utf-8") + "\n" + "\n".join(
            f"{key}: {value}" for key, value in headers.items()
        )
        self.assertNotIn(PRIVATE_ORIGIN_SENTINEL, text)
        self.assertNotIn(EXCEPTION_TEXT_SENTINEL, text)
        self.assertNotIn(self.chat.base_url, text)
        self.assertNotIn(self.embeddings.base_url, text)

    def test_plain_responses_upstream_error_is_sanitized(self):
        status, headers, raw, body = request_error_json(
            self.router.base_url + "/v1/responses",
            method="POST",
            payload={"model": "force-plain-error", "input": "hello"},
        )
        self.assertEqual(status, 429)
        self.assert_safe_upstream_error(headers, raw, body)

    def test_malformed_embedding_upstream_error_is_sanitized(self):
        status, headers, raw, body = request_error_json(
            self.router.base_url + "/v1/embeddings",
            method="POST",
            payload={"model": "force-malformed-error", "input": "hello"},
        )
        self.assertEqual(status, 503)
        self.assert_safe_upstream_error(headers, raw, body)

    def test_oversized_passthrough_upstream_error_is_bounded_and_sanitized(self):
        status, headers, raw, body = request_error_json(
            self.router.base_url + "/force-oversized-error",
        )
        self.assertEqual(status, 507)
        self.assert_safe_upstream_error(headers, raw, body)

    def test_unreachable_upstream_does_not_leak_origin_or_exception(self):
        closed = http.server.HTTPServer(("127.0.0.1", 0), StubHandler)
        dead_origin = "http://127.0.0.1:%d/private-origin" % (
            closed.server_address[1],
        )
        closed.server_close()

        original = proxy.CHAT_UPSTREAM
        proxy.CHAT_UPSTREAM = dead_origin
        try:
            status, headers, raw, body = request_error_json(
                self.router.base_url + "/v1/models",
            )
        finally:
            proxy.CHAT_UPSTREAM = original

        self.assertEqual(status, 502)
        self.assert_safe_upstream_error(headers, raw, body)
        self.assertNotIn(dead_origin, raw.decode("utf-8"))

    def test_healthcheck_exercises_both_upstreams(self):
        with mock.patch.dict(os.environ, {
            "CHAT_UPSTREAM": self.chat.base_url,
            "EMBED_UPSTREAM": self.embeddings.base_url,
            "LISTEN_PORT": str(self.router.server.server_address[1]),
        }):
            self.assertEqual(healthcheck.main(), 0)
        self.assertEqual(
            [(item["method"], item["path"])
             for item in self.chat.server.requests],
            [("GET", "/health")],
        )
        self.assertEqual(
            [(item["method"], item["path"])
             for item in self.embeddings.server.requests],
            [("GET", "/health")],
        )


class RouterUnitTests(unittest.TestCase):
    def test_normalize_upstream_removes_trailing_slashes(self):
        self.assertEqual(
            proxy.normalize_upstream("http://model-host.example:8099///"),
            "http://model-host.example:8099",
        )

    def test_base_path_removes_query_and_trailing_slash(self):
        self.assertEqual(proxy.base_path("/v1/embeddings/?trace=1"), "/v1/embeddings")

    def test_pad_embeddings_never_truncates_wider_vectors(self):
        obj = {"data": [
            {"embedding": [1.0]},
            {"embedding": [1.0, 2.0, 3.0]},
            {"embedding": "encoded"},
        ]}
        self.assertEqual(proxy.pad_embeddings(obj, 2), 1)
        self.assertEqual(obj["data"][0]["embedding"], [1.0, 0.0])
        self.assertEqual(obj["data"][1]["embedding"], [1.0, 2.0, 3.0])
        self.assertEqual(obj["data"][2]["embedding"], "encoded")

    def test_clamp_input_uses_embedder_tokenizer_and_margin(self):
        original_max = proxy.EMBED_MAX_TOKENS
        original_post_json = proxy.post_json
        calls = []

        def fake_post_json(url, payload):
            calls.append((url, payload))
            if url.endswith("/tokenize"):
                return {"tokens": list(range(len(payload["content"])))}
            if url.endswith("/detokenize"):
                return {"content": "trimmed"}
            raise AssertionError(url)

        try:
            proxy.EMBED_MAX_TOKENS = 12
            proxy.post_json = fake_post_json
            payload = {"input": "abcdefghij"}
            self.assertEqual(proxy.clamp_input(payload), 1)
        finally:
            proxy.EMBED_MAX_TOKENS = original_max
            proxy.post_json = original_post_json

        self.assertEqual(payload["input"], "trimmed")
        self.assertTrue(calls[0][0].endswith("/tokenize"))
        self.assertEqual(len(calls[1][1]["tokens"]), 4)

    def test_upstream_error_body_read_is_bounded_and_closed(self):
        class RecordingError:
            def __init__(self):
                self.read_size = None
                self.closed = False

            def read(self, size):
                self.read_size = size
                return b"x" * size

            def close(self):
                self.closed = True

        error = RecordingError()
        proxy.discard_upstream_error(error)
        self.assertEqual(
            error.read_size,
            proxy.MAX_UPSTREAM_ERROR_BYTES + 1,
        )
        self.assertTrue(error.closed)

    def test_startup_message_redacts_configured_upstream_origins(self):
        old_chat = proxy.CHAT_UPSTREAM
        old_embeddings = proxy.EMBED_UPSTREAM
        try:
            proxy.CHAT_UPSTREAM = PRIVATE_ORIGIN_SENTINEL + "/chat"
            proxy.EMBED_UPSTREAM = PRIVATE_ORIGIN_SENTINEL + "/embeddings"
            message = proxy.startup_message()
        finally:
            proxy.CHAT_UPSTREAM = old_chat
            proxy.EMBED_UPSTREAM = old_embeddings

        self.assertNotIn(PRIVATE_ORIGIN_SENTINEL, message)
        self.assertIn("embeddings=configured chat=configured", message)

    def test_healthcheck_failure_does_not_log_exception_or_origin(self):
        stderr = io.StringIO()
        failure = urllib.error.URLError(
            f"{EXCEPTION_TEXT_SENTINEL} at {PRIVATE_ORIGIN_SENTINEL}"
        )
        with mock.patch.object(healthcheck, "check_health", side_effect=failure):
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(healthcheck.main(), 1)

        output = stderr.getvalue()
        self.assertIn("unhealthy: router endpoint is not ready", output)
        self.assertNotIn(PRIVATE_ORIGIN_SENTINEL, output)
        self.assertNotIn(EXCEPTION_TEXT_SENTINEL, output)


if __name__ == "__main__":
    unittest.main()
