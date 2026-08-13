# Forum support thread draft

## Title

Support: AutoGPT Platform Community Applications container

## Body

This thread supports the official AutoGPT Platform template for Unraid
Community Applications.

- Project: https://github.com/Significant-Gravitas/AutoGPT
- Container: https://hub.docker.com/r/significantgravitas/autogpt
- Full self-hosting guide: https://docs.agpt.co/platform/self-hosting/single-container
- Template source: https://github.com/Significant-Gravitas/autogpt-unraid

The image runs the complete AutoGPT Platform in one experimental single-node
container, including the web app, APIs, workers, PostgreSQL, RabbitMQ, Valkey,
and FalkorDB-backed memory. It is intended for local and small deployments, not
high availability.

### First setup

1. Set **Public URL** to the exact origin used in the browser, including the
   selected host port.
2. Set **First Account Email** to the exact address that should create the
   initial account.
3. Install the container and wait for Docker to report `healthy`; first boot can
   take several minutes.
4. Create the account, then promote it:

   ```bash
   docker exec AutoGPT autogpt-admin promote you@example.com
   ```

5. Edit the container and set **Allow New Accounts** to `false` before exposing
   AutoGPT beyond the trusted network.

Model-provider keys are not required to boot, create accounts, or run
provider-free blocks. Features that require a provider report the normal
missing-credential error until configured.

### Resources and storage

- Persistent data: `/mnt/user/appdata/autogpt` on the host, `/data` in the
  container
- Web UI: container port 3000
- Shared memory: 2 GiB
- Graceful stop timeout: 360 seconds
- Observed memory use: about 5-6 GiB; leave additional headroom for Unraid and
  other applications

When asking for help, include the Unraid version, CPU architecture, Docker
health state, container logs with secrets removed, and whether the issue occurs
on a fresh dedicated appdata path.
