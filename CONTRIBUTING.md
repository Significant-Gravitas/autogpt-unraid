# Contributing

Thank you for helping improve the official AutoGPT templates and fully-local
image overlay for Unraid.

## Scope

This repository owns the Unraid templates, their catalog metadata, and the
small AutoGPT-specific compatibility adapter embedded by the fully-local image.
AutoGPT product changes belong in the
[AutoGPT repository](https://github.com/Significant-Gravitas/AutoGPT).

The hosted template must continue to use `significantgravitas/autogpt`. The
fully-local image must derive from the pinned official digest without changing
its entrypoint, command, root bootstrap, or application code. Both preserve:

- persistent `/data` storage;
- container port `3000`;
- `2 GiB` shared memory;
- `nofile=65536:65536`;
- a defensive per-container `360`-second stop allowance, without treating it
  as a substitute for clean shutdown through stock Unraid UI behavior;
- the image-provided health probes (the local image composes its upstream
  checks around them); and
- exact `AUTOGPT_PUBLIC_URL`, `AUTH_SIGNUP_ALLOWLIST`, and
  `AUTH_ALLOW_NEW_ACCOUNTS` behavior.

The fully-local template and embedded adapter must also preserve this contract:

- local chat uses the adapter's private normal `/v1` route;
- Graphiti memory embeddings use `/raw/v1` and retain Nomic's native
  768-dimensional vectors;
- unified search uses the normal `/v1/embeddings` route and receives exactly
  1536 values;
- the adapter trims Nomic inputs to its verified 2048-token window;
- the adapter translates Graphiti's structured Responses API calls to a
  schema-constrained chat-completions request;
- `CHAT_UPSTREAM` and `EMBED_UPSTREAM` remain independent so a chat-capable
  and an embedding-only llama.cpp server can run on separate ports;
- both upstreams provide unauthenticated `/health` endpoints and the adapter
  strips inbound `Authorization` rather than partially forwarding credentials;
- `host.docker.internal` resolves in the AutoGPT container so inference may
  run directly on the Unraid host as well as another trusted device;
- the adapter binds only `127.0.0.1:8098`, is not exposed or published, joins
  Supervisor's existing `runtime` group, and appears in the inherited required
  process list;
- its process runs as the dedicated unprivileged `autogpt-local-adapter` user
  with a scrubbed environment and no-new-privileges; and
- `CHAT_THINKING_STANDARD_MODEL` is deliberately not exposed. Local transport
  always downgrades extended thinking to the fast OpenAI-compatible path, so a
  field for that variable would imply functionality that does not exist.

The adapter is a compatibility layer, not an inference server. Do not add model
weights, model downloads, privileged access, or persistent user data to the
derived image. Keep adapter source root-owned and non-writable, retain
no-new-privileges, and handle Supervisor SIGTERM within its one-second runtime
stop tier. Keep its listener and upstream contract unauthenticated for
trusted-network use, and do not describe it as safe to expose to the internet. Adding
credentialed upstreams requires a complete authentication design across every
translated and passthrough route; do not forward only a subset.

The hosted template deliberately exposes only its two complete-profile keys
plus fixed transport selectors. Do not reintroduce optional blank local fields:
Unraid passes them as empty environment variables and can override working
AutoGPT defaults.

Do not add provider credentials, generated secrets, host-specific paths, or
private acceptance data to the repository. Examples must use documentation
addresses and non-secret placeholders. Redact endpoint hostnames, personal
email addresses, bearer tokens, prompt contents, and webhook URLs from
validation records and issues.

## Validate a change

Install `file` and Python 3, then run:

```bash
scripts/validate.sh
```

The script validates exactly two published XML files, enforces the hosted and
fully-local contracts, tests the adapter and guarded image overlay, and checks
that no standalone router template or port is published. Image changes must
also keep `local-image/Dockerfile` buildable and its composite healthcheck
functional.

For a release-affecting change, also install the template through current
Unraid Docker Authoring Mode on a fresh appdata path, wait for healthy state,
and verify account bootstrap, signup closure, persistence after recreation,
and normal update behavior.

Changes to the fully-local path additionally require a no-terminal UI round
trip of its single template and live verification of:

- streamed chat and tool calls through the generation upstream;
- a schema-constrained Graphiti extraction request;
- 1536 values from `/v1/embeddings` and native 768 values from
  `/raw/v1/embeddings`;
- a zero-failure unified-search backfill and a useful semantic-search result;
- Graphiti memory ingestion and retrieval; and
- clean restart, recreation, and stock-timeout stop behavior.

Use fresh AutoGPT appdata for acceptance unless the test is specifically a
migration or compatibility check. FalkorDB fixes a graph's embedding width at
creation, so changing a live graph's model or width is not a valid shortcut.

## Pull requests

Keep pull requests focused, explain the operator-facing impact, and include the
Unraid version, official base digest, derived image digest, and validation
evidence. Distinguish automated adapter tests from live Unraid acceptance; do
not claim a packaged image or raw Community Applications template was tested
when only a host-local prototype was exercised. Do not change an image
repository, publish an image, or weaken the security defaults without approval
from the AutoGPT maintainers.
