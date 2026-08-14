# AutoGPT for Unraid

This repository contains the official AutoGPT Platform template for
[Unraid Community Applications](https://unraid.net/community/apps). It runs
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
Unraid Docker Authoring Mode:

```text
https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/templates/autogpt.xml
```

Before starting the container:

1. Set **Public URL** to the exact origin you will use in the browser, including
   the selected host port—for example, `http://192.168.1.10:3000`.
2. Set **First Account Email** to the exact email address that should create the
   initial account.
3. Keep **Allow New Accounts** set to `true` for the first signup.
4. Keep the default appdata path unless you have an established Unraid storage
   convention.
5. In **Settings → Docker**, set **Docker Stop Timeout** to at least `360`
   seconds before stopping AutoGPT through Unraid. This is a global Unraid
   setting, so review its effect on your other containers.

Start the container and wait for Docker to report `healthy`. First boot can
take several minutes.

Unraid's **WebUI** shortcut always opens the server IP with the configured host
port over HTTP. If **Public URL** uses a hostname, HTTPS, or a reverse proxy,
open that configured URL directly instead; authentication requires the browser
origin to match **Public URL** exactly.

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
- Graceful stop timeout: `360 seconds`. Unraid's Docker manager sends its
  global **Docker Stop Timeout** explicitly, so that global setting must also
  be at least `360` seconds for UI-managed stops.
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

The template source and documentation are licensed under the
[MIT License](LICENSE). The AutoGPT name and logo remain Significant Gravitas
brand assets; the MIT license does not grant trademark rights. See
[BRANDING.md](BRANDING.md).

The published image labels its bundled software as
`LicenseRef-PolyForm-Shield-1.0.0 AND SSPL-1.0`. AutoGPT Platform is distributed
under the [PolyForm Shield License 1.0.0](https://github.com/Significant-Gravitas/AutoGPT/blob/master/LICENSE),
and bundled components remain under their respective licenses.
