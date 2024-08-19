TOP := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
APSTRA_COLLECTION_ROOT := $(TOP)/ansible_collections/junipernetworks/apstra

VERSION := $(shell sed -n '/^version: / s,.*"\(.*\)"$$,\1,p' $(APSTRA_COLLECTION_ROOT)/galaxy.yml)

APSTRA_COLLECTION = $(TOP)/junipernetworks-apstra-$(VERSION).tar.gz

# Set the PIPENV_VENV_IN_PROJECT environment variable to 1 to install the virtual environment in the project directory
# Only do this for builds so we can control if developer tools get installed.
export PIPENV_VENV_IN_PROJECT := 1

.PHONY: setup build install clean

build: $(APSTRA_COLLECTION_ROOT)/.apstra-collection

# OS-specific settings
OS := $(shell uname -s)
ifeq ($(OS),Darwin)
PYENV_INSTALL_PREFIX := PYTHON_CONFIGURE_OPTS=--enable-framework
endif

setup:
	$(PYENV_INSTALL_PREFIX) pyenv install --force
	pip install pipenv

install: build
	pipenv run ansible-galaxy collection install --force $(APSTRA_COLLECTION)

test: install
	pipenv run ansible-playbook -vvv $(APSTRA_COLLECTION_ROOT)/tests/apstra_facts.yml

clean:
	rm -rf $(APSTRA_COLLECTION_ROOT)/.apstra-collection $(APSTRA_COLLECTION_ROOT)/requirements.txt $(TOP)/junipernetworks-apstra-*.tar.gz

# Get all .py files in the APSTRA_COLLECTION_ROOT directory
PY_FILES := $(shell find $(APSTRA_COLLECTION_ROOT) -name *.py)

$(APSTRA_COLLECTION_ROOT)/.apstra-collection: $(APSTRA_COLLECTION_ROOT)/requirements.txt $(PY_FILES)
	rm -f $(TOP)/junipernetworks-apstra-*.tar.gz
	pipenv run ansible-galaxy collection build $(APSTRA_COLLECTION_ROOT)
	touch $@

$(APSTRA_COLLECTION_ROOT)/requirements.txt: $(TOP)/Pipfile
	pipenv --rm &>/dev/null || true
	pipenv install
	pipenv run pip freeze > $@
	