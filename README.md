# AutoGPT for Unraid

This repository contains the official Unraid Community Applications template
for [AutoGPT Platform](https://github.com/Significant-Gravitas/AutoGPT).
AutoGPT Platform is distributed under PolyForm Shield 1.0.0; the template
repository itself is MIT-licensed.

The template follows verified stable releases from
[`significantgravitas/autogpt:latest`](https://hub.docker.com/r/significantgravitas/autogpt).
The initial submission was validated against `v0.7.1`, whose multi-platform
index digest is
`sha256:4f8b92b8b0f144ae949893ea60e88c0aea74fdc4a8611338af53849495994754`.

## Before submitting to Community Applications

1. Create the permanent `Significant-Gravitas/autogpt-unraid` repository.
2. Create the required Unraid forum support thread.
3. Replace `REPLACE_WITH_UNRAID_SUPPORT_THREAD_URL` in
   `templates/autogpt.xml`.
4. Confirm GitHub and Docker Hub 2FA for the Community Applications form.
5. Run `scripts/validate.sh` and test the template on current Unraid.
6. Submit this repository using the official Community Applications intake
   form.

The native release-image results are recorded in
[`submission/acceptance-report.md`](submission/acceptance-report.md).

## Runtime notes

- The web UI is on container port `3000`.
- All persistent data is stored under `/data`.
- The image includes its own Docker healthcheck. The lightweight liveness URL
  is `/healthz`; wait for Docker to report `healthy` before using the app.
- First boot can take several minutes and observed memory use is about 5-6 GiB.
- This is an experimental single-node distribution for local and small
  deployments, not a high-availability configuration. Leave additional memory
  headroom for Unraid and other applications.
- `AUTOGPT_PUBLIC_URL` must exactly match the browser-visible origin.
- Registration begins open but is restricted by the exact email entered in the
  template. After creating the account, promote it with:

  ```bash
  docker exec AutoGPT autogpt-admin promote you@example.com
  ```

  Then edit the container and set `AUTH_ALLOW_NEW_ACCOUNTS=false`.
- Model-provider credentials are optional for startup and provider-free blocks.
  Provider-backed features report the normal missing-credential error until
  configured.

For complete configuration and operations guidance, see the
[Docker Hub Overview](https://hub.docker.com/r/significantgravitas/autogpt).

## Validation

```bash
scripts/validate.sh
```

The validator checks XML syntax, required local assets, selected static runtime
fields, and submission placeholders. Live image, raw-URL, Community Apps scan,
and Docker Authoring Mode checks are separate release steps. The final
Authoring Mode round-trip must be completed manually in Unraid because that UI
writes to the boot-device configuration.
