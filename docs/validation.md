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

## Validation boundary

The browser/account acceptance run used an isolated port and named volume to
protect existing Unraid workloads. The separate contract run above covers the
default bind path, port, arguments, health, graceful stop, and container
recreation, but it was deliberately launched without writing Unraid's protected
configuration. Before publication, Docker Authoring Mode must still import the
exact template and pass save/close/reopen and rendered-card checks. Community
Applications Validate and Scan must also pass on the exact public commit.
