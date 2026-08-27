# AutoGPT Fully Local on Unraid

**AutoGPT Fully Local** is one Community Apps installation for AutoPilot chat,
Graphiti memory, and unified search through models you operate. The AutoGPT
container includes a small internal compatibility adapter. It does not include
model weights or an inference runtime, and it does not require an OpenRouter,
OpenAI, or Anthropic key for those three platform features.

Use the regular **AutoGPT** app when a hosted provider runs your models. Use
**AutoGPT Fully Local** when you operate the model endpoints yourself on this
Unraid host, another trusted-LAN computer, or a device reachable through a
private VPN. Do not mix the two profiles or copy hosted API keys into the local
form.

## What runs where

```text
AutoGPT Fully Local container
  |-- AutoGPT Platform and persistent /data
  `-- private adapter at 127.0.0.1:8098
       |-- chat and structured output --> llama.cpp chat process
       `-- memory/search embeddings   --> llama.cpp Nomic process
```

Only the AutoGPT web port is published. Port `8098` stays on container
loopback, has no Unraid form field, and cannot be reached from the network.

The two llama.cpp processes can run on the same physical device. They still
need separate ports because a llama.cpp server started in embedding-only mode
does not also serve chat. Both origins are required.

## Model-server requirements

Prepare these before installing AutoGPT Fully Local:

1. A chat-capable llama.cpp server whose `/health` endpoint returns HTTP 200
   JSON with `{"status":"ok"}`. The generation model must support streamed
   chat completions, tool calls, schema-constrained JSON output, reranker log
   probabilities, and at least 24k context; 32k is recommended. Reranker
   acceptance must also verify that its tokenizer produces `True` or `False`
   as the biased top token rather than merely returning HTTP 200.
2. A separate llama.cpp embedding server for `nomic-embed-text`. It must return
   the same health response and expose `/tokenize`, `/detokenize`, and
   `/v1/embeddings`. This accepted profile uses native 768-value vectors and a
   verified 2048-token ceiling.
3. Enough inference compute in addition to AutoGPT's approximately 5–6 GiB of
   observed memory use. Model RAM, VRAM, and disk belong to the device running
   llama.cpp; the AutoGPT image does not download or load models.

Use the origin only in the Unraid fields—scheme, host, and port, with no `/v1`.
For model servers running directly on this Unraid host, use
`host.docker.internal`, not `localhost`. For another device, use its trusted
LAN or private-VPN address.

Examples for two processes on this Unraid host:

```text
Chat Server Origin:      http://host.docker.internal:8099
Embedding Server Origin: http://host.docker.internal:8100
```

Examples for two processes on another device:

```text
Chat Server Origin:      http://192.168.1.42:8099
Embedding Server Origin: http://192.168.1.42:8100
```

## Install through the Unraid UI

1. In **Apps**, install **AutoGPT Fully Local** maintained by Significant
   Gravitas.
2. Set **Public URL** to the exact origin you will open in the browser, such as
   `http://192.168.1.10:3000`.
3. Enter **First Account Email** and leave **Allow New Accounts** set to `true`
   for initial signup.
4. Enter both model-server origins using the examples above.
5. Copy the exact generation model ID reported by the chat server into all
   three model fields. For example: `ornith-1.5-9b`.
6. Apply the template and wait for the single AutoGPT container to become
   healthy. No Unraid terminal command and no companion router app are needed.
7. Create the first account, open the container's **Console**, and run
   `autogpt-admin promote you@example.com`. Then edit the app, set
   **Allow New Accounts** to `false`, and apply the change.

The image validates all five model inputs. A missing value, a URL containing
`/v1`, embedded credentials, or a container-loopback address produces a clear
`local-model configuration error` in the AutoGPT container log instead of
silently routing to the wrong place.

## Which variables belong to which app

| Setting | AutoGPT hosted app | AutoGPT Fully Local app |
|---|---|---|
| `OPEN_ROUTER_API_KEY` | Set it; example format `sk-or-v1-...` | Do not set it |
| `OPENAI_API_KEY` | Set it for default Graphiti embeddings; example format `sk-proj-...` | Do not set it |
| `CHAT_UPSTREAM` | Do not set it | Required chat origin; example `http://host.docker.internal:8099` |
| `EMBED_UPSTREAM` | Do not set it | Required embedding origin; example `http://host.docker.internal:8100` |
| Three generation-model fields | Use AutoGPT's hosted defaults | Required exact IDs; example `ornith-1.5-9b` in each field |

The Fully Local image sets the internal transport variables itself:

- chat and Graphiti LLM traffic use the adapter's private `/v1` route;
- Graphiti embeddings use `/raw/v1` and retain Nomic's native 768 values;
- unified-search embeddings use `/v1/embeddings` and are zero-padded to the
  required 1536 values; and
- embedding inputs are trimmed with the model server's tokenizer to the
  verified 2048-token window; and
- Graphiti reranker requests replace OpenAI-specific True/False token IDs with
  IDs discovered from the selected llama.cpp tokenizer, disable thinking for
  that classifier call, and fail closed unless selected and scored labels
  agree.

These internal values are intentionally absent from the Unraid form. They are
implementation plumbing, not operator choices. The image also validates their
effective values at startup, so a legacy or hand-added Docker environment
override fails clearly instead of silently bypassing the adapter.

Credentials chosen inside an individual agent block are separate from the
platform profile. A block that explicitly uses a hosted integration may still
ask for that integration's credential even when AutoPilot is fully local.

## Existing data and vector widths

Keep the default `/mnt/user/appdata/autogpt-local` path separate from a hosted
installation. FalkorDB fixes a Graphiti graph's vector width when the graph is
created, and PostgreSQL unified search expects 1536 values. Do not point this
profile at appdata created with a different Graphiti embedding model or width
unless you have performed a deliberate migration.

## Health and troubleshooting

The single Docker health state covers AutoGPT, the internal adapter, and both
model upstreams.

- **`CHAT_UPSTREAM is required` or another configuration error:** edit the
  AutoGPT Fully Local app and complete every required model field.
- **Origin must be without `/v1`:** enter only the scheme, host, and port; the
  adapter adds the API paths.
- **Loopback address rejected:** `localhost` and `127.0.0.1` refer to the
  AutoGPT container. Use `host.docker.internal` for llama.cpp on Unraid.
- **Container stays unhealthy:** confirm each model server's `/health` route
  independently, then inspect the AutoGPT container log. The health output
  identifies chat versus embeddings without printing private origins.
- **Graphiti extraction fails:** verify the chat model reliably obeys strict
  JSON schemas through chat completions.
- **Memory ranking looks wrong:** a successful log-probability response alone
  is insufficient. Confirm the reranker response's top token is `True` or
  `False` for the selected model and tokenizer.
- **Memory works but search fails:** verify Nomic emits 768 values. The adapter
  keeps that width for Graphiti and pads only unified-search traffic to 1536.
- **Search works but long documents fail:** verify the embedding process
  exposes `/tokenize` and `/detokenize`; the adapter uses both for safe
  trimming.

The accepted profile covers AutoPilot chat, Graphiti memory, and unified
search. Optional product paths that explicitly require an Ollama-native
`/api/chat` endpoint are not provided by llama.cpp through this adapter. Do not
enable such an optional path unless its endpoint contract is supported.

## Security boundary

The internal adapter binds only to container loopback and runs under a
dedicated unprivileged account with a scrubbed environment. Its source is
root-owned and non-writable. It intentionally strips inbound authorization and
does not add authentication or TLS to the llama.cpp upstreams.

Keep both model-server ports restricted to a trusted LAN or private VPN. Do not
publish them to the internet. Authenticated remote model services belong in the
hosted AutoGPT profile unless a complete authentication-aware gateway is
placed in front of them.
