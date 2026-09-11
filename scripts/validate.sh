#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
template="${repo_root}/templates/autogpt.xml"
profile="${repo_root}/ca_profile.xml"
icon="${repo_root}/images/autogpt.png"
license="${repo_root}/LICENSE"
brand_notice="${repo_root}/BRANDING.md"

command -v xmllint >/dev/null || {
  echo "xmllint is required" >&2
  exit 1
}

command -v file >/dev/null || {
  echo "file is required" >&2
  exit 1
}

xmllint --noout "${template}" "${profile}"

[[ -s "${icon}" ]] || {
  echo "missing images/autogpt.png" >&2
  exit 1
}

icon_description="$(file -b "${icon}")"
[[ "${icon_description}" == "PNG image data, 512 x 512, 8-bit/color RGBA,"* ]] || {
  echo "images/autogpt.png must be a 512x512 RGBA PNG" >&2
  exit 1
}

[[ -s "${license}" ]] || {
  echo "missing root LICENSE" >&2
  exit 1
}

[[ -s "${brand_notice}" ]] || {
  echo "missing BRANDING.md" >&2
  exit 1
}

repository="$(xmllint --xpath 'string(/Container/Repository)' "${template}")"
network="$(xmllint --xpath 'string(/Container/Network)' "${template}")"
privileged="$(xmllint --xpath 'string(/Container/Privileged)' "${template}")"
post_args="$(xmllint --xpath 'string(/Container/PostArgs)' "${template}")"
data_target="$(xmllint --xpath 'string(/Container/Config[@Name="App Data"]/@Target)' "${template}")"
data_default="$(xmllint --xpath 'string(/Container/Config[@Name="App Data"]/@Default)' "${template}")"
web_port="$(xmllint --xpath 'string(/Container/Config[@Name="Web UI Port"]/@Target)' "${template}")"
public_url_target="$(xmllint --xpath 'string(/Container/Config[@Name="Public URL"]/@Target)' "${template}")"
signup_allowlist_target="$(xmllint --xpath 'string(/Container/Config[@Name="First Account Email"]/@Target)' "${template}")"
signup_enabled_target="$(xmllint --xpath 'string(/Container/Config[@Name="Allow New Accounts"]/@Target)' "${template}")"
signup_enabled_choices="$(xmllint --xpath 'string(/Container/Config[@Name="Allow New Accounts"]/@Default)' "${template}")"
signup_enabled_value="$(xmllint --xpath 'string(/Container/Config[@Name="Allow New Accounts"])' "${template}")"
beta="$(xmllint --xpath 'string(/Container/Beta)' "${template}")"
requires="$(xmllint --xpath 'string(/Container/Requires)' "${template}")"
app_license="$(xmllint --xpath 'string(/Container/License)' "${template}")"
support_url="$(xmllint --xpath 'string(/Container/Support)' "${template}")"
profile_forum="$(xmllint --xpath 'string(/CommunityApplications/Forum)' "${profile}")"
extra_params="$(xmllint --xpath 'string(/Container/ExtraParams)' "${template}")"

[[ "${repository}" == "significantgravitas/autogpt:latest" ]]
[[ "${network}" == "bridge" ]]
[[ "${privileged}" == "false" ]]
[[ -z "${post_args}" ]]
[[ "${data_target}" == "/data" ]]
[[ "${data_default}" == "/mnt/user/appdata/autogpt" ]]
[[ "${web_port}" == "3000" ]]
[[ "${public_url_target}" == "AUTOGPT_PUBLIC_URL" ]]
[[ "${signup_allowlist_target}" == "AUTH_SIGNUP_ALLOWLIST" ]]
[[ "${signup_enabled_target}" == "AUTH_ALLOW_NEW_ACCOUNTS" ]]
[[ "${signup_enabled_choices}" == "true|false" ]]
[[ "${signup_enabled_value}" == "true" ]]
[[ "${beta}" == "true" ]]
[[ "${requires}" == *"Experimental single-node"* ]]
[[ "${requires}" != *"Docker Stop Timeout"* ]]
[[ "${requires}" != *"at least 360 seconds"* ]]
[[ "${app_license}" == *"LicenseRef-PolyForm-Shield-1.0.0 AND SSPL-1.0"* ]]
[[ "${support_url}" == "https://github.com/Significant-Gravitas/autogpt-unraid/issues" ]]
[[ "${profile_forum}" == "${support_url}" ]]

expected_extra_params="--restart=unless-stopped --stop-timeout 360 --shm-size 2g --ulimit nofile=65536:65536 --log-driver json-file --log-opt max-size=50m --log-opt max-file=1"
[[ "${extra_params}" == "${expected_extra_params}" ]]

# Self-hosted operators pay the model provider directly, so both AutoPilot
# spend caps must ship disabled (-1) and stay optional.
for cap_target in CHAT_DAILY_COST_LIMIT_MICRODOLLARS CHAT_WEEKLY_COST_LIMIT_MICRODOLLARS; do
  cap_default="$(xmllint --xpath "string(/Container/Config[@Target=\"${cap_target}\"]/@Default)" "${template}")"
  cap_value="$(xmllint --xpath "string(/Container/Config[@Target=\"${cap_target}\"])" "${template}")"
  cap_display="$(xmllint --xpath "string(/Container/Config[@Target=\"${cap_target}\"]/@Display)" "${template}")"
  cap_required="$(xmllint --xpath "string(/Container/Config[@Target=\"${cap_target}\"]/@Required)" "${template}")"
  [[ "${cap_default}" == "-1" ]]
  [[ "${cap_value}" == "-1" ]]
  [[ "${cap_display}" == "advanced" ]]
  [[ "${cap_required}" == "false" ]]
done

if grep -R -E "REPLACE_WITH_|TBD_|REQUIRES_" \
  "${template}" "${profile}" "${repo_root}/README.md" \
  "${repo_root}/CONTRIBUTING.md" "${repo_root}/SECURITY.md" \
  "${repo_root}/BRANDING.md" "${repo_root}/docs/validation.md" \
  "${repo_root}/docs/release-checklist.md" "${repo_root}/.github"; then
  echo "public-facing files contain unresolved placeholders" >&2
  exit 1
fi

echo "Unraid template validation passed"
