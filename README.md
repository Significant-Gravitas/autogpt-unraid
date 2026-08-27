# AutoGPT for Unraid

This repository contains the official AutoGPT Platform templates for
[Unraid Community Applications](https://unraid.net/community/apps). Both run
the complete Platform—including the web app, APIs, workers, PostgreSQL,
RabbitMQ, Valkey, and FalkorDB-backed memory. The hosted variant uses the
official [`significantgravitas/autogpt`](https://hub.docker.com/r/significantgravitas/autogpt)
image. The fully-local variant derives from that exact image and adds only a
small internal compatibility adapter; it does not change AutoGPT application
logic or bundle model weights.

The single-container distribution is experimental and intended for local and
small deployments. It is not a high-availability configuration.

## Choose a model setup

Install exactly one of two AutoGPT apps:

- **AutoGPT** is cloud/API-key-first. Enter an OpenRouter key for primary chat,
  memory extraction, and the default remote search route, plus an OpenAI key
  for Graphiti memory embeddings. Those providers host the models; AutoGPT
  does not.
- **AutoGPT Fully Local** is one Community Apps installation for models you
  operate. Its AutoGPT image contains the private compatibility adapter. You
  enter two model-server origins and three exact generation-model IDs; no
  hosted-provider key is required for AutoPilot, Graphiti, or unified search.

The Fully Local app does not run the models. Before installing it, run one
chat-capable llama.cpp process and one Nomic embedding-only llama.cpp process
on this Unraid host or another trusted device. Both can share one device, but
they need separate processes and ports because llama.cpp's embedding-only mode
does not also serve chat. The local profile supports unauthenticated endpoints
on a trusted LAN or VPN; authenticated hosted providers belong in the regular
AutoGPT app.

The profiles are separate because a blank Unraid template variable is still
passed to Docker as an empty environment variable. Putting optional local and
hosted fields in one large form can therefore override AutoGPT's defaults even
when a user leaves them blank.

Credentials selected inside individual agent blocks are independent of both
paths. A local AutoPilot configuration does not automatically replace a block's
OpenAI or other provider credential.

For the complete local topology, model-host requirements, field-by-field
examples, and local-versus-hosted variable table, see
[AutoGPT Fully Local on Unraid](docs/fully-local.md).

## Install

After the template is listed in Community Applications, open **Apps**, search
for **AutoGPT**, and select the template maintained by **Significant Gravitas**.
Before catalog listing, maintainers can install either raw template URL through
Unraid Docker Authoring Mode:

```text
https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/templates/autogpt.xml
https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/templates/autogpt-local.xml
```

Before starting the container:

1. Set **Public URL** to the exact origin you will use in the browser, including
   the selected host port—for example, `http://192.168.1.10:3000`.
2. Set **First Account Email** to the exact email address that should create the
   initial account.
3. Keep **Allow New Accounts** set to `true` for the first signup.
4. Keep the default appdata path unless you have an established Unraid storage
   convention.

For the hosted variant, paste the two masked API keys. For the fully-local
variant, follow each field's example for the chat origin, embedding origin, and
model IDs. Its adapter is already inside the AutoGPT image; there is no router
app or router port to install. No Unraid terminal command is required.

Start the container and wait for Docker to report `healthy`. First boot can
take several minutes.

Unraid's **WebUI** shortcut always opens the server IP with the configured host
port over HTTP. If **Public URL** uses a hostname, HTTPS, or a reverse proxy,
open that configured URL directly instead; authentication requires the browser
origin to match **Public URL** exactly.

## Secure the first account

Create the account using the exact email address configured in the template.
On the Unraid Docker page, open the AutoGPT container's **Console**, then
promote it to administrator:

```text
autogpt-admin promote you@example.com
```

Edit the container, set **Allow New Accounts** to `false`, and apply the change.
Complete these steps before exposing AutoGPT beyond the trusted local network.
Use HTTPS for any remote or LAN-wide deployment.

## Resources and persistence

- Web interface: container port `3000`
- Persistent state: `/data`, mapped to `/mnt/user/appdata/autogpt` by the base
  template or `/mnt/user/appdata/autogpt-local` by the fully local template
- Shared memory: `2 GiB`
- Open-file limit: `65536`
- Defensive per-container stop allowance: `360 seconds` for Docker runtimes
  that honor it. It does not require or replace an Unraid host-wide setting.
- Observed memory use: approximately `5–6 GiB`; leave additional headroom for
  Unraid and other applications

The `/data` mapping contains accounts, agents, databases, memory, workspaces,
and generated secrets. Preserve it across updates and container recreation.

The hosted template supplies the two platform-level keys used by its default
chat, memory, and search paths. The fully-local template supplies their local
transport instead. Credentials selected inside individual agent blocks remain
independent in both apps.

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
official base image's runtime contract and pass `scripts/validate.sh` before release.
Maintainers should also complete the
[release checklist](docs/release-checklist.md) for every catalog submission or
material template update.

## License

The template source and documentation are licensed under the
[MIT License](LICENSE). The AutoGPT name and logo remain Significant Gravitas
brand assets; the MIT license does not grant trademark rights. See
[BRANDING.md](BRANDING.md).

The official and derived images label the AutoGPT bundle as
`LicenseRef-PolyForm-Shield-1.0.0 AND SSPL-1.0`. AutoGPT Platform is distributed
under the [PolyForm Shield License 1.0.0](https://github.com/Significant-Gravitas/AutoGPT/blob/master/LICENSE),
and the bundled components remain under their respective licenses. The local
adapter source in this repository is MIT-licensed.
