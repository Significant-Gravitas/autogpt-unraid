# Community Applications intake packet

Complete this only after the public template repository and forum support
thread exist.

- Repository name: `Significant-Gravitas/autogpt-unraid`
- Repository URL: `https://github.com/Significant-Gravitas/autogpt-unraid`
- Raw template URL: `https://raw.githubusercontent.com/Significant-Gravitas/autogpt-unraid/main/templates/autogpt.xml`
- Docker repository: `significantgravitas/autogpt:latest`
- Project URL: `https://github.com/Significant-Gravitas/AutoGPT`
- Docker Hub URL: `https://hub.docker.com/r/significantgravitas/autogpt`
- Support thread: `REPLACE_WITH_UNRAID_SUPPORT_THREAD_URL`
- Maintainer: Significant Gravitas
- Application name: AutoGPT
- Application type: Docker
- Architectures: amd64 and arm64
- Beta marker: true
- Application license: PolyForm Shield 1.0.0
- Template repository license: MIT
- Template count: one
- GitHub 2FA acknowledgement: `REQUIRES_ORG_OWNER_CONFIRMATION`
- Docker Hub 2FA acknowledgement: `REQUIRES_ORG_OWNER_CONFIRMATION`
- Preferred contact: `REQUIRES_ORG_OWNER_INPUT`

## Reviewer note

AutoGPT is the upstream project and image owner. The Platform source is publicly
reviewable in the AutoGPT repository and the distribution is clearly marked
experimental/single-node. Native amd64 and arm64 release jobs build, smoke-test,
scan, push, pull by exact digest, smoke-test again, and assemble the public
multi-platform tag. A separate native Unraid acceptance run covered account
bootstrap, a real provider-free Builder execution, persistence, missing-provider
behavior, administrator promotion, registration closure, and relogin.

## Final gates

- [ ] Public template repository exists at the permanent URL
- [ ] Forum support thread exists and both XML placeholders are replaced
- [ ] GitHub and Docker Hub 2FA confirmations are supplied by an organization owner
- [ ] Template installs through Docker Authoring Mode on a fresh appdata path
- [ ] Validate and Scan both pass in the Community Applications submission UI
- [ ] Raw template and icon URLs return HTTP 200
- [ ] `https://docs.agpt.co/platform/self-hosting/single-container` returns HTTP 200 after the docs PR lands
- [ ] Existing account can log in after template-driven recreation with signup closed
