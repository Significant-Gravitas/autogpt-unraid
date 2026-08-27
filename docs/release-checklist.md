# Release checklist

Use this checklist for every Community Applications submission or material
template or image update. Do not publish a revision that has not completed each
applicable check.

## Repository and automated validation

- [ ] The root MIT license, `ca_profile.xml`, approved icon, and exactly two
      published template XML files are present.
- [ ] `scripts/validate.sh`, adapter unit tests, overlay unit tests, shellcheck,
      XML parsing, and whitespace checks pass on the exact release commit.
- [ ] No credentials, endpoint addresses, personal data, generated secrets,
      internal test candidates, or unresolved placeholders are committed.
- [ ] Private vulnerability reporting is enabled for the repository.
- [ ] Every support, project, registry, readme, template, and icon URL returns
      HTTP 200 to a signed-out client.
- [ ] Community Applications **Validate** and **Scan** pass after the final XML
      change and report exactly the two intended AutoGPT listings.

## Official and derived images

- [ ] Record the official `significantgravitas/autogpt` multi-platform index
      digest and source revision.
- [ ] The digest pinned in `local-image/Dockerfile` is the exact official image
      exercised during this release.
- [ ] Build the fully-local image from a clean checkout for `linux/amd64` and
      `linux/arm64`.
- [ ] Confirm the derived image preserves the official root user, entrypoint,
      command, port 3000, `/data` contract, stop signal, and root bootstrap.
- [ ] Confirm it publishes no port 8098 and adds no persistent model or adapter
      data path.
- [ ] Confirm the adapter source is root-owned and non-writable, runs as UID
      10007 with no-new-privileges and a scrubbed environment, joins the
      existing Supervisor `runtime` group, and appears in the required process
      health list.
- [ ] Confirm the composite healthcheck first runs every inherited AutoGPT
      probe, then checks the loopback adapter and both configured model servers.
- [ ] Publish the derived image to
      `ghcr.io/significant-gravitas/autogpt-unraid-local` and record its digest.
- [ ] From a signed-out client, pull both architectures and confirm the GHCR
      package is public before the local template is submitted.
- [ ] Stop the container under Unraid's stock 10-second global timeout and
      confirm exit code 0 with no OOM kill. Do not increase the host-wide
      timeout as a workaround.

## Hosted/API-key-first app

- [ ] Import the exact raw `templates/autogpt.xml` URL through current Unraid
      Docker Authoring Mode on fresh appdata.
- [ ] Save, close, and reopen the form. Confirm the five common fields, two
      masked API-key fields, and two advanced transport selectors were
      preserved exactly.
- [ ] Confirm the image is `significantgravitas/autogpt:latest`, `/data` maps to
      `/mnt/user/appdata/autogpt`, and no local endpoint or model field appears.
- [ ] With valid OpenRouter and OpenAI keys, verify streamed AutoPilot chat,
      Graphiti ingestion/retrieval, and unified search.
- [ ] Confirm the UI explains that the providers, not AutoGPT, host the models
      and that individual agent-block credentials remain separate.

## Fully-local app and adapter

- [ ] Run one real chat-capable llama.cpp process and one real Nomic
      embedding-only llama.cpp process. Verify both `/health` endpoints return
      HTTP 200 JSON with status `ok`.
- [ ] Import the exact raw `templates/autogpt-local.xml` URL through current
      Docker Authoring Mode on fresh `/mnt/user/appdata/autogpt-local` data.
- [ ] Save, close, and reopen the form. Confirm the five common fields, two
      origins, three model-ID fields, host-gateway mapping, and standard AutoGPT
      runtime arguments were preserved.
- [ ] Confirm no companion router app, host port 8098, hosted key, internal URL,
      placeholder key, or embedding plumbing field is rendered.
- [ ] Confirm missing values, `/v1` paths, URL credentials, and container
      loopback origins fail with clear redacted configuration errors.
- [ ] Confirm a schema-constrained `/v1/responses` request succeeds through the
      adapter's chat-completions translation.
- [ ] Confirm `/v1/embeddings` returns exactly 1536 values and
      `/raw/v1/embeddings` returns exactly 768 values for the same Nomic model.
- [ ] Confirm input beyond the 2048-token Nomic window is trimmed through the
      upstream tokenizer and embeds successfully.
- [ ] Complete an AutoPilot turn with streamed output and a tool call.
- [ ] Complete Graphiti ingestion and retrieval without structured-output or
      vector-width errors.
- [ ] Exercise the Graphiti reranker with known relevant and irrelevant facts;
      confirm biased top tokens are `True`/`False` for the selected tokenizer
      and the final ordering is semantically correct.
- [ ] Complete unified-search backfill with zero failures and verify a relevant
      semantic-search result.
- [ ] Confirm unavailable upstreams make the one AutoGPT container unhealthy
      without leaking request bodies, keys, or private origins.
- [ ] Restart and recreate the single app through the Unraid UI. Confirm
      AutoGPT data persists, the adapter recovers, and vector widths do not
      change silently.
- [ ] Confirm both external inference ports stay on a trusted LAN or private VPN
      and are not represented as providing TLS or authentication.

## Account, lifecycle, and presentation

- [ ] For each variant, complete initial signup, promote the allowlisted account
      from the container Console, set **Allow New Accounts** to `false`, and
      confirm another signup is rejected.
- [ ] Verify `/healthz`, persistence across recreation, update, and rollback
      without deleting appdata.
- [ ] Review both Community Applications cards, descriptions, settings,
      category, beta marker, icon, Web UI link, and support link.
- [ ] Confirm the listing makes the boundary explicit: hosted providers run
      remote models; Fully Local is one AutoGPT installation but still requires
      two operator-run model processes.
- [ ] Submit the exact tested commit only after the referenced derived image is
      public. Record the commit, both image digests, date, submission reference,
      and moderator follow-up in the private release record.
