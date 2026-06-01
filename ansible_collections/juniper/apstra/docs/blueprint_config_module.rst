.. Document meta

:orphan:

.. Title

juniper.apstra.blueprint_config module -- Collect rendered device configurations from an Apstra blueprint
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 1.0.9

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- This module collects the rendered configuration from devices in an Apstra blueprint for external storage, backup, compliance auditing, or version control.
- Configurations are retrieved per device via the ``/api/blueprints/{id}/nodes/{node_id}/config-rendering`` API endpoint.
- Supports filtering by device name, device role (spine, leaf, etc.), or an explicit list of device names.
- Optionally saves rendered configs to local files (one file per device).

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: APSTRA_API_URL environment variable

**auth_token** (string): The authentication token to use if already authenticated. Default: APSTRA_AUTH_TOKEN environment variable

**devices** (list): List of device hostnames to collect configs for. If omitted, configs are collected for all devices in the blueprint.

**filename_pattern** (string): Pattern for output filenames when ``output_dir`` is specified. Supports ``{hostname}`` placeholder. Default: ``{hostname}.conf``

**id** (dictionary, required): Dictionary containing the blueprint identifier. ``blueprint`` is the blueprint ID or label.

**output_dir** (string): Directory path to save rendered config files. One file per device will be created. Directory will be created if it does not exist.

**password** (string): The password for authentication. Default: APSTRA_PASSWORD environment variable

**role** (string): Filter devices by role. Common roles include ``spine``, ``leaf``, ``superspine``, ``access``. Cannot be used together with ``devices``. Choices: spine, leaf, superspine, access

**state** (string): The action to perform. Choices: collected. Default: collected

**username** (string): The username for authentication. Default: APSTRA_USERNAME environment variable

**verify_certificates** (boolean): If set to false, SSL certificates will not be verified. Default: True

Examples
--------

Collect All Device Configs
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Collect rendered config for all devices in a blueprint
      juniper.apstra.blueprint_config:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        auth_token: "{{ auth.token }}"
      register: result

Filter by Role
~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Collect config for all spine devices
      juniper.apstra.blueprint_config:
        id:
          blueprint: "my-blueprint"
        role: spine
        auth_token: "{{ auth.token }}"
      register: result

Filter by Device Names
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Collect config for specific devices
      juniper.apstra.blueprint_config:
        id:
          blueprint: "my-blueprint"
        devices:
          - spine1
          - leaf1
        auth_token: "{{ auth.token }}"
      register: result

Save Configs to Files
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Collect and save configs to files
      juniper.apstra.blueprint_config:
        id:
          blueprint: "my-blueprint"
        output_dir: "/tmp/configs"
        filename_pattern: "{hostname}.conf"
        auth_token: "{{ auth.token }}"
      register: result

Return Values
-------------

**changed** (boolean): Always false since this is a read-only module.

**configs** (dictionary): Dictionary of rendered configurations keyed by device hostname. Each entry contains the hostname, rendered config text, system_id, and role.

**device_count** (integer): Number of devices for which configs were collected.

**files_written** (list): List of file paths written when ``output_dir`` is specified.

**msg** (string): Status message.
