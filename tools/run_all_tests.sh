#!/usr/bin/env bash
# =============================================================================
# run_all_tests.sh
#
# Runs every Apstra Ansible collection test target, one by one, with:
#   • Blueprint cleanup before each target (removes stale "test_*" blueprints)
#   • Per-target log file (stdout + stderr)
#   • Rolling summary appended to a single summary file
#   • ConnectorOps group: create → customize suites → integration → delete
#   • Final pass/fail/skip table printed to console and written to summary
#
# Usage:
#   cd /home/cgadiparthi/apstra-ansible-collection
#   bash run_all_tests.sh
#
# Options (env vars):
#   ANSIBLE_FLAGS   extra flags passed to ansible-playbook (default: -v)
#   TESTBED_FILE    path to testbed YAML for ConnectorOps targets
#                   (default: ansible_collections/juniper/apstra/testbed.yml)
#   SKIP_INSTALL    set to 1 to skip the initial 'make install' step
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
COLLECTION_ROOT="ansible_collections/juniper/apstra"
TESTS_DIR="${COLLECTION_ROOT}/tests"
VARS_DIR="${TESTS_DIR}/vars"
INTEGRATION_DIR="${TESTS_DIR}/integration"
# Always use absolute path so Ansible can find the file regardless of playbook dir
TESTBED_FILE="$(realpath "${TESTBED_FILE:-${COLLECTION_ROOT}/testbed.yml}")"
ANSIBLE_FLAGS="${ANSIBLE_FLAGS:--v}"

RUN_TS=$(date +%Y%m%d_%H%M%S)
LOG_DIR="test-run-logs/${RUN_TS}"
SUMMARY_FILE="${LOG_DIR}/summary.txt"
CLEANUP_PB="${TESTS_DIR}/cleanup_test_blueprints.yml"

mkdir -p "${LOG_DIR}"

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ── Result tracking ───────────────────────────────────────────────────────────
declare -a PASSED=()
declare -a FAILED=()
declare -a SKIPPED=()

log() { echo -e "$*"; echo -e "$*" >> "${SUMMARY_FILE}"; }
hdr() { log "${CYAN}${BOLD}$*${NC}"; }

# ── Write summary header ──────────────────────────────────────────────────────
{
  echo "======================================================================"
  echo "  Apstra Ansible Collection — Full Test Run"
  echo "  Started : $(date)"
  echo "  Log dir : ${LOG_DIR}"
  echo "  Testbed : ${TESTBED_FILE}"
  echo "======================================================================"
  echo ""
} | tee -a "${SUMMARY_FILE}"

# ── Helpers ───────────────────────────────────────────────────────────────────

# run_cleanup — delete stale test_ blueprints; errors are non-fatal
run_cleanup() {
  local cleanup_log="${LOG_DIR}/_cleanup_$(date +%H%M%S).log"
  echo "  → [cleanup] removing stale test_* blueprints..."
  if ! pipenv run ansible-playbook -v "${CLEANUP_PB}" \
    > "${cleanup_log}" 2>&1; then
    log "${RED}  ✗ CLEANUP FAILED — aborting run. See ${cleanup_log}${NC}"
    cat "${cleanup_log}" | tail -20
    exit 1
  fi
}

# run_target NAME PLAYBOOK [EXTRA_ARGS...]
#   Runs cleanup, then the playbook. Logs result.
run_target() {
  local name="$1"; local playbook="$2"; shift 2
  local extra_args=("$@")
  local log_file="${LOG_DIR}/${name}.log"

  hdr ""
  hdr "══ [$(date '+%H:%M:%S')] ${name}"

  run_cleanup

  local start_ts; start_ts=$(date +%s)
  set +e
  pipenv run ansible-playbook ${ANSIBLE_FLAGS} "${playbook}" \
    "${extra_args[@]}" > "${log_file}" 2>&1
  local rc=$?
  set -e
  local elapsed=$(( $(date +%s) - start_ts ))

  if [[ ${rc} -eq 0 ]]; then
    log "${GREEN}  ✓ PASSED${NC}  ${name}  (${elapsed}s)"
    PASSED+=("${name}")
    echo "PASSED  | ${name} | ${elapsed}s" >> "${SUMMARY_FILE}"
  else
    log "${RED}  ✗ FAILED${NC}  ${name}  (${elapsed}s) → ${log_file}"
    FAILED+=("${name}")
    echo "FAILED  | ${name} | ${elapsed}s" >> "${SUMMARY_FILE}"
  fi
}

# skip_target NAME REASON
skip_target() {
  local name="$1"; local reason="$2"
  log "${YELLOW}  ⊘ SKIPPED${NC}  ${name}  — ${reason}"
  SKIPPED+=("${name}")
  echo "SKIPPED | ${name} | ${reason}" >> "${SUMMARY_FILE}"
}

# lookup_bp_id LABEL — print blueprint_id for the given label, or empty string
lookup_bp_id() {
  local label="$1"
  # source .env to get Apstra creds if not already set
  # shellcheck disable=SC1091
  [[ -f .env ]] && source .env 2>/dev/null || true

  # Strip trailing /api if present to form the base URL
  local base_url="${APSTRA_API_URL%/api}"

  # 1. Login → token
  local token
  token=$(curl -sk \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${APSTRA_USERNAME}\",\"password\":\"${APSTRA_PASSWORD}\"}" \
    "${base_url}/api/aaa/login" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || true)

  [[ -z "${token}" ]] && { echo ""; return; }

  # 2. List blueprints → find by label
  curl -sk \
    -H "AuthToken: ${token}" \
    "${base_url}/api/blueprints" 2>/dev/null \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', {})
if isinstance(items, list):
    for bp in items:
        if bp.get('label') == '${label}':
            print(bp.get('id',''))
            break
elif isinstance(items, dict):
    for bp_id, bp in items.items():
        if isinstance(bp, dict) and bp.get('label') == '${label}':
            print(bp_id)
            break
" 2>/dev/null || true
}

# ── Phase 0: Build & install collection once ─────────────────────────────────
hdr "══ Phase 0: Build & install collection"
if [[ "${SKIP_INSTALL:-0}" == "1" ]]; then
  log "${YELLOW}  (skipped — SKIP_INSTALL=1)${NC}"
else
  install_log="${LOG_DIR}/_install.log"
  rm -f juniper-apstra-*.tar.gz
  if make install > "${install_log}" 2>&1; then
    log "${GREEN}  ✓ Collection installed${NC}"
  else
    log "${RED}  ✗ Collection install FAILED — aborting${NC}"
    cat "${install_log}"
    exit 1
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Standalone unit tests
#   Each test creates and deletes its own blueprint.  We clean up before each
#   target to handle leftovers from a prior failed run.
# ─────────────────────────────────────────────────────────────────────────────
hdr ""
hdr "══════════════════════════════════════════════════════════════"
hdr "  Phase 1: Standalone unit tests"
hdr "══════════════════════════════════════════════════════════════"

run_target "test-apstra_facts"        "${TESTS_DIR}/apstra_facts.yml"
run_target "test-aaa_server"          "${TESTS_DIR}/aaa_server.yml"
run_target "test-blueprint"           "${TESTS_DIR}/blueprint.yml"
run_target "test-virtual_network"     "${TESTS_DIR}/virtual_network.yml"
run_target "test-routing_policy"      "${TESTS_DIR}/routing_policy.yml"
run_target "test-security_zone"       "${TESTS_DIR}/security_zone.yml"
run_target "test-endpoint_policy"     "${TESTS_DIR}/endpoint_policy.yml"
run_target "test-tag"                 "${TESTS_DIR}/tag.yml"
run_target "test-resource_group"      "${TESTS_DIR}/resource_group.yml"
run_target "test-resource_pools"      "${TESTS_DIR}/resource_pools.yml"
run_target "test-property_set"        "${TESTS_DIR}/property_set.yml"
run_target "test-external_gateway"    "${TESTS_DIR}/external_gateway.yml"
run_target "test-connectivity_template" "${TESTS_DIR}/connectivity_template.yml"
run_target "test-configlets"          "${TESTS_DIR}/configlets.yml"
run_target "test-generic_systems"     "${TESTS_DIR}/generic_systems.yml"
run_target "test-system_agents"       "${TESTS_DIR}/system_agents.yml"
run_target "test-os_upgrade"          "${TESTS_DIR}/os_upgrade.yml"
run_target "test-upgrade_group"       "${TESTS_DIR}/upgrade_group.yml"
run_target "test-interface"           "${TESTS_DIR}/interface.yml"
run_target "test-interface_map"       "${TESTS_DIR}/interface_map.yml"
run_target "test-fabric_settings"     "${TESTS_DIR}/fabric_settings.yml"
run_target "test-ztp_device"          "${TESTS_DIR}/ztp_device.yml"
run_target "test-ztp_config"          "${TESTS_DIR}/ztp_config.yml"
run_target "test-ztp_onboarding"      "${TESTS_DIR}/ztp_onboarding.yml"
run_target "test-iba_probes"          "${TESTS_DIR}/iba_probes.yml"
run_target "test-interconnect_gateway" "${TESTS_DIR}/interconnect_gateway.yml"
run_target "test-cabling_map"         "${TESTS_DIR}/cabling_map.yml"
run_target "test-virtual_infra_manager" "${TESTS_DIR}/virtual_infra_manager.yml"
run_target "test-floating_ip"         "${TESTS_DIR}/floating_ip.yml"
run_target "test-blueprint_health"    "${TESTS_DIR}/blueprint_health.yml"
run_target "test-device_management"   "${TESTS_DIR}/device_management.yml"
run_target "test-os_images"           "${TESTS_DIR}/os_images.yml"
run_target "test-tenant_management"   "${TESTS_DIR}/tenant_management.yml"
run_target "test-rbac_user"           "${TESTS_DIR}/rbac_user.yml"
run_target "test-rbac_roles"          "${TESTS_DIR}/rbac_roles.yml"
run_target "test-allowed_list"        "${TESTS_DIR}/allowed_list.yml"
run_target "test-banned_list"         "${TESTS_DIR}/banned_list.yml"

# blueprint_report: auto-discovers any available blueprint (may fail if none exist)
run_target "test-blueprint_report"    "${TESTS_DIR}/blueprint_report.yml"

# rollback: needs a committed blueprint — expected to fail without one
run_target "test-rollback"            "${TESTS_DIR}/rollback.yml"

# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: ConnectorOps group
#   create-connectorops-blueprint → customize suites → integration → delete
# ─────────────────────────────────────────────────────────────────────────────
hdr ""
hdr "══════════════════════════════════════════════════════════════"
hdr "  Phase 2: ConnectorOps group (testbed: ${TESTBED_FILE})"
hdr "══════════════════════════════════════════════════════════════"

COPS_VARS="${VARS_DIR}/connectorops_blueprint.yml"

# Derive topology_name from testbed file
TOPOLOGY_NAME=$(python3 -c "
import yaml, sys
try:
    with open('${TESTBED_FILE}') as f:
        tb = yaml.safe_load(f)
    print(list(tb['testbeds']['apstra']['testbed1']['topologies'].keys())[0])
except Exception as e:
    print('', file=sys.stderr)
    raise
" 2>/dev/null || true)

if [[ -z "${TOPOLOGY_NAME}" ]]; then
  log "${RED}  Could not derive topology_name from ${TESTBED_FILE} — skipping ConnectorOps group${NC}"
  skip_target "connectorops-group" "could not read topology_name from testbed"
else
  log "  Topology name : ${TOPOLOGY_NAME}"

  # 2.1 Create ConnectorOps blueprint
  run_cleanup
  hdr ""
  hdr "── [$(date '+%H:%M:%S')] create-connectorops-blueprint"
  cops_create_log="${LOG_DIR}/create-connectorops-blueprint.log"
  cops_create_start=$(date +%s)
  set +e
  pipenv run ansible-playbook ${ANSIBLE_FLAGS} \
    -e "@${COPS_VARS}" \
    -e "testbed_file=${TESTBED_FILE}" \
    "${TESTS_DIR}/create_connectorops_blueprint.yml" \
    > "${cops_create_log}" 2>&1
  cops_create_rc=$?
  set -e
  cops_create_elapsed=$(( $(date +%s) - cops_create_start ))

  if [[ ${cops_create_rc} -eq 0 ]]; then
    log "${GREEN}  ✓ PASSED${NC}  create-connectorops-blueprint  (${cops_create_elapsed}s)"
    PASSED+=("create-connectorops-blueprint")
    echo "PASSED  | create-connectorops-blueprint | ${cops_create_elapsed}s" >> "${SUMMARY_FILE}"

    # Look up the blueprint ID for the customize sub-tests
    COPS_BP_ID=$(lookup_bp_id "${TOPOLOGY_NAME}")

    if [[ -z "${COPS_BP_ID}" ]]; then
      log "${YELLOW}  ⚠ Could not resolve blueprint_id for '${TOPOLOGY_NAME}' — skipping customize tests${NC}"
      skip_target "test-customize_external_gateway"    "blueprint_id lookup failed"
      skip_target "test-customize_generic_systems"     "blueprint_id lookup failed"
      skip_target "test-customize_connectivity_template" "blueprint_id lookup failed"
    else
      log "  ConnectorOps blueprint_id : ${COPS_BP_ID}"

      # 2.2 Customize sub-tests (run against the live blueprint; no cleanup needed)
      run_target "test-customize_external_gateway" \
        "${TESTS_DIR}/customize_external_gateway.yml" \
        -e "blueprint_id=${COPS_BP_ID}"

      run_target "test-customize_generic_systems" \
        "${TESTS_DIR}/customize_generic_systems.yml" \
        -e "blueprint_id=${COPS_BP_ID}"

      run_target "test-customize_connectivity_template" \
        "${TESTS_DIR}/customize_connectivity_template.yml" \
        -e "blueprint_id=${COPS_BP_ID}"
    fi

    # 2.3 Integration test (uses testbed_file to discover topology)
    run_target "test-integration-connectivity_template_connectorops" \
      "${INTEGRATION_DIR}/connectivity_template_connectorops.yml" \
      -e "@${COPS_VARS}" \
      -e "testbed_file=${TESTBED_FILE}"

    # 2.4 Delete ConnectorOps blueprint (teardown)
    hdr ""
    hdr "── [$(date '+%H:%M:%S')] delete-connectorops-blueprint"
    cops_delete_log="${LOG_DIR}/delete-connectorops-blueprint.log"
    cops_delete_start=$(date +%s)
    set +e
    pipenv run ansible-playbook ${ANSIBLE_FLAGS} \
      -e "@${COPS_VARS}" \
      -e "testbed_file=${TESTBED_FILE}" \
      "${TESTS_DIR}/delete_connectorops_blueprint.yml" \
      > "${cops_delete_log}" 2>&1
    cops_delete_rc=$?
    set -e
    cops_delete_elapsed=$(( $(date +%s) - cops_delete_start ))

    if [[ ${cops_delete_rc} -eq 0 ]]; then
      log "${GREEN}  ✓ PASSED${NC}  delete-connectorops-blueprint  (${cops_delete_elapsed}s)"
      PASSED+=("delete-connectorops-blueprint")
      echo "PASSED  | delete-connectorops-blueprint | ${cops_delete_elapsed}s" >> "${SUMMARY_FILE}"
    else
      log "${RED}  ✗ FAILED${NC}  delete-connectorops-blueprint  (${cops_delete_elapsed}s) → ${cops_delete_log}"
      FAILED+=("delete-connectorops-blueprint")
      echo "FAILED  | delete-connectorops-blueprint | ${cops_delete_elapsed}s" >> "${SUMMARY_FILE}"
    fi

  else
    log "${RED}  ✗ FAILED${NC}  create-connectorops-blueprint  (${cops_create_elapsed}s) → ${cops_create_log}"
    FAILED+=("create-connectorops-blueprint")
    echo "FAILED  | create-connectorops-blueprint | ${cops_create_elapsed}s" >> "${SUMMARY_FILE}"
    log "${YELLOW}  Skipping ConnectorOps customize + integration tests (blueprint not created)${NC}"
    skip_target "test-customize_external_gateway"    "create-connectorops-blueprint failed"
    skip_target "test-customize_generic_systems"     "create-connectorops-blueprint failed"
    skip_target "test-customize_connectivity_template" "create-connectorops-blueprint failed"
    skip_target "test-integration-connectivity_template_connectorops" "create-connectorops-blueprint failed"
    skip_target "delete-connectorops-blueprint"      "create-connectorops-blueprint failed"
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────────────────────────────────────
total=$(( ${#PASSED[@]} + ${#FAILED[@]} + ${#SKIPPED[@]} ))

{
  echo ""
  echo "======================================================================"
  echo "  FINAL SUMMARY  —  $(date)"
  echo "======================================================================"
  printf "  %-8s  %d / %d\n" "PASSED"  "${#PASSED[@]}"  "${total}"
  printf "  %-8s  %d / %d\n" "FAILED"  "${#FAILED[@]}"  "${total}"
  printf "  %-8s  %d / %d\n" "SKIPPED" "${#SKIPPED[@]}" "${total}"
  echo ""
  if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo "  Failed targets:"
    for t in "${FAILED[@]}"; do echo "    ✗  ${t}"; done
  fi
  if [[ ${#SKIPPED[@]} -gt 0 ]]; then
    echo "  Skipped targets:"
    for t in "${SKIPPED[@]}"; do echo "    ⊘  ${t}"; done
  fi
  echo ""
  echo "  Log directory: ${LOG_DIR}"
  echo "  Summary file : ${SUMMARY_FILE}"
  echo "======================================================================"
} | tee -a "${SUMMARY_FILE}"

# Exit non-zero if any test failed
[[ ${#FAILED[@]} -eq 0 ]]
