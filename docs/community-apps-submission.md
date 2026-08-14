# Community Applications submission copy

This page is the prepared maintainer copy for the final Community Applications
submission. Reconfirm all facts immediately before submitting.

## Repository

- Repository: `https://github.com/Significant-Gravitas/autogpt-unraid`
- Template: `https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/templates/autogpt.xml`
- Profile: `https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/ca_profile.xml`
- Icon: `https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/images/autogpt.png`
- Image: `significantgravitas/autogpt:latest`
- Publisher: `Significant Gravitas`
- Application: `AutoGPT`
- Architectures published by the image: `amd64`, `arm64`
- Template repository license: `MIT`
- AutoGPT Platform license: `PolyForm Shield License 1.0.0`

## Short description

Run the complete AutoGPT Platform as one persistent, health-checked container
for local and small Unraid deployments.

## Reviewer note

This template is maintained by the AutoGPT project and uses its official Docker
Hub image. The container bundles the Platform web application, APIs, workers,
PostgreSQL, RabbitMQ, Valkey, and FalkorDB-backed memory behind one published
port. It runs unprivileged in bridge networking and persists all application
state under `/data`.

Native amd64 acceptance covered first boot, account creation and promotion,
registration closure, a real provider-free Builder run, persistence after
container recreation, actionable missing-provider behavior, clean shutdown,
and password relogin. The published release pipeline builds, smoke-tests, and
scans native amd64 and arm64 images, then pulls and retests the exact registry
digests before publishing the multi-platform manifest.

The distribution is marked beta because the one-container deployment remains
experimental and is intended for local and small deployments rather than high
availability. First boot and steady state have used approximately 5–6 GiB of
memory, so the template prominently asks operators to leave additional
headroom.

## Attestations to confirm at send time

- GitHub two-factor authentication is enforced for the publisher organization.
- Docker Hub two-factor authentication is enforced for the publisher account.
- The named maintainer is authorized to support and submit this repository.
- The exact submitted commit passed repository CI, Community Applications
  Validate and Scan, and the release checklist in `docs/release-checklist.md`.
