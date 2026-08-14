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
- 360-second graceful stop timeout
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
- Graceful stop with exit code 0 and no OOM kill
- Exact-address signup allowlist
- Closed-signup rejection with the identity count unchanged
- Logout and password login after registration was disabled
- Final healthy state with zero restarts and registration closed

## Exact template runtime contract

A separate non-destructive run on the same Unraid 7.2.3 host exercised the
template's exact default Docker contract:

- host port `3000` mapped to container port `3000`;
- bind mount `/mnt/user/appdata/autogpt:/data`;
- the template's restart policy, 360-second stop timeout, 2-GiB shared memory,
  `nofile=65536:65536`, and bounded JSON logging options; and
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
allocation, `nofile=65536:65536`, 360-second container stop timeout, restart
policy, bounded JSON logging, and exact environment values. The container
reached healthy with zero restarts or OOM kills, and `/healthz` returned `ok`.

The native Unraid **Stop** action then exposed a host-specific lifecycle gate.
The host's global **Docker Stop Timeout** was the default 10 seconds. Unraid's
Docker manager explicitly sent that value to the Engine, overriding the
container's stored 360-second timeout. AutoGPT received SIGTERM and began a
graceful shutdown, but Unraid forced termination after 10 seconds; the
container exited `137` with `OOMKilled=false`.

The test container, saved template, and appdata remain preserved and stopped.
Before submission, set **Settings → Docker → Docker Stop Timeout** to at least
360 seconds, repeat the native UI stop, and require exit code `0`. The setting
is global to the Unraid host and was deliberately not changed during this test.

## Validation boundary

The browser/account acceptance run used an isolated port and named volume to
protect existing Unraid workloads. The separate contract run covers the
default bind path, port, arguments, health, graceful stop, and container
recreation. The native authoring run covers UI serialization and healthy
startup with isolated values, and it identified the global stop-timeout gate.
The repository is now public. Docker Authoring Mode must still import the exact
raw template and pass the final rendered-card check. Community Applications
Validate and Scan must also pass on the exact public commit.
