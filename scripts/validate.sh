#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
template="${repo_root}/templates/autogpt.xml"
profile="${repo_root}/ca_profile.xml"
icon="${repo_root}/images/autogpt.png"
license="${repo_root}/LICENSE"

command -v xmllint >/dev/null || {
  echo "xmllint is required" >&2
  exit 1
}

xmllint --noout "${template}" "${profile}"

[[ -s "${icon}" ]] || {
  echo "missing images/autogpt.png" >&2
  exit 1
}

[[ -s "${license}" ]] || {
  echo "missing root LICENSE" >&2
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
overview="$(xmllint --xpath 'string(/Container/Overview)' "${template}")"
app_license="$(xmllint --xpath 'string(/Container/License)' "${template}")"
support_url="$(xmllint --xpath 'string(/Container/Support)' "${template}")"
profile_forum="$(xmllint --xpath 'string(/CommunityApplications/Forum)' "${profile}")"

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
[[ "${overview}" == *"experimental single-node"* ]]
[[ "${app_license}" == *"PolyForm Shield 1.0.0"* ]]
[[ "${support_url}" == "https://github.com/Significant-Gravitas/autogpt-unraid/issues" ]]
[[ "${profile_forum}" == "${support_url}" ]]

for required_flag in \
  "--restart=unless-stopped" \
  "--stop-timeout 360" \
  "--shm-size 2g" \
  "--ulimit nofile=65536:65536" \
  "--log-driver json-file" \
  "--log-opt max-size=50m" \
  "--log-opt max-file=1"; do
  grep -Fq -- "${required_flag}" "${template}"
done

if grep -R -E "REPLACE_WITH_|TBD_|REQUIRES_" \
  "${template}" "${profile}" "${repo_root}/README.md" \
  "${repo_root}/CONTRIBUTING.md" "${repo_root}/SECURITY.md"; then
  echo "public-facing files contain unresolved placeholders" >&2
  exit 1
fi

echo "Unraid template validation passed"
