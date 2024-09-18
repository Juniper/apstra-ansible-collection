TOP := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
APSTRA_COLLECTION_ROOT := $(TOP)/ansible_collections/junipernetworks/apstra

# Get all .py files in the APSTRA_COLLECTION_ROOT directory
PY_FILES := $(shell find $(APSTRA_COLLECTION_ROOT) -name *.py)

VERSION := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)

PY_VERSION := $(shell cat .python-version)

APSTRA_COLLECTION = $(TOP)/junipernetworks-apstra-$(VERSION).tar.gz

.PHONY: setup build force-rebuild install clean clean-pipenv pipenv

# OS-specific settings
OS := $(shell uname -s)
ifeq ($(OS),Darwin)
PYENV_INSTALL_PREFIX := PYTHON_CONFIGURE_OPTS=--enable-framework
else
# Latest 
export LDFLAGS := -Wl,-rpath,$(shell brew --prefix openssl)/lib
export CPPFLAGS := -I$(shell brew --prefix openssl)/include
export CONFIGURE_OPTS := --with-openssl=$(shell brew --prefix openssl)
endif

setup: clean-pipenv
	pyenv uninstall --force $(PY_VERSION)
	rm -rf $(HOME)/.pyenv/versions/$(PY_VERSION)
	$(PYENV_INSTALL_PREFIX) pyenv install --force $(PY_VERSION)
	pip install pipenv
	$(MAKE) pipenv

pipenv:
	pipenv install --dev

force-rebuild:
	rm -f $(APSTRA_COLLECTION_ROOT)/.apstra-collection

build: $(APSTRA_COLLECTION_ROOT)/.apstra-collection

$(APSTRA_COLLECTION_ROOT)/.apstra-collection: $(APSTRA_COLLECTION_ROOT)/requirements.txt $(PY_FILES)
	rm -f $(TOP)/junipernetworks-apstra-*.tar.gz
	pipenv run ansible-galaxy collection build $(APSTRA_COLLECTION_ROOT)
	touch $@

$(APSTRA_COLLECTION_ROOT)/requirements.txt: $(TOP)/Pipfile
	pipenv --rm &>/dev/null || true
	pipenv install
	pipenv run pip freeze > $@
	pipenv install --dev
	
install: build
	pipenv run ansible-galaxy collection install --force $(APSTRA_COLLECTION)

.PHONY: test-apstra_facts test-blueprint test-virtual_network

test-apstra_facts: install
	pipenv run ansible-playbook -vvv $(APSTRA_COLLECTION_ROOT)/tests/apstra_facts.yml

test-blueprint: install
	pipenv run ansible-playbook -vvv $(APSTRA_COLLECTION_ROOT)/tests/blueprint.yml

test-virtual_network: install
	pipenv run ansible-playbook -vvv $(APSTRA_COLLECTION_ROOT)/tests/virtual_network.yml

test: test-apstra_facts test-blueprint test-virtual_network

clean-pipenv:
	pipenv --rm || true
	PIPENV_VENV_IN_PROJECT= pipenv --rm || true
	rm -rf .venv

clean: clean-pipenv
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/requirements.txt $(TOP)/junipernetworks-apstra-*.tar.gz
