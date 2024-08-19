TOP := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
APSTRA_COLLECTION_ROOT := $(TOP)/ansible_collections/junipernetworks/apstra

# Get all .py files in the APSTRA_COLLECTION_ROOT directory
PY_FILES := $(shell find $(APSTRA_COLLECTION_ROOT) -name *.py)

VERSION := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)

PY_VERSION := $(shell cat .python-version)

APSTRA_COLLECTION = $(TOP)/junipernetworks-apstra-$(VERSION).tar.gz

# Set the PIPENV_VENV_IN_PROJECT environment variable to 1 to install the virtual environment in the project directory
# Only do this for builds so we can control if developer tools get installed.
export PIPENV_VENV_IN_PROJECT := 1

.PHONY: setup build force-rebuild install clean

# OS-specific settings
OS := $(shell uname -s)
ifeq ($(OS),Darwin)
PYENV_INSTALL_PREFIX := PYTHON_CONFIGURE_OPTS=--enable-framework
endif

setup:
	pyenv uninstall --force $(PY_VERSION)
	rm -rf $(HOME)/.pyenv/versions/$(PY_VERSION)
	$(PYENV_INSTALL_PREFIX) pyenv install --force $(PY_VERSION)
	pip install pipenv
	rm -rf .venv
	pipenv install

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
	
install: build
	pipenv run ansible-galaxy collection install --force $(APSTRA_COLLECTION)

test: install
	pipenv run ansible-playbook -vvvvvv $(APSTRA_COLLECTION_ROOT)/tests/apstra_facts.yml

clean:
	pipenv --rm
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/requirements.txt $(TOP)/junipernetworks-apstra-*.tar.gz
