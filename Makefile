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
	pipenv run ansible-galaxy collection build $(APSTRA_COLLECTION_ROOT)
	touch "$@"

$(APSTRA_COLLECTION_ROOT)/requirements.txt: Pipfile Makefile pipenv
	pipenv clean && pipenv requirements --from-pipfile --exclude-markers | sed -e 's:==:>=:' > "$@"

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
	test-configlets

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

test-configlets: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) $(APSTRA_COLLECTION_ROOT)/tests/configlets.yml

test: test-apstra_facts test-blueprint test-virtual_network test-routing_policy test-security_zone test-endpoint_policy test-tag test-resource_group test-resource_pools test-configlets

clean-pipenv:
	PIPENV_VENV_IN_PROJECT= pipenv --rm 2>/dev/null || true
	rm -rf .venv

clean: clean-pipenv
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/requirements.txt juniper-apstra-*.tar.gz

demo: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) demo/security_zone.yml
