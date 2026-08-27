# Validation record

The initial template was validated on 2026-08-13 against
`significantgravitas/autogpt:v0.7.1` and
`significantgravitas/autogpt:latest`. Both tags resolved to the multi-platform
index:

```text
sha256:4f8b92b8b0f144ae949893ea60e88c0aea74fdc4a8611338af53849495994754
```

## Host and runtime

- Native `linux/amd64` Unraid `7.2.3` host
- Isolated host port and dedicated Docker named volume at `/data`
- `2 GiB` shared memory
- `nofile=65536:65536`
- Defensive 360-second per-container stop allowance
- Image-provided Docker healthcheck and `/healthz`
- Observed steady-state memory: `5.542 GiB`

## Accepted flows

- Image pull, source-revision verification, first boot, and healthy state
- Microsoft Edge signup and onboarding
- Provider-free Builder run: Calculator `10 * 5 = 50`
- Save to Library and persistence across container recreation
- Marketplace route
- Actionable missing-provider behavior in the UI and authenticated chat API
- Administrator promotion with `autogpt-admin`
- Direct Docker stop with exit code 0 and no OOM kill
- Exact-address signup allowlist
- Closed-signup rejection with the identity count unchanged
- Logout and password login after registration was disabled
- Final healthy state with zero restarts and registration closed

## Exact template runtime contract

A separate non-destructive run on the same Unraid 7.2.3 host exercised the
template's exact default Docker contract:

- host port `3000` mapped to container port `3000`;
- bind mount `/mnt/user/appdata/autogpt:/data`;
- the template's restart policy, defensive 360-second per-container stop
  allowance, 2-GiB shared memory, `nofile=65536:65536`, and bounded JSON
  logging options; and
- exact `AUTOGPT_PUBLIC_URL`, signup allowlist, and open-first-account values.

The container reached healthy with zero restarts and `/healthz` returned `ok`.
A graceful stop exited `0` without an OOM kill. Recreating only that isolated
container against the same bind mount returned healthy again; the generated
runtime environment and PostgreSQL data predated the replacement and remained
mounted. Existing AutoGPT containers and their data were not modified.

## Native Docker Authoring Mode round trip

The template contract was also entered through Unraid 7.2.3 Docker Authoring
Mode and applied as the isolated `autogpt-ca-ui-test` container. To avoid
conflicting with existing workloads, this run used host port `3002` and
`/mnt/user/appdata/autogpt-ca-ui-test` while preserving container port `3000`
and the `/data` target.

Unraid saved and reopened the authored template with the expected image,
container shell, bind mount, host port, public URL, signup allowlist, and
registration setting. Runtime inspection confirmed the 2-GiB shared-memory
allocation, `nofile=65536:65536`, defensive 360-second per-container stop
allowance, restart policy, bounded JSON logging, and exact environment values.
The container reached healthy with zero restarts or OOM kills, and `/healthz`
returned `ok`.

The native Unraid **Stop** action then exposed a host-specific lifecycle gate.
The host's global **Docker Stop Timeout** was the default 10 seconds. Unraid's
Docker manager explicitly sent that value to the Engine, overriding the
container's stored 360-second timeout. AutoGPT received SIGTERM and began a
graceful shutdown, but Unraid forced termination after 10 seconds; the
container exited `137` with `OOMKilled=false`.

This result was a product acceptance failure, not an operator configuration
requirement. The host-wide timeout must not be increased as a workaround for
AutoGPT.

## Stock stop-timeout gate: fixed and re-verified

The defect was traced to the application image, not the template. Three causes
compounded: an unconfigured LaunchDarkly client raised out of the scheduler's
teardown so that process never exited; Supervisor stopped its programs one
group at a time, and with the default one-group-per-program layout the wedged
scheduler stranded every program behind it, including the databases; and the
per-program stop budget totalled far more than Docker's stock timeout, so the
overrun could not be observed in CI. The fix is
[Significant-Gravitas/AutoGPT#14077](https://github.com/Significant-Gravitas/AutoGPT/pull/14077).

Re-verified on 2026-08-20 on the same native `linux/amd64` Unraid `7.2.3` host,
with the host-wide **Docker Stop Timeout** left at its stock `10` seconds
(`DOCKER_TIMEOUT="10"`), using the template's own run arguments, container port
`3000`, and appdata on the host's cache pool:

| Run | Result |
| --- | --- |
| Previous image, native UI **Stop** (2026-08-14) | exit `137` |
| Fixed image, stop at the stock 10-second timeout | `4541 ms`, exit `0`, `OOMKilled=false` |
| Fixed image, stopped under a live database write load | `5064 ms`, exit `0`, `OOMKilled=false` |

Every bundled data store reported `exit status 0` in each run. Under load,
PostgreSQL completed its shutdown checkpoint — 15861 buffers, 96.8 % dirty — in
`2.297 s` and logged `database system is shut down`. Deleting the appdata
directory and starting again returned the container to healthy in `100 s`.

The appliance also now refuses to start if a previous database migration was
interrupted, naming the migration and the recovery, rather than failing with an
opaque migration trace on every subsequent boot. That path was exercised on
this host by injecting the interrupted state.

These stops were issued at the host's stock timeout — the same value Unraid's
Docker manager sends to the Engine — against a container running the template's
arguments. Repeating the stop through the Unraid UI's native **Stop** control on
a Docker Authoring Mode container remains part of the submission checklist, and
requires a published image containing the fix.

## Fully-local runtime proof

A live Unraid 7.x installation later exercised AutoGPT entirely through an
operator-run generation model and embedding model. The AutoGPT image carried
source revision `65e80c71591461d77b19fe64c939dd768ab455ef`. Endpoint addresses,
account data, and placeholder-key values are intentionally omitted.

The working topology used two independent llama.cpp upstreams behind one
AutoGPT-specific compatibility adapter running outside the tested AutoGPT
container:

- the normal `/v1` route forwarded chat to the generation server and embedding
requests to the Nomic server;
- `/v1/responses` requests were translated into schema-constrained chat
  completions for Graphiti;
- normal `/v1/embeddings` returned Nomic vectors padded from 768 to the 1536
  values required by unified search; and
- `/raw/v1/embeddings` returned the same model's native 768 values for the
  existing Graphiti graph.

Local transport always downgrades extended-thinking requests to the fast
OpenAI-compatible path. The published local fields therefore intentionally
omit `CHAT_THINKING_STANDARD_MODEL`; exposing it would imply a selectable local
thinking path that the runtime does not provide.

The accepted runtime evidence recorded for pull request 3 was:

- AutoGPT reached healthy in approximately 75 seconds;
- unified-search embedding backfill completed `5524/5524` items with zero
  failures;
- semantic search returned a relevant Discord result at `0.854` cosine for a
  Discord-message query;
- one Graphiti ingestion extracted 8 entities and 7 facts without a structured
  output validation error; and
- AutoPilot chat responded through the configured local generation model.

A later read-only inspection confirmed that the normal and raw embedding routes
returned 1536 and 768 values respectively, and recent chat-completion requests
through the adapter completed successfully. The generation and embedding
servers ran on separate ports and could therefore reside on the same inference
device without being inside the AutoGPT container.

This evidence proves the adapter behavior and the AutoGPT environment values.
It does **not** yet prove the derived one-container image or the published
fully-local XML: the accepted runtime used a host-local adapter script and
pre-existing container configuration. The derived image now embeds that same
adapter as an unprivileged Supervisor service, but still requires a fresh build,
one-container installation through current Unraid Docker Authoring Mode, a
save/reopen round trip, image-digest recording, clean-appdata acceptance, and
Community Applications Validate and Scan before release.

## Validation boundary

The browser/account acceptance run used an isolated port and named volume to
protect existing Unraid workloads. The separate contract run covers the
default bind path, port, arguments, health, graceful stop, and container
recreation. The native authoring run covers UI serialization and healthy
startup with isolated values, and it identified the global stop-timeout gate.
That gate has since been fixed in the product image and re-verified on this
host under stock Unraid settings; the remaining step is to repeat it through
the native UI control once an image carrying the fix is published. The
repository is now public. Docker Authoring Mode must still import each exact raw
template and pass the final rendered-card and saved-value checks. The derived
fully-local image retains the additional acceptance boundary described above.
Community Applications Validate and Scan must also pass on the exact public
commit and show exactly two AutoGPT listings.
