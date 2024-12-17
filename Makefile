REMOTE ?= origin

APSTRA_COLLECTION_ROOT := ansible_collections/junipernetworks/apstra

# Get all .py files in the APSTRA_COLLECTION_ROOT directory
PY_FILES := $(shell find $(APSTRA_COLLECTION_ROOT) -name *.py)

VERSION := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)

PY_VERSION := $(shell cat .python-version)

APSTRA_COLLECTION = junipernetworks-apstra-$(VERSION).tar.gz

.PHONY: setup build release-build install clean clean-pipenv pipenv docs tag

# OS-specific settings
OS := $(shell uname -s)
BREW := $(shell which brew 2>/dev/null)
ifeq ($(OS),Darwin)
PYENV_INSTALL_PREFIX := PYTHON_CONFIGURE_OPTS=--enable-framework
else ifneq ($(BREW),"")
# Use brew if it exists
export LDFLAGS := -Wl,-rpath,$(shell brew --prefix openssl)/lib
export CPPFLAGS := -I$(shell brew --prefix openssl)/include
export CONFIGURE_OPTS := --with-openssl=$(shell brew --prefix openssl)
endif

# By default use .venv in the current directory
export PIPENV_VENV_IN_PROJECT=1

# Needed for antsi-build doc build
CERT_PATH := $(shell python -m certifi)
export SSL_CERT_FILE=$(CERT_PATH)
export REQUESTS_CA_BUNDLE=$(CERT_PATH)

setup: clean-pipenv
	pyenv uninstall --force $(PY_VERSION)
	rm -rf $(HOME)/.pyenv/versions/$(PY_VERSION)
	$(PYENV_INSTALL_PREFIX) pyenv install --force $(PY_VERSION)
	pip install pipenv pre-commit
	$(MAKE) pipenv
	pre-commit install

define install_collection_if_missing
	pipenv run ansible-doc $(1) &>/dev/null || pipenv run ansible-galaxy collection install --ignore-certs --force $(1)
endef

pipenv: build/wheels/aos_sdk-0.1.0-py3-none-any.whl
	pipenv --help &>/dev/null || pip install pipenv
	pipenv install --dev

build/wheels:
	mkdir -p build/wheels

build/wheels/aos_sdk-0.1.0-py3-none-any.whl: build/wheels
	# If this fails, download the wheel from juniper.net to the wheels directory...
	(test -r "$@" && touch "$@") || curl -fso "$@" https://s-artifactory.juniper.net:443/artifactory/atom-generic/aos_sdk_5.0.0-RC5/aos_sdk-0.1.0-py3-none-any.whl 2>/dev/null

tag:
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push $(REMOTE) $(VERSION)
	git push --tags

release-build: tag docs
	rm -f $(APSTRA_COLLECTION_ROOT)/.apstra-collection
	pipenv install
	make build

build: $(APSTRA_COLLECTION_ROOT)/.apstra-collection

APSTRA_COLLECTION_DOCS_BUILD := ansible_collections/junipernetworks/apstra/_build

docs: pipenv install
	rm -rf "$(APSTRA_COLLECTION_DOCS_BUILD)"
	mkdir -p $(APSTRA_COLLECTION_ROOT)/_build
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
		junipernetworks.apstra
	pipenv run $(APSTRA_COLLECTION_DOCS_BUILD)/build.sh
	cp $(APSTRA_COLLECTION_DOCS_BUILD)/rst/*.rst $(APSTRA_COLLECTION_ROOT)/docs/

$(APSTRA_COLLECTION_ROOT)/.apstra-collection: $(APSTRA_COLLECTION_ROOT)/requirements.txt $(APSTRA_COLLECTION_ROOT)/galaxy.yml  $(PY_FILES)
	rm -f junipernetworks-apstra-*.tar.gz
	pipenv run ansible-galaxy collection build $(APSTRA_COLLECTION_ROOT)
	touch "$@"

$(APSTRA_COLLECTION_ROOT)/requirements.txt: Pipfile Makefile pipenv
	pipenv clean && pipenv requirements --from-pipfile > "$@"

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
	test-resource_group

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

test: test-apstra_facts test-blueprint test-virtual_network test-routing_policy test-security_zone test-endpoint_policy test-tag test-resource_group

clean-pipenv:
	PIPENV_VENV_IN_PROJECT= pipenv --rm 2>/dev/null || true
	rm -rf .venv

clean: clean-pipenv
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/requirements.txt junipernetworks-apstra-*.tar.gz

demo: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) demo/security_zone.yml
