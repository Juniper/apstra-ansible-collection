REMOTE ?= origin

APSTRA_COLLECTION_ROOT := ansible_collections/juniper/apstra

VERSION := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)

APSTRA_COLLECTION := $(APSTRA_COLLECTION_ROOT)/juniper-apstra-$(VERSION).tar.gz

# Get all .py files in the APSTRA_COLLECTION_ROOT directory
PY_FILES := $(shell find $(APSTRA_COLLECTION_ROOT) -name *.py)

PY_VERSION := $(shell cat .python-version)

APSTRA_COLLECTION = juniper-apstra-$(VERSION).tar.gz

.PHONY: setup build release-build install clean clean-pipenv pipenv docs tag image

# OS-specific settings
OS := $(shell uname -s)
ifeq ($(OS),Darwin)
PYENV_INSTALL_PREFIX := PYTHON_CONFIGURE_OPTS=--enable-framework
endif

# By default use .venv in the current directory
export PIPENV_VENV_IN_PROJECT=1

# Needed for antsi-build doc build
CERT_PATH = $(shell python -m certifi 2>/dev/null)
export SSL_CERT_FILE=$(CERT_PATH)
export REQUESTS_CA_BUNDLE=$(CERT_PATH)

setup: clean-pipenv
	pyenv uninstall --force $(PY_VERSION)
	rm -rf $(HOME)/.pyenv/versions/$(PY_VERSION)
	$(PYENV_INSTALL_PREFIX) pyenv install --force $(PY_VERSION)
	$(MAKE) pipenv
	# Needed for tests
	pipenv run ansible-galaxy collection install --ignore-certs --force community.general

define install_collection_if_missing
	pipenv run ansible-doc $(1) &>/dev/null || pipenv run ansible-galaxy collection install --ignore-certs --force $(1)
endef

AOS_SDK_DEFAULT_WHL := aos_sdk-0.1.0-py3-none-any.whl
AOS_SDK_DEFAULT_URL := https://s-artifactory.juniper.net:443/artifactory/atom-generic/aos_sdk_5.1.0/$(AOS_SDK_DEFAULT_WHL)

pipenv: build/wheels
	@# Pick the highest-versioned aos_sdk wheel; fall back to downloading the default
	@AOS_SDK_WHL=$$(ls build/wheels/aos_sdk-*.whl 2>/dev/null | grep -v '$(AOS_SDK_DEFAULT_WHL)' | sort -V | tail -1); \
	if [ -z "$$AOS_SDK_WHL" ]; then \
		AOS_SDK_WHL=$$(ls build/wheels/$(AOS_SDK_DEFAULT_WHL) 2>/dev/null); \
	fi; \
	if [ -z "$$AOS_SDK_WHL" ]; then \
		echo "No aos_sdk wheel found in build/wheels/, downloading default $(AOS_SDK_DEFAULT_WHL)..."; \
		curl -fso "build/wheels/$(AOS_SDK_DEFAULT_WHL)" "$(AOS_SDK_DEFAULT_URL)"; \
		AOS_SDK_WHL="build/wheels/$(AOS_SDK_DEFAULT_WHL)"; \
	fi; \
	AOS_SDK_BASENAME=$$(basename $$AOS_SDK_WHL); \
	echo "Using aos_sdk wheel: $$AOS_SDK_BASENAME"; \
	CURRENT=$$(sed -n 's/.*aos-sdk = {file = "build\/wheels\/\(aos_sdk-[^"]*\.whl\)".*/\1/p' Pipfile); \
	if [ "$$CURRENT" != "$$AOS_SDK_BASENAME" ]; then \
		echo "Updating Pipfile: $$CURRENT -> $$AOS_SDK_BASENAME"; \
		sed -i "s|aos-sdk = {file = \"build/wheels/aos_sdk-[^\"]*\.whl\"}|aos-sdk = {file = \"build/wheels/$$AOS_SDK_BASENAME\"}|" Pipfile; \
		rm -f Pipfile.lock; \
	fi
	(pip install pipenv pre-commit && \
	 pre-commit install && \
	 pipenv install --dev)

build/wheels:
	mkdir -p build/wheels

tag:
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push $(REMOTE) $(VERSION)
	git push --tags

image: build
	mkdir -p build/collections
	rm -f build/collections/juniper-apstra.tar.gz
	cp "$(APSTRA_COLLECTION)" build/collections/juniper-apstra.tar.gz
	@AOS_SDK_WHL=$$(ls build/wheels/aos_sdk-*.whl 2>/dev/null | sort -V | tail -1); \
	AOS_SDK_BASENAME=$$(basename $$AOS_SDK_WHL); \
	echo "Updating ee-builder.yml with SDK wheel: $$AOS_SDK_BASENAME"; \
	sed -i "s|aos_sdk-[^/]*\.whl|$$AOS_SDK_BASENAME|g" build/ee-builder.yml
	TAG=$(VERSION) pipenv run build/build_image.sh

release-build: docs
	make build

build: $(APSTRA_COLLECTION_ROOT)/.apstra-collection

NEWVER := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)-$(SHORT_COMMIT)
update-version:
	sed -i "s/^version: \".*\"/version: \"$(NEWVER)\"/" $(APSTRA_COLLECTION_ROOT)/galaxy.yml
APSTRA_COLLECTION_DOCS_BUILD := ansible_collections/juniper/apstra/_build

docs: pipenv install
	rm -rf "$(APSTRA_COLLECTION_DOCS_BUILD)" "$(APSTRA_COLLECTION_ROOT)/.apstra-collection"
	mkdir -p $(APSTRA_COLLECTION_ROOT)/_build
	chmod og-rwx $(APSTRA_COLLECTION_ROOT)/_build
	pipenv run antsibull-docs sphinx-init \
		--dest-dir $(APSTRA_COLLECTION_DOCS_BUILD) \
		--no-indexes \
		--no-add-antsibull-docs-version \
		--output-format simplified-rst \
		--use-current \
		--squash-hierarchy \
		--lenient \
		--project "Juniper Network Apstra Ansible Collection" \
		--copyright "Juniper Networks, Inc." \
		--title "Apstra Ansible Collection" \
		--title "Apstra Ansible Collection" \
		juniper.apstra
	pipenv run $(APSTRA_COLLECTION_DOCS_BUILD)/build.sh
	cp $(APSTRA_COLLECTION_DOCS_BUILD)/rst/*.rst $(APSTRA_COLLECTION_ROOT)/docs/

$(APSTRA_COLLECTION_ROOT)/.apstra-collection: $(APSTRA_COLLECTION_ROOT)/requirements.txt $(APSTRA_COLLECTION_ROOT)/galaxy.yml  $(PY_FILES)
	rm -f juniper-apstra-*.tar.gz
	rm -f $(APSTRA_COLLECTION_ROOT)/MANIFEST.json $(APSTRA_COLLECTION_ROOT)/FILES.json
	pipenv run ansible-galaxy collection build $(APSTRA_COLLECTION_ROOT)
	touch "$@"

$(APSTRA_COLLECTION_ROOT)/requirements.txt: Pipfile Makefile pipenv
	pipenv clean && pipenv requirements --from-pipfile --exclude-markers | sed -e 's:==:>=:' | sed -e '\:build/wheels/aos_sdk:d' | sed -e '\:ansible-core:d' > "$@"

install: build
	pipenv run ansible-galaxy collection install --ignore-certs --force $(APSTRA_COLLECTION)

.PHONY: test \
	test-apstra_facts \
	test-blueprint \
	test-virtual_network \
	test-routing_policy \
	test-security_zone \
	test-endpoint_policy \
	test-tag \
	test-resource_group \
	test-resource_pools \
	test-property_set \
	test-external_gateway \
	test-customize_external_gateway \
	test-connectivity_template \
	test-configlets \
	test-generic_systems \
	test-customize_generic_systems \
	test-system_agents \
	test-os_upgrade \
	test-upgrade_group \
	test-interface_map \
	test-fabric_settings \
	test-ztp_device \
	test-iba_probes \
	test-interconnect_gateway \
	test-cabling_map \
        test-virtual_infra_manager \
        test-floating_ip
# Ignore warnings about localhost from ansible-playbook
export ANSIBLE_LOCALHOST_WARNING=False
export ANSIBLE_INVENTORY_UNPARSED_WARNING=False

ANSIBLE_FLAGS ?= -v

test-apstra_facts: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/apstra_facts.yml

test-blueprint: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/blueprint.yml

test-virtual_network: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/virtual_network.yml

test-routing_policy: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/routing_policy.yml

test-security_zone: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/security_zone.yml

test-endpoint_policy: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/endpoint_policy.yml

test-tag: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/tag.yml

test-resource_group: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/resource_group.yml

test-resource_pools: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/resource_pools.yml

test-property_set: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/property_set.yml

test-external_gateway: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/external_gateway.yml

BLUEPRINT_ID ?=
test-customize_external_gateway: install
	@if [ -z "$(BLUEPRINT_ID)" ]; then echo "ERROR: BLUEPRINT_ID is required. Usage: make test-customize_external_gateway BLUEPRINT_ID=<id>"; exit 1; fi
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/customize_external_gateway.yml -e blueprint_id=$(BLUEPRINT_ID)

test-customize_connectivity_template: install
	@if [ -z "$(BLUEPRINT_ID)" ]; then echo "ERROR: BLUEPRINT_ID is required. Usage: make test-customize_connectivity_template BLUEPRINT_ID=<id>"; exit 1; fi
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/customize_connectivity_template.yml -e blueprint_id=$(BLUEPRINT_ID)

test-connectivity_template: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/connectivity_template.yml

test-configlets: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/configlets.yml

test-generic_systems: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/generic_systems.yml

test-customize_generic_systems: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/customize_generic_systems.yml

test-system_agents: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/system_agents.yml

test-os_upgrade: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/os_upgrade.yml

test-upgrade_group: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/upgrade_group.yml

test-interface_map: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/interface_map.yml

test-fabric_settings: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/fabric_settings.yml

test-cabling_map: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/cabling_map.yml

# ── virtual_infra_manager tests ───────────────────────────────────────────────
# Credentials are loaded automatically from .env (vcenter_hostname /
# vcenter_username / vcenter_password).  Override with -e when needed.
#
# Full run — all phases + auto-cleanup:
#   make test-virtual_infra_manager
#
# Skip teardown (leave VIM alive for manual inspection):
#   make test-virtual_infra_manager ANSIBLE_FLAGS="--skip-tags teardown -v"
#
# Single phase:
#   make test-virtual_infra_manager ANSIBLE_FLAGS="--tags phase1 -v"
#   make test-virtual_infra_manager ANSIBLE_FLAGS="--tags phase2 -v -e vim_id=<uuid>"
#   make test-virtual_infra_manager ANSIBLE_FLAGS="--tags phase3 -v"
#
# Teardown only — clean up a stale VIM left by an interrupted run:
#   make test-virtual_infra_manager ANSIBLE_FLAGS="--tags teardown -v -e vim_id=<uuid>"
# ──────────────────────────────────────────────────────────────────────────────
test-virtual_infra_manager: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/virtual_infra_manager.yml

test-floating_ip: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/floating_ip.yml

test-interconnect_gateway: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/interconnect_gateway.yml

test-rollback: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/rollback.yml $(if $(BLUEPRINT_ID),-e blueprint_id=$(BLUEPRINT_ID),)

test-ztp_device: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/ztp_device.yml

test-iba_probes: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/iba_probes.yml

test-name_resolution: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/name_resolution.yml

TESTBED_FILE ?=

# ── ConnectorOps full run (all phases) ────────────────────────────────────────
create-connectorops-blueprint: install
	@if [ -z "$(TESTBED_FILE)" ]; then echo "ERROR: TESTBED_FILE is required. Usage: make create-connectorops-blueprint TESTBED_FILE=/path/to/testbed.yaml"; exit 1; fi
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) \
		$(APSTRA_COLLECTION_ROOT)/tests/create_connectorops_blueprint.yml \
		-e @$(APSTRA_COLLECTION_ROOT)/tests/vars/connectorops_blueprint.yml \
		-e testbed_file=$(TESTBED_FILE)

# ── ConnectorOps demo targets (cumulative — each includes all prerequisites) ─
#  make demo-auth                   → Phase 1 only
#  make demo-onboard                → Phases 1-2
#  make demo-design                 → Phases 1-3
#  make demo-interface-maps         → Phases 1-4
#  make demo-blueprint              → Phases 1-5
#  make demo-external-gateway       → Phases 1-6
#  make demo-connectivity-template  → Phases 1-7

_DEMO_BASE = pipenv run ansible-playbook $(ANSIBLE_FLAGS) \
	$(APSTRA_COLLECTION_ROOT)/tests/create_connectorops_blueprint.yml \
	-e @$(APSTRA_COLLECTION_ROOT)/tests/vars/connectorops_blueprint.yml \
	-e testbed_file=$(TESTBED_FILE)

_DEMO_CHECK = @if [ -z "$(TESTBED_FILE)" ]; then echo "ERROR: TESTBED_FILE is required. Usage: make $@ TESTBED_FILE=/path/to/testbed.yaml"; exit 1; fi

demo-auth: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth"

demo-onboard: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase2_onboard"

demo-design: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase2_onboard,phase3_design"

demo-interface-maps: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase2_onboard,phase3_design,phase4_interface_maps"

demo-blueprint: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase2_onboard,phase3_design,phase4_interface_maps,phase5_blueprint"

demo-external-gateway: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase2_onboard,phase3_design,phase4_interface_maps,phase5_blueprint,phase6_external_gateway"

demo-connectivity-template: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase2_onboard,phase3_design,phase4_interface_maps,phase5_blueprint,phase6_external_gateway,phase7_connectivity_template"

# ── Regression: customer-scenario VN test (Phase 15f) ─────────────────────────
# Runs against an already-deployed connectorops blueprint.
# Phase 0 (always) loads testbed vars; phase14_sz builds the SZ facts and the
# vn_esi_bound_to / vn_fallback_bound_to lists used by Phase 15f.
# All earlier tasks are idempotent — only Phase 15f adds new assertions.
# Usage: make test-vn-regression TESTBED_FILE=/path/to/testbed.yaml
test-vn-regression: install
	$(_DEMO_CHECK)
	$(_DEMO_BASE) --tags "phase1_auth,phase14_sz,phase15_vn"

delete-connectorops-blueprint: install
	@if [ -z "$(TESTBED_FILE)" ]; then echo "ERROR: TESTBED_FILE is required. Usage: make delete-connectorops-blueprint TESTBED_FILE=/path/to/testbed.yaml"; exit 1; fi
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) \
		$(APSTRA_COLLECTION_ROOT)/tests/delete_connectorops_blueprint.yml \
		-e @$(APSTRA_COLLECTION_ROOT)/tests/vars/connectorops_blueprint.yml \
		-e testbed_file=$(TESTBED_FILE)

test: test-apstra_facts test-blueprint test-virtual_network test-routing_policy test-security_zone test-endpoint_policy test-tag test-resource_group test-configlets test-property_set test-resource_pools test-external_gateway test-connectivity_template test-generic_systems test-system_agents test-os_upgrade test-upgrade_group test-interface_map test-fabric_settings test-interconnect_gateway test-ztp_device test-cabling_map test-iba_probes test-virtual_infra_manager test-floating_ip

# Integration Tests
.PHONY: test-integration-property_set
.PHONY: test-integration-resource_pools
.PHONY: test-integration-configlets
.PHONY: test-integration-connectivity_template_connectorops
.PHONY: test-integration-os_upgrade
.PHONY: test-integration-upgrade_group
.PHONY: test-integration-virtual_infra_manager_vcenter

test-integration-property_set: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/integration/property_set.yml

test-integration-resource_pools: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/integration/resource_pools.yml

test-integration-configlets: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/integration/configlets.yml

# ── Connectivity Template Assignment — Connectorops Integration Test ──────────
# Replicates the exact account team scenario that triggered fix_ct_issue fixes.
# Runs against the live "vg-am-cops-tb-0" connectorops blueprint with real devices.
# Creates + destroys a temporary SZ + VN; the existing blueprint is not modified.
#
# Prerequisites:
#   - Blueprint "vg-am-cops-tb-0" must already exist (create-connectorops-blueprint)
#   - AOS at 10.88.137.14 must be reachable
#
# Usage:
#   make test-integration-connectivity_template_connectorops
#   make test-integration-connectivity_template_connectorops ANSIBLE_FLAGS="-v"
test-integration-connectivity_template_connectorops: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) \
		$(APSTRA_COLLECTION_ROOT)/tests/integration/connectivity_template_connectorops.yml

# ── OS Upgrade Integration Test (requires account team Apstra 6.1.1) ─────────
# Tests state=gathered and state=impact_report (READ-ONLY — safe for account team).
# state=present (actual upgrade) is DISABLED by default (run_upgrade_test=false).
#
# ⚠️  ACCOUNT TEAM SETUP: Tests 1–3 are read-only and safe at any time.
#     Test 4 (upgrade) requires explicit opt-in — NEVER run without approval.
#
# Usage against account team (read-only):
#   APSTRA_API_URL="https://apstra-d5b0895e-3549-4f9c-a786-6d7f68bb071a.aws.apstra.com/api" \
#   APSTRA_USERNAME="admin" \
#   APSTRA_PASSWORD="SwiftChimpanzee4+" \
#   PIPENV_DONT_LOAD_ENV=1 \
#   make test-integration-os_upgrade ANSIBLE_FLAGS="-v"
#
# Usage against local Apstra (6.0.0 — gathered/impact may return empty):
#   make test-integration-os_upgrade ANSIBLE_FLAGS="-v"
test-integration-os_upgrade: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) \
		$(APSTRA_COLLECTION_ROOT)/tests/integration/os_upgrade.yml

# ── Upgrade Group Integration Test (requires account team Apstra 6.1.1) ──────
# Tests 1–2 are READ-ONLY (state=gathered).
# Tests 3–9 perform WRITE operations but always clean up in always: block.
#
# ⚠️  ACCOUNT TEAM SETUP: All write tests restore devices to 'default'.
#     Safe to run in full at any time.  No device upgrades are triggered.
#
# Read-only run (gathered tests only):
#   APSTRA_API_URL="https://apstra-d5b0895e-3549-4f9c-a786-6d7f68bb071a.aws.apstra.com/api" \
#   APSTRA_USERNAME="admin" \
#   APSTRA_PASSWORD="SwiftChimpanzee4+" \
#   PIPENV_DONT_LOAD_ENV=1 \
#   make test-integration-upgrade_group ANSIBLE_FLAGS="-v --tags read_only"
#
# Full run (all tests — cleanup guaranteed):
#   APSTRA_API_URL="https://apstra-d5b0895e-3549-4f9c-a786-6d7f68bb071a.aws.apstra.com/api" \
#   APSTRA_USERNAME="admin" \
#   APSTRA_PASSWORD="SwiftChimpanzee4+" \
#   PIPENV_DONT_LOAD_ENV=1 \
#   make test-integration-upgrade_group ANSIBLE_FLAGS="-v"
test-integration-upgrade_group: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) \
		$(APSTRA_COLLECTION_ROOT)/tests/integration/upgrade_group.yml

# ── VIM vCenter Integration Test (requires live vCenter at 10.204.16.35) ─────
# Full run (all phases):
#   make test-integration-virtual_infra_manager_vcenter \
#     ANSIBLE_FLAGS="-v -e vcenter_hostname=10.204.16.35 \
#                   -e vcenter_username=administrator@vsphere.local \
#                   -e vcenter_password=C0ntrail\!23"
#
# Single phase (e.g., verify only with existing resources):
#   make test-integration-virtual_infra_manager_vcenter \
#     ANSIBLE_FLAGS="--tags verify -v -e vim_id=<uuid> -e blueprint_id=<uuid> \
#                   -e vim_system_id=<uuid>"
test-integration-virtual_infra_manager_vcenter: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/integration/virtual_infra_manager_vcenter.yml

# ── VIM vCenter Integration Test — ConnectorOps Blueprint ────────────────────
# Prerequisite: make create-connectorops-blueprint TESTBED_FILE=~/ACS/testbed.yaml
#
# Full run (all phases):
#   make test-integration-vim-connectorops \
#     ANSIBLE_FLAGS="-v \
#       -e vcenter_hostname=10.204.16.35 \
#       -e vcenter_username=administrator@vsphere.local \
#       -e vcenter_password=C0ntrail\!23"
#
# With explicit blueprint_id (skip auto-discovery):
#   make test-integration-vim-connectorops \
#     ANSIBLE_FLAGS="-v \
#       -e blueprint_id=e1d32dac-895f-4ae6-b27a-272dcef072a7 \
#       -e vcenter_hostname=10.204.16.35 \
#       -e vcenter_username=administrator@vsphere.local \
#       -e vcenter_password=C0ntrail\!23"
#
# Teardown only (clean up artifacts from a prior run):
#   make test-integration-vim-connectorops \
#     ANSIBLE_FLAGS="--tags phase_teardown -v \
#       -e blueprint_id=<uuid> \
#       -e vim_id=<uuid> \
#       -e vim_system_id=<uuid> \
#       -e esxi_system_id=<blueprint_node_id> \
#       -e vi_id=<virtual_infra_id>"
#
# Verify phase only (after a waiting period for VIM analytics indexing):
#   make test-integration-vim-connectorops \
#     ANSIBLE_FLAGS="--tags phase_verify -v \
#       -e blueprint_id=<uuid> \
#       -e vim_id=<uuid> \
#       -e vim_system_id=<uuid> \
#       -e vi_id=<virtual_infra_id>"
.PHONY: test-integration-vim-connectorops
test-integration-vim-connectorops: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/integration/virtual_infra_manager_connectorops.yml

clean-pipenv:
	PIPENV_VENV_IN_PROJECT= pipenv --rm 2>/dev/null || true
	rm -rf .venv

clean: clean-pipenv
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/requirements.txt juniper-apstra-*.tar.gz

demo: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) demo/security_zone.yml
