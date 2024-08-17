![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# Juniper Apstra Ansible Collection

This repository contains the Juniper Apstra Ansible Collection, which provides a set of Ansible modules and roles for network management via the Juniper Apstra AOS platform.

## Installation

To install the Juniper Apstra Ansible Collection, you can use the following command:

```shell
ansible-galaxy collection install junipernetworks.apstra
```

## Usage

Once the collection is installed, you can start using the provided modules and roles in your Ansible playbooks. Here's an example of how to use the `apstra_facts` module to get network configuration state information from Apstra:

```yaml
---
- name: Gather Apstra facts
  hosts: all
  gather_facts: no
  tasks:
    - name: Run apstra_facts module
      junipernetworks.apstra.apstra_facts:
      register: apstra_facts_result

    - name: Display gathered facts
      debug:
        var: apstra_facts_result.ansible_facts
```

Here's an example of how you specify the Apstra inventory:
```yaml
all:
  hosts:
    cloudlabs-apstra:
      ansible_connection: junipernetworks.apstra.apstra_connection
```

You need to specify environment variables to connect to Apstra. For example:
```bash
APSTRA_API_URL="https://apstra-34d9c451-d688-408b-826d-581b963c086e.aws.apstra.com/api"
APSTRA_USERNAME="admin"
APSTRA_PASSWORD="TenaciousFlyingfish1#"
```

For more information on the available modules and their usage, please refer to the [documentation](https://docs.juniper.net/apstra/ansible-collection).

## Contributing

If you would like to contribute to this project, please follow the guidelines outlined in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Development Environment

The following tools are recommended for development of this collection:
1. [brew.sh](https://brew.sh/)
1. [pyenv](https://github.com/pyenv/pyenv/blob/master/README.md)
2. [pipenv](https://github.com/pyenv/pyenv/blob/master/README.md)

### Setup

1. If you don't have brew, install it: 
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```
2. Install the brew components needed for pyenv: 
    ```bash
    brew install xz pyenv
    ```
3. Optional: Follow documentation [(link)](https://pipenv.pypa.io/en/stable/shell.html#shell-completion) to set up shell completion.
4. Add the following to you shell profile (usually `~/.zprofile` on OS X or `~/.bash_profile` on Ubuntu):
    ```bash
    eval "$(/opt/homebrew/bin/brew shellenv)"
    export PYENV_ROOT="$HOME/.pyenv"
    [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH" eval "$(pyenv init -)"
    ```
5. If you changed your shell profile in the last step, source it. For example: 
      ```bash
      source ~/.zprofile
      ```
6. Build proper version of python (version is specified in [.python-version](.python-version)): 
   ```bash
   pyenv install
   ```
7. Install pipenv in the new build of python: 
   ```bash
   pip install pipenv
   ```
### Usage

To use the development environment after setting everything up, simply run the commands:

  ```bash
  pipenv install --dev
  pipenv shell
  ```

This will start a new interactive prompt in which the known supported version of Ansible and required dependencies to use the Apstra SDK is installed.

### Packaging

The following `make` targets are supported to build, install and test an ansible galaxy package.

|Target|Purpose|
|---|---|
|build|Create package junipernetworks-apstra-$(VERSION).tar.gz|
|install|Install package junipernetworks-apstra-$(VERSION).tar.gz|
|test|Test the collection.|
|clean|Clean up created files.|

## License

This project is licensed under the [MIT License](LICENSE).
