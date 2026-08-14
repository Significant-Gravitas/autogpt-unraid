# AutoGPT for Unraid

This repository contains the official Unraid Community Applications template
for [AutoGPT Platform](https://github.com/Significant-Gravitas/AutoGPT). It runs
the complete Platform—including the web app, APIs, workers, PostgreSQL,
RabbitMQ, Valkey, and FalkorDB-backed memory—from the official
[`significantgravitas/autogpt`](https://hub.docker.com/r/significantgravitas/autogpt)
image.

The single-container distribution is experimental and intended for local and
small deployments. It is not a high-availability configuration.

## Install

After the template is listed in Community Applications, open **Apps**, search
for **AutoGPT**, and select the template maintained by **Significant Gravitas**.
Before catalog listing, maintainers can install the raw template URL through
Unraid Docker Authoring Mode.

Before starting the container:

1. Set **Public URL** to the exact origin you will use in the browser, including
   the selected host port—for example, `http://tower.local:3000`.
2. Set **First Account Email** to the exact email address that should create the
   initial account.
3. Keep **Allow New Accounts** set to `true` for the first signup.
4. Keep the default appdata path unless you have an established Unraid storage
   convention.

Start the container and wait for Docker to report `healthy`. First boot can
take several minutes.

## Secure the first account

Create the account using the exact email address configured in the template,
then promote it to administrator:

```bash
docker exec AutoGPT autogpt-admin promote you@example.com
```

Edit the container, set **Allow New Accounts** to `false`, and apply the change.
Complete these steps before exposing AutoGPT beyond the trusted local network.
Use HTTPS for any remote or LAN-wide deployment.

## Resources and persistence

- Web interface: container port `3000`
- Persistent state: `/data`, mapped to `/mnt/user/appdata/autogpt` by default
- Shared memory: `2 GiB`
- Open-file limit: `65536`
- Graceful stop timeout: `360 seconds`
- Observed memory use: approximately `5–6 GiB`; leave additional headroom for
  Unraid and other applications

The `/data` mapping contains accounts, agents, databases, memory, workspaces,
and generated secrets. Preserve it across updates and container recreation.

Model-provider credentials are optional for startup and provider-free blocks.
Provider-backed features return an actionable missing-credential error until a
compatible key or local provider is configured.

## Documentation and support

- [Single-container operator guide](https://docs.agpt.co/platform/self-hosting/single-container)
- [AutoGPT documentation](https://docs.agpt.co/)
- [Template issues](https://github.com/Significant-Gravitas/autogpt-unraid/issues)
- [AutoGPT product issues](https://github.com/Significant-Gravitas/AutoGPT/issues)

When requesting help, include your Unraid version, the image tag, Docker health
state, relevant logs with secrets removed, and whether the issue reproduces on
a fresh appdata path.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Template changes must preserve the
official image's runtime contract and pass `scripts/validate.sh` before release.
Maintainers should also complete the
[release checklist](docs/release-checklist.md) for every catalog submission or
material template update.

## License

The files in this template repository are licensed under the [MIT License](LICENSE).
AutoGPT Platform itself is distributed under the
[PolyForm Shield License 1.0.0](https://github.com/Significant-Gravitas/AutoGPT/blob/master/LICENSE).
