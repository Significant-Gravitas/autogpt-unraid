#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
templates_dir="${repo_root}/templates"
icon="${repo_root}/images/autogpt.png"
base_digest="sha256:9a97378805acd43b4bf12bac463f80ff10b7b3743146f74e35c7b7281d2ad48b"

fail() {
  echo "validation failed: $*" >&2
  exit 1
}

assert_file_contains() {
  local file="$1"
  local expected_substring="$2"
  grep -Fq -- "${expected_substring}" "${file}" || \
    fail "${file#"${repo_root}/"}: expected text containing '${expected_substring}'"
}

assert_file_not_contains() {
  local file="$1"
  local rejected_substring="$2"
  ! grep -Fq -- "${rejected_substring}" "${file}" || \
    fail "${file#"${repo_root}/"}: must not contain '${rejected_substring}'"
}

command -v python3 >/dev/null || fail "python3 is required"
command -v file >/dev/null || fail "file is required"

python3 "${repo_root}/scripts/validate_xml.py"

[[ -s "${icon}" ]] || fail "missing images/autogpt.png"
icon_description="$(file -b "${icon}")"
[[ "${icon_description}" == "PNG image data, 512 x 512, 8-bit/color RGBA,"* ]] || \
  fail "images/autogpt.png must be a 512x512 RGBA PNG"
[[ -s "${repo_root}/LICENSE" ]] || fail "missing root LICENSE"
[[ -s "${repo_root}/BRANDING.md" ]] || fail "missing BRANDING.md"

dockerfile="${repo_root}/local-image/Dockerfile"
supervisor="${repo_root}/local-image/supervisord-local-adapter.conf"
install_script="${repo_root}/local-image/install.py"
runner="${repo_root}/local-image/run_adapter.py"
combined_health="${repo_root}/local-image/healthcheck.sh"
adapter_dir="${repo_root}/router"
required_files=(
  "${repo_root}/.dockerignore"
  "${dockerfile}"
  "${supervisor}"
  "${install_script}"
  "${runner}"
  "${combined_health}"
  "${repo_root}/scripts/validate_xml.py"
  "${repo_root}/local-image/tests/test_install.py"
  "${repo_root}/local-image/tests/test_run_adapter.py"
  "${repo_root}/local-image/tests/stub_health.py"
  "${adapter_dir}/proxy.py"
  "${adapter_dir}/healthcheck.py"
  "${adapter_dir}/tests/test_proxy.py"
)
for required_file in "${required_files[@]}"; do
  [[ -s "${required_file}" ]] || \
    fail "image overlay is incomplete: missing ${required_file#"${repo_root}/"}"
done

[[ ! -e "${templates_dir}/autogpt-local-router.xml" ]] || \
  fail "standalone router template must not be published"
[[ ! -e "${adapter_dir}/Dockerfile" ]] || \
  fail "standalone router Dockerfile must not be published"

assert_file_contains "${dockerfile}" "significantgravitas/autogpt@${base_digest}"
assert_file_contains "${dockerfile}" 'org.opencontainers.image.base.name="${AUTOGPT_IMAGE}"'
assert_file_contains "${dockerfile}" "LISTEN_HOST=127.0.0.1"
assert_file_contains "${dockerfile}" "CHAT_BASE_URL=http://127.0.0.1:8098/v1"
assert_file_contains "${dockerfile}" "GRAPHITI_EMBEDDER_BASE_URL=http://127.0.0.1:8098/raw/v1"
assert_file_contains "${dockerfile}" "GRAPHITI_EMBEDDER_MODEL=nomic-embed-text"
assert_file_contains "${dockerfile}" "STORE_EMBEDDING_MODEL=nomic-embed-text"
assert_file_contains "${dockerfile}" "--timeout=45s"
assert_file_contains "${dockerfile}" "--start-period=5m"
assert_file_not_contains "${dockerfile}" "EXPOSE 8098"
assert_file_not_contains "${dockerfile}" "ENTRYPOINT"
assert_file_not_contains "${dockerfile}" "USER "
! grep -Eq '^CMD[[:space:]]' "${dockerfile}" || \
  fail "local-image/Dockerfile must inherit AutoGPT's command"

assert_file_contains "${supervisor}" "/usr/bin/env -i"
assert_file_contains "${supervisor}" "/usr/bin/setpriv --no-new-privs"
assert_file_contains "${supervisor}" "user=autogpt-local-adapter"
assert_file_contains "${supervisor}" "stopwaitsecs=1"
assert_file_contains "${install_script}" "REQUIRED_RUNTIME_PROGRAMS"
assert_file_contains "${install_script}" "runtime:{PROGRAM_NAME}"
assert_file_contains "${runner}" "INTERNAL_VARIABLES"
assert_file_contains "${combined_health}" "/usr/local/bin/autogpt-healthcheck"
assert_file_contains "${combined_health}" "/opt/autogpt-local/healthcheck.py"
assert_file_contains "${adapter_dir}/proxy.py" 'os.getenv("CHAT_UPSTREAM"'
assert_file_contains "${adapter_dir}/proxy.py" 'os.getenv("EMBED_UPSTREAM"'
assert_file_contains "${adapter_dir}/proxy.py" "is_graphiti_reranker_request"
assert_file_contains "${adapter_dir}/proxy.py" 'RAW_PREFIX = "/raw"'

pycache_dir="$(mktemp -d)"
trap 'rm -rf -- "${pycache_dir}"' EXIT
PYTHONPYCACHEPREFIX="${pycache_dir}" python3 -m py_compile \
  "${repo_root}/scripts/validate_xml.py" \
  "${adapter_dir}/proxy.py" \
  "${adapter_dir}/healthcheck.py" \
  "${adapter_dir}/tests/test_proxy.py" \
  "${install_script}" \
  "${runner}" \
  "${repo_root}/local-image/tests/test_install.py" \
  "${repo_root}/local-image/tests/test_run_adapter.py" \
  "${repo_root}/local-image/tests/stub_health.py"
PYTHONPYCACHEPREFIX="${pycache_dir}" python3 -m unittest discover \
  -s "${adapter_dir}/tests" -p 'test_*.py' -v
PYTHONPYCACHEPREFIX="${pycache_dir}" python3 -m unittest discover \
  -s "${repo_root}/local-image/tests" -p 'test_*.py' -v

if grep -R -E "REPLACE_WITH_|TBD_|REQUIRES_" \
  "${templates_dir}" "${repo_root}/ca_profile.xml" "${repo_root}/README.md" \
  "${repo_root}/CONTRIBUTING.md" "${repo_root}/SECURITY.md" \
  "${repo_root}/BRANDING.md" "${repo_root}/docs" "${repo_root}/.github"; then
  fail "public-facing files contain unresolved placeholders"
fi

echo "Two-variant Unraid templates and fully-local image overlay validation passed"
