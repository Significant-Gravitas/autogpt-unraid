# Release checklist

Use this checklist for every Community Applications submission or material
template update. Do not publish a revision that has not completed every
required check.

## Repository and policy

- [x] The repository is public and active.
- [x] The root MIT license, `ca_profile.xml`, template XML, and approved icon
      are present.
- [x] The repository contents are MIT-licensed as required by Community
      Applications. The container image's separate
      `LicenseRef-PolyForm-Shield-1.0.0 AND SSPL-1.0` license is identified
      without representing the application code as MIT-licensed.
- [ ] GitHub and Docker Hub organization accounts enforce two-factor
      authentication.
- [x] `scripts/validate.sh` and repository CI pass on the exact release commit.
- [ ] Community Applications **Validate** and **Scan** both pass after the final
      XML change.
- [x] The support, project, registry, readme, template, and icon URLs return
      HTTP 200 from a signed-out client.
- [ ] **Settings → Docker → Docker Stop Timeout** is at least 360 seconds on
      the validation host; record that this is a global Unraid setting.

## Image and runtime

- [x] `significantgravitas/autogpt:latest` resolves to the intended stable
      multi-platform release; record its index digest.
- [x] The image exposes port 3000, declares `/data`, includes its healthcheck,
      and carries the expected source-revision label.
- [x] Run the exact template Docker contract with a fresh
      `/mnt/user/appdata/autogpt` path and host port 3000 without writing
      protected Unraid configuration.
- [x] Enter the template contract through current Unraid Docker Authoring Mode.
- [x] Save, close, and reopen the authored template; confirm Unraid preserved all
      required fields and additional Docker arguments.
- [ ] After the repository is public, import the exact raw template URL through
      Docker Authoring Mode and confirm the rendered values match.
- [x] Wait for healthy state and verify `/healthz`.
- [ ] Create the allowlisted first account, complete onboarding, promote the
      account, set **Allow New Accounts** to `false`, and confirm a second
      signup is rejected.
- [ ] Run a provider-free Builder workflow and confirm it persists in Library.
- [ ] Confirm a provider-backed action without credentials returns an
      actionable missing-credential error.
- [x] Recreate the isolated contract container and confirm generated runtime
      configuration and database files remain mounted.
- [x] Stop the contract container cleanly and confirm exit code 0 with no OOM
      kill.
- [ ] Stop the UI-managed container with Unraid's global Docker Stop Timeout set
      to at least 360 seconds; confirm exit code 0 with no OOM kill.
- [ ] Recreate through Docker Authoring Mode and confirm the account, agent,
      and data persist through the UI-managed lifecycle.
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
