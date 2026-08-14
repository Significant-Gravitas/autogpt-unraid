# Validation record

The initial template was validated on 2026-08-13 against
`significantgravitas/autogpt:v0.7.1` and
`significantgravitas/autogpt:latest`. Both tags resolved to the multi-platform
index:

```text
sha256:4f8b92b8b0f144ae949893ea60e88c0aea74fdc4a8611338af53849495994754
```

## Host and runtime

- Native `linux/amd64` Unraid host
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

## Validation boundary

This acceptance run used an isolated port and named volume to protect existing
Unraid workloads. Release acceptance additionally covers the exact template
defaults—`/mnt/user/appdata/autogpt:/data`, host port `3000`, Docker Authoring
Mode save/reopen behavior, Community Applications Validate and Scan, and
persistence after a template-driven recreation.
