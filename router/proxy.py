#!/usr/bin/env python3
"""One OpenAI-compatible endpoint in front of two llama.cpp servers.

Two problems this solves, both caused by llama.cpp's surface not matching what
clients assume:

1. ``--embeddings`` RESTRICTS a server to embeddings only, so one process
   cannot serve both chat and embeddings. AutoGPT under ``CHAT_USE_LOCAL=true``
   points every platform helper at a single ``CHAT_BASE_URL``, so embedding
   calls 501 against the chat server. Routed here by path.

2. llama.cpp's ``/v1/responses`` ACCEPTS ``text.format`` (json_schema) and then
   IGNORES it -- the model free-forms. Verified directly: a strict schema on
   ``/v1/responses`` came back as a markdown table, while the same schema via
   ``/v1/chat/completions`` ``response_format`` returned clean conforming JSON.
   graphiti_core's ``openai_client.py`` calls ``client.responses.parse(...)``,
   so entity extraction fails validation on every episode. This translates
   Responses -> Chat Completions (where the schema IS enforced by grammar) and
   converts the reply back into Responses shape.

3. The two consumers disagree on embedding width. AutoGPT's search table is
   ``vector(1536)`` NOT NULL (sized for text-embedding-3-small) and rejects
   anything else, while Graphiti's local default -- and the only embedder small
   enough to sit beside a 9.6 GB chat model on this card -- is nomic-embed-text
   at 768. Zero-padding 768 -> 1536 is exact for cosine: appending zeros changes
   neither the dot product nor either norm, so ranking is bit-identical to
   searching in 768 dimensions. Queries take the same path, so both sides stay
   consistent. Graphiti keeps its native width via the ``/raw`` prefix, because
   FalkorDB fixes the vector index width at creation and it was built at 768.

4. Graphiti's reranker request carries OpenAI-specific True/False token IDs.
   Those IDs mean unrelated text in other tokenizers, so a local request can
   return HTTP 200 while silently ranking facts incorrectly. The exact Graphiti
   classifier request is remapped with llama.cpp's own tokenizer, forced out of
   thinking mode, and rejected unless selected content and scored token agree.

Routing:
    /v1/embeddings, /embeddings, /embedding -> EMBED_UPSTREAM (8100), padded
    /raw/... (prefix stripped)              -> as above but never padded
    /v1/responses                           -> CHAT_UPSTREAM, translated
    everything else                         -> CHAT_UPSTREAM (8099)
"""
import http.server
import json
import signal
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

import os

def normalize_upstream(value):
    """Accept an operator-entered origin with or without a trailing slash."""
    return value.rstrip("/")


CHAT_UPSTREAM = normalize_upstream(
    os.getenv("CHAT_UPSTREAM", "http://127.0.0.1:8099")
)
EMBED_UPSTREAM = normalize_upstream(
    os.getenv("EMBED_UPSTREAM", "http://127.0.0.1:8100")
)
GRAPHITI_RERANKER_MODEL = os.getenv("GRAPHITI_RERANKER_MODEL", "")
LISTEN_HOST = os.getenv("LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.getenv("LISTEN_PORT", "8098"))
TIMEOUT = 1800
# 0 disables padding entirely.
EMBED_PAD_DIM = int(os.getenv("EMBED_PAD_DIM", "1536"))
# Conservative ceiling verified against the accepted Nomic GGUF/llama.cpp
# server. Other Nomic runtimes can support longer inputs; 0 disables trimming.
EMBED_MAX_TOKENS = int(os.getenv("EMBED_MAX_TOKENS", "2048"))
SPECIAL_TOKEN_MARGIN = 8
RAW_PREFIX = "/raw"

GRAPHITI_RERANKER_SYSTEM_PROMPT = (
    "You are an expert tasked with determining whether the passage is relevant "
    "to the query"
)
GRAPHITI_RERANKER_INSTRUCTION = (
    'Respond with "True" if PASSAGE is relevant to QUERY and "False" otherwise.'
)
GRAPHITI_OPENAI_BIAS = {"6432": 1, "7983": 1}
_reranker_token_ids = None
_reranker_token_ids_origin = None
_reranker_token_lock = threading.Lock()

EMBED_PATHS = ("/v1/embeddings", "/embeddings", "/embedding")
RESPONSES_PATHS = ("/v1/responses", "/responses")

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host",
}
# The router intentionally supports unauthenticated llama.cpp upstreams only.
# Never let a bearer token supplied to the public-facing router become an
# ambient credential on either upstream.
STRIPPED_REQUEST_HEADERS = HOP_BY_HOP | {"authorization"}

# Upstream error bodies are untrusted and can be arbitrarily large. Drain only
# a small bounded prefix before closing the response, then return our own stable
# error envelope rather than relaying body text, headers, origins, or exception
# details to the caller.
MAX_UPSTREAM_ERROR_BYTES = 64 * 1024
UPSTREAM_ERROR = {
    "error": {
        "message": "upstream request failed",
        "type": "upstream_error",
    },
}


def base_path(path: str) -> str:
    return path.split("?", 1)[0].rstrip("/")


def responses_input_to_messages(payload):
    """Responses ``input`` accepts a bare string or a list of message dicts
    whose ``content`` may itself be a list of typed parts. Chat Completions
    wants plain {role, content} strings, so flatten."""
    raw = payload.get("input")
    if raw is None:
        return [{"role": "user", "content": ""}]
    if isinstance(raw, str):
        msgs = [{"role": "user", "content": raw}]
    else:
        msgs = []
        for item in raw:
            if not isinstance(item, dict):
                msgs.append({"role": "user", "content": str(item)})
                continue
            role = item.get("role", "user")
            content = item.get("content", "")
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict):
                        parts.append(p.get("text") or p.get("input_text") or "")
                    else:
                        parts.append(str(p))
                content = "".join(parts)
            msgs.append({"role": role, "content": content})
    # Responses carries the system prompt separately from ``input``.
    instructions = payload.get("instructions")
    if instructions:
        msgs.insert(0, {"role": "system", "content": instructions})
    return msgs


def extract_schema(payload):
    """Pull the json_schema out of Responses' ``text.format`` and re-shape it
    for Chat Completions' ``response_format``."""
    fmt = ((payload.get("text") or {}).get("format")) or {}
    if fmt.get("type") != "json_schema":
        return None
    schema = fmt.get("schema") or fmt.get("json_schema")
    if not schema:
        return None
    return {
        "type": "json_schema",
        "json_schema": {
            "name": fmt.get("name") or "response",
            "schema": schema,
            "strict": bool(fmt.get("strict", True)),
        },
    }


def to_responses_shape(chat, model):
    """Wrap a Chat Completions reply in the Responses envelope the OpenAI SDK
    parses (it reads output[].content[].text)."""
    choice = (chat.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    text = msg.get("content") or ""
    usage = chat.get("usage") or {}
    return {
        "id": "resp_" + uuid.uuid4().hex[:24],
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": chat.get("model") or model,
        "output": [{
            "id": "msg_" + uuid.uuid4().hex[:24],
            "type": "message",
            "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "text": text, "annotations": []}],
        }],
        "output_text": text,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
        "parallel_tool_calls": False,
        "tool_choice": "none",
        "tools": [],
    }


def pad_embeddings(obj, target):
    """Zero-extend every embedding to ``target`` dims, in place.

    Exact for cosine similarity -- appended zeros leave the dot product and
    both norms untouched -- so this widens vectors to fit a fixed-width column
    without perturbing ranking. Never truncates: a vector WIDER than the target
    cannot be narrowed without losing information, so it is passed through and
    left to fail loudly at the database rather than silently mis-ranked.
    """
    n = 0
    for row in (obj.get("data") or []):
        emb = row.get("embedding")
        if isinstance(emb, list) and len(emb) < target:
            row["embedding"] = emb + [0.0] * (target - len(emb))
            n += 1
    return n


def post_json(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _is_plain_number(value, expected):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value == expected
    )


def is_graphiti_reranker_request(payload):
    """Match only AutoGPT's pinned Graphiti cross-encoder request shape."""
    if not isinstance(payload, dict) or not GRAPHITI_RERANKER_MODEL:
        return False
    if payload.get("model") != GRAPHITI_RERANKER_MODEL:
        return False
    if payload.get("stream") not in (None, False):
        return False
    if not _is_plain_number(payload.get("temperature"), 0):
        return False
    if not _is_plain_number(payload.get("max_tokens"), 16):
        return False
    if payload.get("logprobs") is not True:
        return False
    if not _is_plain_number(payload.get("top_logprobs"), 2):
        return False
    bias = payload.get("logit_bias")
    if not isinstance(bias, dict) or bias != GRAPHITI_OPENAI_BIAS:
        return False
    if any(payload.get(name) for name in (
        "tools", "response_format", "grammar", "chat_template_kwargs"
    )):
        return False

    messages = payload.get("messages")
    if not isinstance(messages, list) or len(messages) != 2:
        return False
    system, user = messages
    if not isinstance(system, dict) or not isinstance(user, dict):
        return False
    if (
        system.get("role") != "system"
        or system.get("content") != GRAPHITI_RERANKER_SYSTEM_PROMPT
    ):
        return False
    content = user.get("content")
    if user.get("role") != "user" or not isinstance(content, str):
        return False
    if GRAPHITI_RERANKER_INSTRUCTION not in content:
        return False
    markers = ("<PASSAGE>", "</PASSAGE>", "<QUERY>", "</QUERY>")
    positions = [content.find(marker) for marker in markers]
    return all(position >= 0 for position in positions) and positions == sorted(positions)


def _single_token_id(payload, expected_piece):
    tokens = payload.get("tokens") if isinstance(payload, dict) else None
    if (
        not isinstance(tokens, list)
        or len(tokens) != 1
        or not isinstance(tokens[0], dict)
        or tokens[0].get("piece") != expected_piece
        or not isinstance(tokens[0].get("id"), int)
        or isinstance(tokens[0].get("id"), bool)
    ):
        raise RuntimeError("reranker label is not one token")
    return tokens[0]["id"]


def reset_reranker_token_cache():
    """Reset process cache; used by contract tests after changing upstreams."""
    global _reranker_token_ids, _reranker_token_ids_origin
    with _reranker_token_lock:
        _reranker_token_ids = None
        _reranker_token_ids_origin = None


def reranker_token_ids():
    """Discover and cache this llama.cpp tokenizer's bare label IDs."""
    global _reranker_token_ids, _reranker_token_ids_origin
    with _reranker_token_lock:
        if (
            _reranker_token_ids is not None
            and _reranker_token_ids_origin
            == (CHAT_UPSTREAM, GRAPHITI_RERANKER_MODEL)
        ):
            return _reranker_token_ids

        discovered = {}
        for label in ("True", "False", " True", " False"):
            discovered[label] = _single_token_id(
                post_json(CHAT_UPSTREAM + "/tokenize", {
                    "model": GRAPHITI_RERANKER_MODEL,
                    "content": label,
                    "add_special": False,
                    "parse_special": False,
                    "with_pieces": True,
                }),
                label,
            )
        true_id = discovered["True"]
        false_id = discovered["False"]
        if true_id == false_id:
            raise RuntimeError("reranker labels share a token ID")
        _reranker_token_ids = (true_id, false_id)
        _reranker_token_ids_origin = (CHAT_UPSTREAM, GRAPHITI_RERANKER_MODEL)
        return _reranker_token_ids


def valid_reranker_response(response):
    """Require selected content and first scored token to agree exactly."""
    try:
        choice = response["choices"][0]
        message = choice["message"]
        content_label = message["content"].strip()
        if message.get("reasoning_content"):
            return False
        scored_label = (
            choice["logprobs"]["content"][0]["top_logprobs"][0]["token"].strip()
        )
    except (KeyError, IndexError, TypeError, AttributeError):
        return False
    return content_label in {"True", "False"} and scored_label == content_label


def discard_upstream_error(error):
    """Bound reads from an HTTPError body and close it without exposing it."""
    try:
        error.read(MAX_UPSTREAM_ERROR_BYTES + 1)
    except Exception:
        pass
    finally:
        try:
            error.close()
        except Exception:
            pass


def startup_message():
    """Describe routing without logging private configured upstream origins."""
    return (
        "llm-router-proxy on %s:%d -> embeddings=configured chat=configured\n"
        "  /v1/responses  : translated to chat/completions so json_schema binds\n"
        "  Graphiti rerank: local True/False token IDs with validated scoring\n"
        "  /v1/embeddings : trimmed to %s tokens, zero-padded to %s dims"
        " (%s/v1/embeddings stays native)\n"
        % (LISTEN_HOST, LISTEN_PORT, EMBED_MAX_TOKENS or "no",
           EMBED_PAD_DIM or "no", RAW_PREFIX)
    )


def clamp_input(payload):
    """Trim each input to the embedder ceiling configured for this route.

    llama.cpp does not truncate: an over-long input comes back as a 500
    ("input (4747 tokens) is too large"), which the caller sees as a failed
    row rather than a shorter embedding. AutoGPT trims to OpenAI's 8191-token
    limit, which is nearly 4x what nomic-embed-text was trained on, so the
    trimming has to happen here. Uses the server's own /tokenize + /detokenize
    so the boundary is exact rather than a chars-per-token guess -- and only
    for inputs long enough to be at risk, since it costs two extra round trips.
    """
    if not EMBED_MAX_TOKENS:
        return 0
    # /tokenize reports the bare sequence, but the embedding path wraps it in
    # BERT's [CLS] and [SEP]. Trimming to the ceiling itself therefore lands
    # two tokens OVER it ("input (2050 tokens) is too large ... batch size:
    # 2048"); the margin absorbs those plus any drift from the detokenize /
    # retokenize round trip, at a cost of a few tokens off the tail.
    budget = max(1, EMBED_MAX_TOKENS - SPECIAL_TOKEN_MARGIN)
    raw = payload.get("input")
    items = raw if isinstance(raw, list) else [raw]
    trimmed = 0
    out = []
    for text in items:
        # A token is at least one character, so anything shorter than the
        # budget cannot exceed it and needs no round trip.
        if not isinstance(text, str) or len(text) <= budget:
            out.append(text)
            continue
        toks = post_json(EMBED_UPSTREAM + "/tokenize", {"content": text}).get("tokens") or []
        if len(toks) <= budget:
            out.append(text)
            continue
        text = post_json(EMBED_UPSTREAM + "/detokenize",
                         {"tokens": toks[:budget]}).get("content", text)
        trimmed += 1
        out.append(text)
    if trimmed:
        payload["input"] = out if isinstance(raw, list) else out[0]
    return trimmed


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "llm-router-proxy/2.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_upstream_error(self, error):
        code = error.code
        discard_upstream_error(error)
        self._send_json(code, UPSTREAM_ERROR)

    def _handle_responses(self, body):
        """Translate Responses -> Chat Completions so the schema is enforced."""
        try:
            payload = json.loads(body or b"{}")
        except Exception:
            self._send_json(400, {"error": {
                "message": "invalid JSON request body",
                "type": "invalid_request_error",
            }})
            return

        chat_req = {
            "model": payload.get("model"),
            "messages": responses_input_to_messages(payload),
            "stream": False,
        }
        rf = extract_schema(payload)
        if rf:
            chat_req["response_format"] = rf
        for src, dst in (("max_output_tokens", "max_tokens"),
                         ("temperature", "temperature"),
                         ("top_p", "top_p")):
            if payload.get(src) is not None:
                chat_req[dst] = payload[src]
        # A reasoning model spends tokens in <think> before any JSON appears;
        # too small a cap yields empty content and a confusing parse error.
        chat_req.setdefault("max_tokens", 4096)

        data = json.dumps(chat_req).encode()
        req = urllib.request.Request(
            CHAT_UPSTREAM + "/v1/chat/completions", data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                chat = json.loads(r.read())
        except urllib.error.HTTPError as e:
            self._send_upstream_error(e)
            return
        except Exception:
            self._send_json(502, UPSTREAM_ERROR)
            return

        self._send_json(200, to_responses_shape(chat, payload.get("model")))

    def _handle_embeddings(self, body, pad):
        """Buffer the embedder's reply so widths can be normalised."""
        try:
            payload = json.loads(body or b"{}")
        except Exception:
            self._send_json(400, {"error": {
                "message": "invalid JSON request body",
                "type": "invalid_request_error",
            }})
            return

        # The OpenAI SDK asks for base64 by default, and llama.cpp obliges --
        # which hid the padding below for a whole backfill, because a base64
        # string is not a list and slipped through untouched. Forcing float
        # keeps the vectors inspectable here; the SDK's decoder only rewrites
        # values that came back as strings, so a list reaches the caller
        # unchanged either way.
        payload["encoding_format"] = "float"

        try:
            clamp_input(payload)
            obj = post_json(EMBED_UPSTREAM + "/v1/embeddings", payload)
        except urllib.error.HTTPError as e:
            self._send_upstream_error(e)
            return
        except Exception:
            self._send_json(502, UPSTREAM_ERROR)
            return
        if pad:
            pad_embeddings(obj, pad)
        self._send_json(200, obj)

    def _handle_reranker(self, payload):
        """Adapt and validate the one known Graphiti classifier request."""
        try:
            true_id, false_id = reranker_token_ids()
            payload["logit_bias"] = {str(true_id): 1, str(false_id): 1}
            payload["chat_template_kwargs"] = {"enable_thinking": False}
            response = post_json(
                CHAT_UPSTREAM + "/v1/chat/completions",
                payload,
            )
        except urllib.error.HTTPError as error:
            self._send_upstream_error(error)
            return
        except Exception:
            self._send_json(502, UPSTREAM_ERROR)
            return
        if not valid_reranker_response(response):
            self._send_json(502, UPSTREAM_ERROR)
            return
        self._send_json(200, response)

    def _proxy_passthrough(self, upstream, body):
        url = upstream + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in STRIPPED_REQUEST_HEADERS}
        req = urllib.request.Request(url, data=body, headers=headers,
                                     method=self.command)
        try:
            resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        except urllib.error.HTTPError as e:
            self._send_upstream_error(e)
            return
        except Exception:
            self._send_json(502, UPSTREAM_ERROR)
            return

        with resp:
            self.send_response(resp.status)
            chunked = False
            for k, v in resp.headers.items():
                if k.lower() in HOP_BY_HOP or k.lower() == "content-length":
                    continue
                self.send_header(k, v)
            clen = resp.headers.get("Content-Length")
            if clen:
                self.send_header("Content-Length", clen)
            else:
                chunked = True
                self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                if chunked:
                    self.wfile.write(b"%X\r\n%s\r\n" % (len(chunk), chunk))
                else:
                    self.wfile.write(chunk)
                self.wfile.flush()      # SSE: deliver tokens as they arrive
            if chunked:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()

    def _dispatch(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        # ``/raw`` opts a caller out of width normalisation. Strip it before
        # anything else so the rest of the routing sees a normal path.
        raw = self.path.startswith(RAW_PREFIX + "/")
        if raw:
            self.path = self.path[len(RAW_PREFIX):]

        bp = base_path(self.path)
        if bp == "/health" and self.command == "GET":
            self._send_json(200, {"status": "ok"})
        elif bp in RESPONSES_PATHS and self.command == "POST":
            self._handle_responses(body)
        elif bp in EMBED_PATHS and self.command == "POST":
            self._handle_embeddings(body, 0 if raw else EMBED_PAD_DIM)
        elif bp in EMBED_PATHS:
            self._proxy_passthrough(EMBED_UPSTREAM, body)
        else:
            reranker_payload = None
            if bp == "/v1/chat/completions" and self.command == "POST":
                try:
                    candidate = json.loads(body or b"{}")
                except Exception:
                    candidate = None
                if is_graphiti_reranker_request(candidate):
                    reranker_payload = candidate
            if reranker_payload is not None:
                self._handle_reranker(reranker_payload)
            else:
                self._proxy_passthrough(CHAT_UPSTREAM, body)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _dispatch

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods",
                         "GET,POST,PUT,DELETE,PATCH,OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    srv = ThreadedServer((LISTEN_HOST, LISTEN_PORT), Handler)

    def request_shutdown(signum, _frame):
        """Stop cleanly when Docker sends SIGTERM to this PID 1 process."""
        sys.stderr.write("received signal %s; stopping router\n" % signum)
        sys.stderr.flush()
        # BaseServer.shutdown() must run outside the serve_forever() thread.
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    sys.stderr.write(startup_message())
    sys.stderr.flush()
    try:
        srv.serve_forever()
    finally:
        srv.server_close()
