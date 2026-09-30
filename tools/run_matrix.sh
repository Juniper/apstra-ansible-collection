#!/usr/bin/env bash
# ── Apstra version compatibility matrix runner ────────────────────────────────
# Runs every test against each configured Apstra version and prints a table.
#
# Usage (from the workspace root):
#   source .env && bash tools/run_matrix.sh
#
# To add a new Apstra version, edit tools/versions.conf — no changes here needed.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COLLECTION_ROOT="${WORKSPACE_ROOT}/ansible_collections/juniper/apstra"
VERSIONS_CONF="${SCRIPT_DIR}/versions.conf"

# ── Load version registry ─────────────────────────────────────────────────────
if [[ ! -f "$VERSIONS_CONF" ]]; then
    echo "ERROR: versions.conf not found at $VERSIONS_CONF" >&2
    exit 1
fi
# shellcheck source=versions.conf
source "$VERSIONS_CONF"

# Build VERSION_ORDER array and VER_URLS / DEVICE_IPS maps from sourced vars
declare -a VER_ORDER
read -ra VER_ORDER <<< "$VERSION_ORDER"

declare -A VER_URLS
declare -A VER_DEVICE_IPS
for ver in "${VER_ORDER[@]}"; do
    key="${ver//./_}"
    url_var="VER_URL_${key}"
    ip_var="DEVICE_IP_${key}"
    VER_URLS["$ver"]="${!url_var:?\"VER_URL_${key} not set in versions.conf\"}"
    VER_DEVICE_IPS["$ver"]="${!ip_var:-}"
done

# ── Test list ─────────────────────────────────────────────────────────────────
TESTS=(
    apstra_facts
    aaa_server
    blueprint
    virtual_network
    routing_policy
    security_zone
    endpoint_policy
    tag
    resource_group
    configlets
    property_set
    resource_pools
    external_gateway
    connectivity_template
    generic_systems
    system_agents
    os_upgrade
    upgrade_group
    interface_map
    fabric_settings
    interconnect_gateway
    ztp_device
    cabling_map
    iba_probes
    virtual_infra_manager
    floating_ip
    device_management
    os_images
    allowed_list
    banned_list
)

RESULTS_DIR="/tmp/matrix_results"
mkdir -p "$RESULTS_DIR"

# ── Helper: switch APSTRA_API_URL in .env ─────────────────────────────────────
set_url() {
    sed -i "s|export APSTRA_API_URL=.*|export APSTRA_API_URL=\"${1}\"|" "${WORKSPACE_ROOT}/.env"
}

# ── Helper: run one test, echoes PASS / FAIL / ERROR ─────────────────────────
run_test() {
    local test="$1"
    local logfile="$2"
    local pb="${COLLECTION_ROOT}/tests/${test}.yml"

    local extra_args=""
    local _dev_user="${DEVICE_USERNAME:-admin}"
    local _dev_pass="${DEVICE_PASSWORD:?'Set DEVICE_PASSWORD env var (see .env)'}"
    local _dev_ip="${VER_DEVICE_IPS[$VER]:-}"

    case "$test" in
      system_agents)
        extra_args="-e management_ip=10.0.0.99 -e device_username=${_dev_user} -e device_password=${_dev_pass}"
        ;;
      device_management|os_upgrade)
        if [[ -n "$_dev_ip" ]]; then
            extra_args="-e device_ip=${_dev_ip} -e device_username=${_dev_user} -e device_password=${_dev_pass} -e device_wait_timeout=600"
        fi
        ;;
    esac

    cd "$WORKSPACE_ROOT"
    pipenv run ansible-playbook -v $extra_args "$pb" >"$logfile" 2>&1
    local rc=$?

    local recap
    recap=$(grep "^localhost" "$logfile" | tail -1 || true)
    [[ -z "$recap" ]] && { echo "ERROR"; return; }

    local failed
    failed=$(echo "$recap" | grep -oP 'failed=\K\d+' || echo "0")
    if [[ "$failed" -gt 0 ]] || [[ $rc -ne 0 ]]; then
        echo "FAIL"
    else
        echo "PASS"
    fi
}

# ── Main: iterate versions → tests ───────────────────────────────────────────
declare -A MATRIX   # ["ver:test"] = PASS|FAIL|ERROR

for VER in "${VER_ORDER[@]}"; do
    URL="${VER_URLS[$VER]}"
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  Apstra $VER — $URL"
    echo "════════════════════════════════════════════════════════"

    set_url "$URL"

    echo "  [install] building & installing collection..."
    make -C "$WORKSPACE_ROOT" install >/dev/null 2>&1
    echo "  [install] done"

    mkdir -p "$RESULTS_DIR/$VER"

    for TEST in "${TESTS[@]}"; do
        logfile="$RESULTS_DIR/$VER/${TEST}.log"
        printf "  %-30s ... " "$TEST"
        result=$(run_test "$TEST" "$logfile")
        MATRIX["${VER}:${TEST}"]="$result"
        printf "%s\n" "$result"
    done
done

# ── Results table ─────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  RESULTS MATRIX"
echo "════════════════════════════════════════════════════════════════════"

printf "%-28s" "Test"
for VER in "${VER_ORDER[@]}"; do printf " │ %-8s" "$VER"; done
echo " │"

printf "%-28s" "$(printf '%0.s─' {1..28})"
for VER in "${VER_ORDER[@]}"; do printf "─┼─%-8s" "$(printf '%0.s─' {1..8})"; done
echo "─┤"

for TEST in "${TESTS[@]}"; do
    printf "%-28s" "$TEST"
    for VER in "${VER_ORDER[@]}"; do
        val="${MATRIX[${VER}:${TEST}]:-ERROR}"
        case "$val" in
            PASS)  sym="✅ PASS " ;;
            FAIL)  sym="❌ FAIL " ;;
            *)     sym="⚠  ERROR" ;;
        esac
        printf " │ %-8s" "$sym"
    done
    echo " │"
done

# ── TSV export ────────────────────────────────────────────────────────────────
TSV="$RESULTS_DIR/matrix.tsv"
{
    printf "Test\t"; printf "%s\t" "${VER_ORDER[@]}"; echo ""
    for TEST in "${TESTS[@]}"; do
        printf "%s\t" "$TEST"
        for VER in "${VER_ORDER[@]}"; do printf "%s\t" "${MATRIX[${VER}:${TEST}]:-ERROR}"; done
        echo ""
    done
} > "$TSV"

echo ""
echo "Logs saved to: $RESULTS_DIR/"
echo "TSV  saved to: $TSV"
