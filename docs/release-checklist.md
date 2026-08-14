# Release checklist

Use this checklist for every Community Applications submission or material
template update. Do not publish a revision that has not completed every
required check.

## Repository and policy

- [ ] The repository is public and active.
- [ ] The root MIT license, `ca_profile.xml`, template XML, and approved icon
      are present.
- [ ] GitHub and Docker Hub organization accounts enforce two-factor
      authentication.
- [ ] `scripts/validate.sh` and repository CI pass on the exact release commit.
- [ ] Community Applications **Validate** and **Scan** both pass after the final
      XML change.
- [ ] The support, project, registry, readme, template, and icon URLs return
      HTTP 200 from a signed-out client.

## Image and runtime

- [ ] `significantgravitas/autogpt:latest` resolves to the intended stable
      multi-platform release; record its index digest.
- [ ] The image exposes port 3000, declares `/data`, includes its healthcheck,
      and carries the expected source-revision label.
- [ ] Install the template through current Unraid Docker Authoring Mode with a
      fresh `/mnt/user/appdata/autogpt` path and host port 3000.
- [ ] Save, close, and reopen the template; confirm Unraid preserved all
      required fields and additional Docker arguments.
- [ ] Wait for healthy state and verify `/healthz`.
- [ ] Create the allowlisted first account, complete onboarding, promote the
      account, set **Allow New Accounts** to `false`, and confirm a second
      signup is rejected.
- [ ] Run a provider-free Builder workflow and confirm it persists in Library.
- [ ] Confirm a provider-backed action without credentials returns an
      actionable missing-credential error.
- [ ] Recreate the container from the template and confirm the account, agent,
      and data persist.
- [ ] Stop the container cleanly and confirm there is no OOM kill.
- [ ] Exercise update and rollback procedures without deleting appdata.

## Presentation and submission

- [ ] Review the rendered Community Applications card, description, settings,
      category, beta marker, icon, Web UI link, and support link.
- [ ] Confirm the operator guide is live at
      `https://docs.agpt.co/platform/self-hosting/single-container`.
- [ ] Review all text for accuracy, spelling, security guidance, and release
      readiness; remove internal notes and placeholders.
- [ ] Submit the exact tested repository commit through the current Community
      Applications intake flow.
- [ ] Record the submission reference, submitted commit, image digest, date,
      and any moderator follow-up in the private release record.
