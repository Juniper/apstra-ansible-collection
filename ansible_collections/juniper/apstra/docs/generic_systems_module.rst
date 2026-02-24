.. Document meta

:orphan:

.. Title

juniper.apstra.generic_systems module -- Manage datacenter generic systems in Apstra blueprints
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 0.2.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- This module manages generic systems in Apstra datacenter blueprints using a flat parameter model for creating, updating, and deleting generic systems with their links to switches.
- Generic systems represent servers, storage devices, or other endpoints connected to leaf/access switches in a blueprint.
- Links are defined as a flat list, each specifying the target switch, interface name, interface transform, optional LAG mode, group label, and per-link tags.
- System-level properties include name, hostname, deploy mode, tags, ASN, loopback IPs, port-channel ID range, and external flag.
- Supports creating, updating, and deleting generic systems with full idempotency.
- Uses the ``switch-system-links`` API to create in-rack systems and the ``external-generic-systems`` API for external systems.
- Requires a blueprint to already exist and leaf switches to have interface maps assigned.

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: ``APSTRA_API_URL`` environment variable.

**auth_token** (string): The authentication token to use if already authenticated. Default: ``APSTRA_AUTH_TOKEN`` environment variable.

**blueprint_id** (string) **[required]**: The ID of the datacenter blueprint.

**system_id** (string): The graph node ID of an existing generic system. Required for update and delete operations. Returned after create.

**name** (string): The display name (label) of the generic system. Used for idempotent lookups — if a system with this name already exists, it will be updated rather than recreated.

**hostname** (string): The hostname of the generic system.

**tags** (list of strings): Tags to apply to the generic system node. Default: ``[]``.

**links** (list of dictionaries): Link definitions connecting switches to the generic system. Each link supports:

  - ``target_switch_id`` (string) **[required]**: The graph node ID of the target leaf/access switch.
  - ``target_switch_if_name`` (string) **[required]**: The physical interface name on the switch (e.g. ``xe-0/0/6``).
  - ``target_switch_if_transform_id`` (integer) **[required]**: The interface transform ID controlling speed/breakout mode.
  - ``lag_mode`` (string): LAG mode for this link. Choices: ``lacp_active``, ``lacp_passive``, ``static_lag``. Omit or set to null for standalone links.
  - ``group_label`` (string): Label to group multiple links into a single LAG (e.g. ``bond0``).
  - ``tags`` (list of strings): Tags to apply to this individual link. Default: ``[]``.

**deploy_mode** (string): The deploy mode. Choices: ``deploy``, ``ready``, ``drain``, ``undeploy``. When omitted (``None``), the deploy mode is left unchanged on update and uses the Apstra default (``deploy``) on create.

**asn** (integer): ASN to assign to the generic system. Set to null to clear.

**loopback_ipv4** (string): IPv4 loopback address in CIDR notation (e.g. ``10.0.0.1/32``). Set to null to clear.

**loopback_ipv6** (string): IPv6 loopback address in CIDR notation (e.g. ``fd00::1/128``). Set to null to clear.

**port_channel_id_min** (integer): Minimum port-channel ID. Default: ``0`` (disabled).

**port_channel_id_max** (integer): Maximum port-channel ID. Default: ``0`` (disabled).

**external** (boolean): Whether this is an external generic system (outside of racks). Default: ``false``. Cannot be changed after creation.

**clear_cts_on_destroy** (boolean): If ``true``, clear all connectivity templates from the system's links before deletion. Default: ``false``.

**state** (string): Desired state. Choices: ``present``, ``absent``. Default: ``present``.

**password** (string): The password for authentication. Default: ``APSTRA_PASSWORD`` environment variable.

**username** (string): The username for authentication. Default: ``APSTRA_USERNAME`` environment variable.

**verify_certificates** (boolean): If set to ``false``, SSL certificates will not be verified. Default: ``true``.

Design Highlights
-----------------

This module uses a flat parameter model with automatic link-set reconciliation:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Feature
     - Details
   * - Parameter style
     - Flat top-level parameters — no nested ``id`` / ``body`` dictionaries required
   * - Link definition
     - Flat link objects with ``target_switch_id``, ``target_switch_if_name``, ``target_switch_if_transform_id``
   * - Logical device
     - Auto-generated from link count and speed — no manual logical device definition needed
   * - System properties
     - ``name``, ``hostname``, ``deploy_mode``, ``asn``, ``loopback_ipv4``, ``loopback_ipv6``, ``port_channel_id_min``, ``port_channel_id_max`` as top-level params
   * - Tags
     - ``tags`` param for system-level tags; per-link ``tags`` in link definitions
   * - Link set management
     - Automatic diff-based link set reconciliation (add missing, remove extra)
   * - External systems
     - ``external: true`` top-level parameter
   * - CT cleanup on delete
     - ``clear_cts_on_destroy`` parameter to clear connectivity templates before deletion
   * - Idempotency lookup
     - By ``name`` or ``hostname`` (automatic)

Examples
--------

Create a Generic System with a Single Link
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a generic system connected to a leaf switch
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        name: "my-server-01"
        hostname: "my-server-01.example.com"
        tags:
          - "server"
          - "prod"
        deploy_mode: "deploy"
        links:
          - target_switch_id: "{{ leaf_id }}"
            target_switch_if_name: "ge-0/0/6"
            target_switch_if_transform_id: 1
            tags:
              - "1G"
        state: present
      register: gs_create

Create a Generic System with LAG Links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a server with two LAG bonds across two leaf switches
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        name: "lag-server-01"
        hostname: "lag-server-01.example.com"
        tags:
          - "server"
          - "lag"
        links:
          - target_switch_id: "{{ leaf_ids[0] }}"
            target_switch_if_name: "ge-0/0/7"
            target_switch_if_transform_id: 1
            lag_mode: "lacp_active"
            group_label: "bond0"
            tags: ["1G", "bond0"]
          - target_switch_id: "{{ leaf_ids[0] }}"
            target_switch_if_name: "ge-0/0/8"
            target_switch_if_transform_id: 1
            lag_mode: "lacp_active"
            group_label: "bond0"
            tags: ["1G", "bond0"]
        state: present

Update a Generic System
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Update generic system hostname and deploy mode
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        system_id: "{{ gs_create.system_id }}"
        name: "my-server-01-updated"
        hostname: "my-server-01-updated.example.com"
        deploy_mode: "ready"
        state: present

Configure ASN and Loopback Addresses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Set ASN and loopback IPs on a generic system
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        system_id: "{{ gs_create.system_id }}"
        asn: 65001
        loopback_ipv4: "10.0.0.1/32"
        loopback_ipv6: "fd00::1/128"
        port_channel_id_min: 1
        port_channel_id_max: 128
        state: present

Create an External Generic System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create external generic system
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        name: "external-server-01"
        hostname: "external-server-01.example.com"
        external: true
        state: present
      register: ext_gs

Delete a Generic System
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Delete a generic system by system ID
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        system_id: "{{ gs_create.system_id }}"
        state: absent

Delete with CT Cleanup
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Delete generic system and clear connectivity templates first
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        system_id: "{{ gs_create.system_id }}"
        clear_cts_on_destroy: true
        state: absent

Delete by Name
~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Delete a generic system by name (no system_id needed)
      juniper.apstra.generic_systems:
        blueprint_id: "{{ blueprint_id }}"
        name: "my-server-01"
        state: absent

Running Tests
~~~~~~~~~~~~~

The module ships with a 20-test playbook covering create, update, delete,
idempotency, LAG, external systems, and validation errors.

**Standalone mode** — creates and destroys its own blueprint:

.. code-block:: bash

    make test-generic_systems

**Existing blueprint mode** — user provides all infrastructure details:

.. code-block:: bash

    make test-generic_systems-bp \
      BLUEPRINT_ID=839079b7-7145-4048-bfe3-8ddb5868201f \
      LEAF_SWITCH_ID=rnz8KEIUsTG_uI7uSA \
      IF_NAME_1=ge-0/0/6 \
      IF_NAME_2=ge-0/0/7 \
      IF_NAME_3=ge-0/0/8 \
      IF_NAME_4=ge-0/0/9 \
      IF_TRANSFORM_ID=1

Required extra vars for existing blueprint mode:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``BLUEPRINT_ID``
     - Blueprint UUID
   * - ``LEAF_SWITCH_ID``
     - Node ID of the target leaf switch in the blueprint
   * - ``IF_NAME_1``
     - Free interface for single-link tests (Tests 1–8)
   * - ``IF_NAME_2``
     - Free interface for LAG link 1 (Tests 9–11)
   * - ``IF_NAME_3``
     - Free interface for LAG link 2 (Tests 9–11)
   * - ``IF_NAME_4``
     - Free interface for delete-by-name test (Test 18)
   * - ``IF_TRANSFORM_ID``
     - Interface transform ID (usually ``1``)

Or directly via ``ansible-playbook``:

.. code-block:: bash

    pipenv run ansible-playbook -v \
      ansible_collections/juniper/apstra/tests/generic_systems.yml \
      -e use_existing_blueprint=true \
      -e blueprint_id=<uuid> \
      -e leaf_switch_id=<leaf-node-id> \
      -e if_name_1=ge-0/0/6 \
      -e if_name_2=ge-0/0/7 \
      -e if_name_3=ge-0/0/8 \
      -e if_name_4=ge-0/0/9 \
      -e if_transform_id=1

Link Fields
~~~~~~~~~~~

Each link in the ``links`` list supports these fields:

- ``target_switch_id`` (string, required): The graph node ID of the target leaf/access switch.
- ``target_switch_if_name`` (string, required): Interface name on the switch (e.g. ``xe-0/0/6``).
- ``target_switch_if_transform_id`` (integer, required): Interface transform ID controlling speed/breakout.
- ``lag_mode`` (string, optional): LAG mode — ``lacp_active``, ``lacp_passive``, or ``static_lag``.
- ``group_label`` (string, optional): Groups links into a single LAG (e.g. ``bond0``).
- ``tags`` (list of strings, optional): Per-link tags.

Return Values
-------------

**changed** (boolean): Indicates whether the module has made any changes. Returned: always.

**system_id** (string): The graph node ID of the generic system. Returned: on create or when identified.

**blueprint_id** (string): The blueprint ID. Returned: always.

**name** (string): The display name (label) of the generic system. Returned: when system exists.

**hostname** (string): The hostname of the generic system. Returned: when system exists.

**tags** (list): The tags applied to the generic system node. Returned: when system exists.

**links** (list): List of link IDs created. Returned: on create.

**deploy_mode** (string): The deploy mode. Returned: when system exists.

**external** (boolean): Whether this is an external generic system. Returned: when system exists.

**asn** (integer): The ASN assigned. Returned: when system exists and ASN is set.

**loopback_ipv4** (string): IPv4 loopback address. Returned: when set.

**loopback_ipv6** (string): IPv6 loopback address. Returned: when set.

**port_channel_id_min** (integer): Minimum port-channel ID. Returned: when system exists.

**port_channel_id_max** (integer): Maximum port-channel ID. Returned: when system exists.

**changes** (dictionary): Dictionary of changes made during update. Returned: on update when changes are made.

**msg** (string): The output message. Returned: always.
