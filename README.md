![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# Juniper Apstra Ansible Collection

This repository contains the Juniper Apstra Ansible Collection, which provides a set of Ansible modules and roles for network management via the Juniper Apstra AOS platform.

- [Juniper Apstra Ansible Collection](#juniper-apstra-ansible-collection)
  - [Installation and Usage](#installation-and-usage)
  - [Contributing](#contributing)
  - [Development Environment](#development-environment)
    - [Setup](#setup)
      - [Mac OS X](#mac-os-x)
      - [Linux-based Systems](#linux-based-systems)
      - [All Systems](#all-systems)
    - [Usage](#usage)
    - [Test Configuration](#test-configuration)
    - [Image Build](#image-build)
    - [Image Publish](#image-publish)
    - [Building/Testing](#buildingtesting)
    - [Debugging](#debugging)
    - [Using the Apstra SDK in the Ansible Collection](#using-the-apstra-sdk-in-the-ansible-collection)
    - [Locking the Blueprint](#locking-the-blueprint)
  - [License](#license)
  - [Community and Support](#community-and-support)

## Installation and Usage

See [README](ansible_collections/juniper/apstra/README.md).

## Contributing

If you would like to contribute to this project, please follow the guidelines outlined in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Development Environment

The following tools are recommended for development of this collection:
1. [brew.sh](https://brew.sh/) -- Only needed for _Mac OS X_
1. [pyenv](https://github.com/pyenv/pyenv/blob/master/README.md)
2. [pipenv](https://github.com/pyenv/pyenv/blob/master/README.md)
3. [pre-commit](https://github.com/pre-commit/pre-commit)

### Setup

#### Mac OS X

1. If you're on a Mac and don't have brew, install it:
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```
2. If you have an ARM-based Mac, make sure the following is in your ~/.zprofile:
   ```bash
    eval "$(/opt/homebrew/bin/brew shellenv)"
   ```
   For Intel-based Mac, you may have to add this to ~/.zprofile instead:
   ```bash
    eval "$(/usr/local/bin/brew shellenv)"
   ```

3. Run the following command to install pyenv:
   ```bash
   brew install xz pyenv
   ```

4. Add this to your ~/.zprofile and restart your shell:
    ```bash
    export PYENV_ROOT="$HOME/.pyenv"
    [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    ```

#### Linux-based Systems

1. Install pyenv:

    ```bash
    curl https://pyenv.run | bash
    ```

2. To set it up in your shell follow these instructions: https://github.com/pyenv/pyenv?tab=readme-ov-file#b-set-up-your-shell-environment-for-pyenv

3. On _Ubuntu_, you'll need to install some packages to build Python properly:
      ```bash
      sudo apt -y install build-essential liblzma-dev libbz2-dev zlib1g zlib1g-dev libssl-dev libcrypt-dev libffi-dev libsqlite3-dev
      ```

#### All Systems

1. Download the aos-sdk, from the [Juniper Download page for Apstra](https://support.juniper.net/support/downloads/?p=apstra). Select the option for the [Apstra Automation Python 3 SDK](https://webdownload.juniper.net/swdl/dl/secure/site/1/record/179819.html?pf=Apstra%20Fabric%20Conductor). The SDK is a closed-source project. Juniper Networks is actively working to split the Apstra client code out and open-source it, as that is the only part needed for this collection.

2. The file that's downloaded will have either a 'whl' or a 'dms' extension. Just move the file to the expected location. For example: `mv ~/Downloads/aos_sdk-0.1.0-py3-none-any.dms build/wheels/aos_sdk-0.1.0-py3-none-any.whl`.

3. Run the setup `make` target:
   ```bash
   make setup
   ```

4. Optional: Follow [pipenv command completion setup instructions](https://pipenv.pypa.io/en/stable/shell.html#shell-completion). Only do it if pipenv is installed in your global Python interpreter.

### Usage

To use the development environment after setting everything up, simply run the commands:

  ```bash
  pipenv install --dev
  pipenv shell
  ```

This will start a new interactive prompt in which the known supported version of Ansible and required dependencies to use the Apstra SDK is installed.

### Test Configuration

To run tests, you should have an Apstra 5.0 instance in the lab.

At the root of your 'apstra-ansible-collection' repo, create a .env file. Put the authentication files you need in there. `pipenv` will set these when the pipenv is initialized. Here is an example.

```bash
APSTRA_API_URL="https://apstra-34d9c451-d688-408b-826d-581b963c086e.aws.apstra.com/api"
APSTRA_USERNAME="admin"
APSTRA_PASSWORD="TenaciousFlyingfish1#"
APSTRA_VERIFY_CERTIFICATES=0
```

### Image Build

To build the image, docker is required.

To build an image, you'll need to set the environment variables `RH_USERNAME` and `RH_PASSWORD` in the .env file at the root of your repo.  For example:

```bash
RH_USERNAME=jsmith
RH_PASSWORD=XXXXXXXXXXXXXX
```

Then `make image` will create an image named `apstra-ee:latest`.

### Image Publish

To publish an image, you'll need to set the REGISTRY_URL in your .env file to point to the location of the docker registry you use to publish Execution Environments. For example:

```bash
REGISTRY_URL=s-artifactory.juniper.net/ee/apstra-ansible-collection
```

Then, simply run `make image` again, and in addition to rebuilding (if needed), the image `apstra-ee:latest` will be tagged and pushed to the location specified in the `REGISTRY_URL`.

### Building/Testing

The following `make` targets are supported to build, install and test an ansible galaxy package.

|Target|Purpose|
|---|---|
|setup|Setup the build/test execution environment.|
|build|Create package `juniper-apstra-$(VERSION).tar.gz.`|
|install|Install package `juniper-apstra-$(VERSION).tar.gz.`|
|image|Build an execution environment (container) image `apstra-ee:latest`, and optionally tag/publish if `REGISTRY_URL` is set.|
|test|Test the collection.|
|clean|Clean up created files.|
|release-build|Force rebuilding the collection for release.|
|pipenv|Setup the pipenv used for developement and execution.|
|clean-pipenv|Clean the pipenv used for development and execution.|


### Debugging

Debugging Ansible modules in VSCode is easy. Simply use the `Debug: Ansible Module` debug configuration. To use it:

1. Be sure to have a `.env` file as described in the [Test Configuration](#test-configuration) section.
1. Open the code for the module you wish to debug in VS Code.
2. Set your breakpoint as needed.
3. _OPTIONAL:_ Create a `module_args/<your_module>.json` file with your (optional) additional parameters to debug. For example, here's a `module_args/authenticate.json` to debug the `authenticate` module:
    ```json
    {
      "ANSIBLE_MODULE_ARGS": {
        "logout": false
      }
    }
    ```
4. Hit the green button!

### Using the Apstra SDK in the Ansible Collection

Here's an example of how the Apstra SDK can be used to perform CRUD operations.

```python
        # Instantiate the client
        client_factory = ApstraClientFactory.from_params(module.params)
        client = client_factory.l3clos_client()

        # Gather facts using the persistent connection

        # Get /api/version
        version = client.version.get()

        # Get /api/blueprints
        blueprints = client.blueprints
        blueprints_list = blueprints.list()
        blueprints_map = {blueprint['id']: blueprint for blueprint in blueprints_list}

        # prepare the blueprint query
        blueprint = client.blueprints['941660a1-2967-4550-ae3b-04d6d9fd71b4']
        # get the blueprint data
        bp_data = blueprint.get()

        # prepare the security zone query
        security_zone = blueprint.security_zones['hJR2j7ExBhEHgWE2Cbg']
        # get the security zone data
        sz_data = security_zone.get()

        # update the security zone data
        sz_data['label'] = 'Default routing zone EDWIN WUZ HERE'
        security_zone.update(sz_data)

        # get the updated security zone data
        sz_data_updated = security_zone.get()

        # update the security zone data back to the original
        sz_data['label'] = 'Default routing zone'
        security_zone.update(sz_data)

        # create a new security zone
        Routing_Zone_Name = "Example_RZ"
        new_sz = blueprint.security_zones.create(data={
            "vrf_name": "{}".format(Routing_Zone_Name),
            # "vni_id": 90000,
            "vrf_description": "vrf desc for {}".format(Routing_Zone_Name),
            "sz_type": "evpn",
            "label": "{}".format(Routing_Zone_Name)
        })

        # get the security zone
        new_sz_check = blueprint.security_zones[new_sz['id']].get()

        # delete the security zone
        blueprint.security_zones[new_sz['id']].delete()
```

### Locking the Blueprint

The Terrform plugin implementation provides a model for how we will lock the blueprint during plays. See [Blueprint Mutex Documentation](https://github.com/Juniper/terraform-provider-apstra/blob/main/kb/blueprint_mutex.md)

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

## Community and Support

For community support, join us on Matrix: [#network:ansible.com](https://matrix.to/#/#network:ansible.com)
