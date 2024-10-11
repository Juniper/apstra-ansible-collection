APSTRA_COLLECTION_ROOT := ansible_collections/junipernetworks/apstra

# Get all .py files in the APSTRA_COLLECTION_ROOT directory
PY_FILES := $(shell find $(APSTRA_COLLECTION_ROOT) -name *.py)

VERSION := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)

PY_VERSION := $(shell cat .python-version)

APSTRA_COLLECTION = junipernetworks-apstra-$(VERSION).tar.gz

.PHONY: setup build release-build install clean clean-pipenv pipenv docs

# OS-specific settings
OS := $(shell uname -s)
ifeq ($(OS),Darwin)
PYENV_INSTALL_PREFIX := PYTHON_CONFIGURE_OPTS=--enable-framework
else
# Unix 
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
	pip install pipenv
	$(MAKE) pipenv

define install_collection_if_missing
	pipenv run ansible-doc $(1) &>/dev/null || pipenv run ansible-galaxy collection install --ignore-certs --force $(1)
endef

pipenv:
	pipenv --help &>/dev/null || pip install pipenv
	pipenv install --dev

release-build: docs
	rm -f $(APSTRA_COLLECTION_ROOT)/.apstra-collection
	make clean-pipenv
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

$(APSTRA_COLLECTION_ROOT)/.apstra-collection: $(APSTRA_COLLECTION_ROOT)/docs/requirements.txt $(APSTRA_COLLECTION_ROOT)/galaxy.yml  $(PY_FILES)
	rm -f junipernetworks-apstra-*.tar.gz
	pipenv run ansible-galaxy collection build $(APSTRA_COLLECTION_ROOT)
	touch "$@"

$(APSTRA_COLLECTION_ROOT)/docs/requirements.txt: Pipfile Makefile
	pipenv --rm &>/dev/null || true
	pipenv install
	pipenv run pip freeze > "$@.tmp"
	sed -e 's/==/~=/' "$@.tmp" > "$@"
	rm "$@.tmp"
	pipenv install --dev
	
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
	pipenv --rm || true
	PIPENV_VENV_IN_PROJECT= pipenv --rm || true
	rm -rf .venv

clean: clean-pipenv
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/docs/requirements.txt junipernetworks-apstra-*.tar.gz

demo: install
	pipenv run ansible-playbook $(ANSIBLE_FLAGS) demo/security_zone.yml