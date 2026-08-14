# Contributing

Thank you for helping improve the official AutoGPT template for Unraid.

## Scope

This repository owns the Unraid template and its catalog metadata. Product
changes belong in the
[AutoGPT repository](https://github.com/Significant-Gravitas/AutoGPT).

Template changes must continue to use the official
`significantgravitas/autogpt` image and preserve these runtime requirements:

- persistent `/data` storage;
- container port `3000`;
- `2 GiB` shared memory;
- `nofile=65536:65536`;
- a `360`-second graceful stop timeout;
- the image-provided Docker healthcheck; and
- exact `AUTOGPT_PUBLIC_URL`, `AUTH_SIGNUP_ALLOWLIST`, and
  `AUTH_ALLOW_NEW_ACCOUNTS` behavior.

Do not add provider credentials, generated secrets, host-specific paths, or
private acceptance data to the repository.

## Validate a change

Install `xmllint`, then run:

```bash
scripts/validate.sh
```

For a release-affecting change, also install the template through current
Unraid Docker Authoring Mode on a fresh appdata path, wait for healthy state,
and verify account bootstrap, signup closure, persistence after recreation,
and normal update behavior.

## Pull requests

Keep pull requests focused, explain the operator-facing impact, and include the
Unraid version and validation evidence. Do not change the image repository or
weaken the security defaults without approval from the AutoGPT maintainers.
