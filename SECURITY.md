# Security policy

Please do not open a public issue for a suspected vulnerability.

Report vulnerabilities in AutoGPT Platform through the private process in the
[AutoGPT security policy](https://github.com/Significant-Gravitas/AutoGPT/security/policy).
Include the affected image tag or digest, Unraid version, reproduction steps,
and relevant logs with credentials and personal data removed.

Report vulnerabilities in the AutoGPT Fully Local image overlay or its
embedded compatibility adapter through
[private vulnerability reporting for this repository](https://github.com/Significant-Gravitas/autogpt-unraid/security/advisories/new).
Reports should include the derived image tag or digest, official base digest, affected route,
upstream software versions, and a minimal reproduction. Do not include real
API keys, private endpoint addresses, prompt contents, account email addresses,
or other user data.

Treat authentication bypass, unintended public exposure, request or response
smuggling, unsafe upstream forwarding, structured-output translation errors,
and leakage through adapter logs as security-sensitive until triaged. The
adapter listens only on container loopback and is not published. The external
llama.cpp ports are intended for a trusted network and do not provide TLS or
client authentication. The adapter intentionally strips inbound bearer
authorization rather than forwarding it to only a subset of upstream routes;
its llama.cpp upstreams must therefore be unauthenticated.

For non-sensitive template configuration problems, use this repository's
[issue tracker](https://github.com/Significant-Gravitas/autogpt-unraid/issues).
