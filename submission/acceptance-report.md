# Unraid acceptance report

Validated 2026-08-13 against `significantgravitas/autogpt:v0.7.1` and
`significantgravitas/autogpt:latest`, both resolving to multi-platform index
`sha256:4f8b92b8b0f144ae949893ea60e88c0aea74fdc4a8611338af53849495994754`.

## Host and runtime

- Native `linux/amd64` Unraid host
- Isolated host port and dedicated Docker named volume at `/data`
- 2 GiB shared memory
- `nofile=65536:65536`
- 360-second graceful stop timeout
- Built-in Docker healthcheck and `/healthz`
- Observed steady-state memory: 5.542 GiB

## Passed flows

- Image pull, source-revision verification, first boot, and healthy state
- Microsoft Edge signup and onboarding
- Real provider-free Builder run: Calculator `10 * 5 = 50`
- Save to Library and persistence across container replacement
- Marketplace route
- Missing-provider behavior in the UI and authenticated chat API
- Administrator promotion with `autogpt-admin`
- Graceful stop with exit code 0 and no OOM kill
- Exact-address signup allowlist
- Closed-signup rejection with the identity count unchanged
- Logout and password login after registration was disabled
- Final state healthy with zero restarts and registration closed

## Submission-only check still required

The Community Applications template defaults to the Unraid appdata bind
`/mnt/user/appdata/autogpt:/data` and port 3000. The final maintainer must install
the published template through Docker Authoring Mode, perform a Validate and
Scan pass, and verify persistence across a template-driven recreate. The live
acceptance run deliberately used an isolated port and named volume so it could
not alter an existing appdata share or container.
